"""Investigation Orchestrator.

Handles parallel, rate-limited execution of multiple OSINT transforms against a target entity,
broadcasting live WebSocket progress events as each transform discovers entities.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.models.api_key import APIKeyVault
from app.models.entity import Entity
from app.transforms.registry import transform_registry
from app.transforms.runner import TransformRunner
from app.core.websocket import manager as ws_manager

logger = logging.getLogger(__name__)


class InvestigationOrchestrator:
    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id

    async def run_all_safe_osint(
        self,
        investigation_id: str,
        entity_id: str,
    ) -> dict[str, Any]:
        """Automatically route a target entity through all relevant, passive/safe OSINT modules."""
        # 1. Fetch Target Entity
        stmt = select(Entity).where(Entity.id == entity_id, Entity.investigation_id == investigation_id)
        result = await self.session.execute(stmt)
        entity = result.scalars().first()

        if not entity:
            return {"status": "error", "message": "Target entity not found."}

        entity_type = entity.entity_type
        entity_value = entity.value

        # 2. Query configured API keys
        result_keys = await self.session.execute(
            select(APIKeyVault.service_name).where(APIKeyVault.is_active == True)  # noqa: E712
        )
        active_keys = set(result_keys.scalars().all())

        # 3. Find Applicable Transforms
        applicable_transforms = transform_registry.get_by_input_type(entity_type)

        # Filter for all safe tools (Passive or Low Impact) that are Available
        safe_transforms = []
        for t in applicable_transforms:
            # Skip Active Scanners that require explicit authorized confirmation (e.g. Nmap)
            if getattr(t, "passive_or_active", "PASSIVE") == "ACTIVE_AUTHORIZED" or getattr(t, "authorization_required", False):
                continue

            # Check dynamic availability status
            avail = t.check_availability(active_keys) if hasattr(t, "check_availability") else getattr(t, "availability_status", "AVAILABLE")
            if avail.startswith("AVAILABLE"):
                safe_transforms.append(t)

        if not safe_transforms:
            return {
                "status": "success",
                "message": f"No available safe/passive transforms found for {entity_type}.",
                "results": [],
            }

        logger.info(
            "Orchestrator executing %d safe transforms against %s (%s)",
            len(safe_transforms),
            entity_type,
            entity_value,
        )

        session_factory = get_session_factory()
        semaphore = asyncio.Semaphore(4)  # 4 concurrent workers to avoid overloading

        async def run_single_transform(transform):
            async with semaphore:
                async with session_factory() as task_session:
                    runner = TransformRunner(task_session)
                    try:
                        # Broadcast transform starting
                        await ws_manager.broadcast(
                            investigation_id,
                            {
                                "type": "transform_executing",
                                "investigation_id": investigation_id,
                                "transform_id": transform.id,
                                "entity_id": entity_id,
                                "entity_value": entity_value,
                            },
                        )

                        run = await runner.execute_transform(
                            investigation_id=investigation_id,
                            transform_id=transform.id,
                            input_entity_id=entity_id,
                            user_id=self.user_id,
                            params={},
                        )

                        # Broadcast graph update immediately
                        await ws_manager.broadcast(
                            investigation_id,
                            {
                                "type": "graph_updated",
                                "investigation_id": investigation_id,
                                "entity_id": entity_id,
                                "transform_id": transform.id,
                                "entities_created": run.entities_created,
                                "relationships_created": run.relationships_created,
                            },
                        )

                        return {
                            "id": transform.id,
                            "name": transform.name,
                            "status": "success",
                            "entities_created": run.entities_created,
                            "relationships_created": run.relationships_created,
                        }
                    except Exception as e:
                        logger.error("Orchestrator transform %s failed: %s", transform.id, e)
                        return {
                            "id": transform.id,
                            "name": transform.name,
                            "status": "error",
                            "message": str(e),
                        }

        tasks = [run_single_transform(t) for t in safe_transforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Final completion event
        await ws_manager.broadcast(
            investigation_id,
            {
                "type": "graph_updated",
                "investigation_id": investigation_id,
                "entity_id": entity_id,
                "entities_created": sum(r.get("entities_created", 0) for r in results if isinstance(r, dict)),
            },
        )

        return {
            "status": "success",
            "message": f"Orchestrated {len(safe_transforms)} safe OSINT modules against {entity_value}.",
            "results": [r for r in results if isinstance(r, dict)],
        }
