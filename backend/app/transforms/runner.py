"""Transform execution engine and database persistence runner."""

from __future__ import annotations

import datetime
import json
import logging
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, TransformError
from app.models.api_key import APIKeyVault
from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.models.transform import TransformResult, TransformRun, TransformStatus
from app.repositories.entity import EntityRepository
from app.repositories.relationship import RelationshipRepository
from app.services.crypto import CryptoService
from app.transforms.registry import transform_registry

logger = logging.getLogger(__name__)


class TransformRunner:
    """Engine responsible for running transforms and persisting entities & relationships."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.entity_repo = EntityRepository(session)
        self.relationship_repo = RelationshipRepository(session)

    async def execute_transform(
        self,
        investigation_id: str,
        transform_id: str,
        input_entity_id: str,
        params: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> TransformRun:
        """Execute a transform on an input entity and create resulting entities/relationships in DB.

        Args:
            investigation_id: ID of investigation
            transform_id: ID of transform to execute (e.g. "builtin.dns_lookup")
            input_entity_id: ID of input entity
            params: User parameters dictionary
            user_id: User executing the transform

        Returns:
            TransformRun record containing execution details and summary
        """
        params = params or {}

        # 1. Fetch transform
        transform = transform_registry.get(transform_id)
        if not transform:
            raise NotFoundError("Transform", transform_id)

        # 2. Fetch input entity
        input_entity = await self.entity_repo.get_by_id(input_entity_id)
        if not input_entity or input_entity.investigation_id != investigation_id:
            raise NotFoundError("Entity", input_entity_id)

        # 3. Create TransformRun entry
        run = TransformRun(
            investigation_id=investigation_id,
            transform_id=transform.id,
            transform_name=transform.name,
            status=TransformStatus.RUNNING.value,
            input_entity_id=input_entity.id,
            input_params=json.dumps(params),
            started_at=datetime.datetime.now(datetime.timezone.utc),
            triggered_by_id=user_id,
        )
        self.session.add(run)
        await self.session.flush()

        start_time = time.time()

        # 4. Fetch API key if required
        api_key: str | None = None
        if transform.requires_api_key and transform.api_key_service:
            # Query active API key for service
            result = await self.session.execute(
                select(APIKeyVault).where(
                    APIKeyVault.service_name == transform.api_key_service,
                    APIKeyVault.is_active == True,  # noqa: E712
                )
            )
            key_entry = result.scalar_one_or_none()
            if key_entry:
                from app.config import get_settings
                crypto = CryptoService(get_settings().encryption_key)
                try:
                    api_key = crypto.decrypt(key_entry.encrypted_value)
                except Exception as e:
                    logger.warning("Failed to decrypt API key for %s: %s", transform.api_key_service, e)

        # 5. Execute Transform
        try:
            if api_key:
                params["api_key"] = api_key
                
            entities, relationships, raw_data = await transform.execute(
                entity=input_entity,
                params=params,
            )
        except Exception as e:
            duration = time.time() - start_time
            run.status = TransformStatus.FAILED.value
            run.error_message = str(e)
            run.duration_seconds = duration
            run.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await self.session.commit()
            raise TransformError(transform.name, str(e)) from e

        duration = time.time() - start_time

        # 6. Process results: Create or link entities & relationships
        entities_created_count = 0
        relationships_created_count = 0

        # Entity type to color mapping (matches frontend EntityNode COLOR_MAP)
        TYPE_COLORS: dict[str, str] = {
            "person": "#3B82F6", "organization": "#8B5CF6", "company": "#6366F1",
            "domain": "#10B981", "subdomain": "#34D399", "url": "#06B6D4",
            "ip_address": "#F59E0B", "ipv6_address": "#F59E0B", "asn": "#D97706",
            "email": "#EC4899", "phone": "#14B8A6", "username": "#8B5CF6",
            "certificate": "#22C55E", "website": "#0EA5E9", "server": "#64748B",
            "service": "#64748B", "cloud_asset": "#38BDF8", "repository": "#A3A3A3",
            "social_profile": "#E11D48", "wallet": "#F7931A",
            "bitcoin_wallet": "#F7931A", "ethereum_wallet": "#627EEA",
            "malware": "#EF4444", "hash": "#71717A", "ioc": "#F97316",
            "cve": "#DC2626", "threat_actor": "#7C3AED", "campaign": "#E11D48",
            "street_address": "#059669", "country": "#2563EB", "city": "#0891B2",
            "mx_record": "#EC4899", "nameserver": "#10B981",
        }

        # Keep track of newly mapped IDs in case relationships reference them
        entity_id_map: dict[Any, str] = {}

        for item in entities:
            pos_x = 0.0
            pos_y = 0.0

            entity_color = item.color or TYPE_COLORS.get(item.entity_type, "#6B7280")
            normalized_value = item.value.strip().lower() if item.value else ""
            
            # Aggressive normalization for specific types
            if item.entity_type in ("domain", "subdomain", "url", "website"):
                normalized_value = normalized_value.replace("https://", "").replace("http://", "")
                if normalized_value.endswith("/"):
                    normalized_value = normalized_value[:-1]
                if normalized_value.startswith("www."):
                    normalized_value = normalized_value[4:]
                    
            normalized_label = (item.label or item.value or "").strip()

            # Check if entity with same value already exists in investigation
            duplicates = await self.entity_repo.find_duplicates(
                investigation_id=investigation_id,
                value=normalized_value,
            )

            if duplicates:
                target_entity = duplicates[0]
            else:
                props_data = item.properties
                if isinstance(props_data, dict):
                    props_data = json.dumps(props_data)
                elif props_data is None:
                    props_data = "{}"

                target_entity = await self.entity_repo.upsert_entity(
                    investigation_id=investigation_id,
                    entity_type=item.entity_type,
                    label=normalized_label,
                    value=normalized_value,
                    properties=props_data,
                    confidence=item.confidence,
                    source=f"Transform: {transform.name}",
                    icon=item.icon,
                    color=entity_color,
                    position_x=pos_x,
                    position_y=pos_y,
                )
                entities_created_count += 1
                
            if item.id:
                entity_id_map[item.id] = target_entity.id
            entity_id_map[id(item)] = target_entity.id
            entity_id_map[normalized_value] = target_entity.id
            entity_id_map[(item.entity_type, normalized_value)] = target_entity.id

            result_record = TransformResult(
                transform_run_id=run.id,
                result_type="entity",
                entity_id=target_entity.id,
                confidence=item.confidence,
                raw_data=json.dumps(raw_data) if raw_data else None,
            )
            self.session.add(result_record)

        for item in relationships:
            # Map source
            raw_src = item.source_entity_id
            if hasattr(raw_src, "id"):
                raw_src = raw_src.id
            actual_source_id = entity_id_map.get(raw_src, raw_src)
            if not actual_source_id or actual_source_id == "None":
                actual_source_id = input_entity.id

            # Map target
            raw_tgt = item.target_entity_id
            if hasattr(raw_tgt, "id"):
                raw_tgt = raw_tgt.id
            actual_target_id = entity_id_map.get(raw_tgt, raw_tgt)

            # Fallback if target wasn't resolved by id
            if (not actual_target_id or actual_target_id == "None"):
                if len(entities) == 1 and entities[0].id in entity_id_map:
                    actual_target_id = entity_id_map[entities[0].id]
                elif hasattr(item, "target_entity") and getattr(item, "target_entity") in entity_id_map:
                    actual_target_id = entity_id_map[getattr(item, "target_entity")]

            if not actual_source_id or not actual_target_id or actual_source_id == actual_target_id:
                continue

            rel_exists = await self.relationship_repo.relationship_exists(
                source_entity_id=actual_source_id,
                target_entity_id=actual_target_id,
                relationship_type=item.relationship_type,
            )

            if not rel_exists:
                relationship = await self.relationship_repo.upsert_relationship(
                    investigation_id=investigation_id,
                    source_entity_id=actual_source_id,
                    target_entity_id=actual_target_id,
                    relationship_type=item.relationship_type,
                    label=item.label or item.relationship_type,
                    confidence=item.confidence,
                    source=f"Transform: {transform.name}",
                )
                relationships_created_count += 1
                
                result_record = TransformResult(
                    transform_run_id=run.id,
                    result_type="relationship",
                    relationship_id=relationship.id,
                    confidence=item.confidence,
                )
                self.session.add(result_record)

        # 7. Create Evidence record for this transform execution
        evidence_count = 0
        try:
            from app.models.evidence import Evidence
            evidence_record = Evidence(
                investigation_id=investigation_id,
                entity_id=input_entity.id,
                evidence_type="transform_output",
                title=f"{transform.name} on {input_entity.value}",
                description=f"Transform '{transform.name}' executed on entity '{input_entity.value}' ({input_entity.entity_type}). "
                            f"Discovered {len(entities)} entities and {len(relationships)} relationships.",
                raw_data=json.dumps(raw_data, default=str) if raw_data else None,
                confidence=1.0,
                transform_run_id=run.id,
            )
            self.session.add(evidence_record)
            evidence_count = 1
        except Exception as ev_err:
            logger.warning("Failed to create evidence record: %s", ev_err)

        # 8. Create Timeline Events for new entity discoveries
        timeline_count = 0
        try:
            from app.models.timeline import TimelineEvent
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            
            if entities_created_count > 0:
                timeline_event = TimelineEvent(
                    investigation_id=investigation_id,
                    entity_id=input_entity.id,
                    event_type="transform_discovery",
                    title=f"{transform.name}: {entities_created_count} new entities",
                    description=f"Transform '{transform.name}' discovered {entities_created_count} new entities "
                                f"and {relationships_created_count} new relationships from {input_entity.value}.",
                    event_time=now_utc,
                    icon="sparkles",
                    color="#3B82F6",
                    source=f"Transform: {transform.name}",
                    is_auto_generated=True,
                )
                self.session.add(timeline_event)
                timeline_count = 1
        except Exception as tl_err:
            logger.warning("Failed to create timeline event: %s", tl_err)

        # 9. Finalize Run Record
        run.status = TransformStatus.COMPLETED.value
        run.entities_created = entities_created_count
        run.relationships_created = relationships_created_count
        run.duration_seconds = round(duration, 3)
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        run.output_summary = f"Discovered {len(entities)} entities and {len(relationships)} relationships ({entities_created_count} new entities, {relationships_created_count} new relationships)"
        await self.session.commit()
        await self.session.refresh(run)

        return run

