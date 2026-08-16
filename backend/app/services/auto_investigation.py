"""Auto-Investigation and Recursive Discovery Engine.

Executes recursive OSINT transforms up to N layers deep (default: 10 layers),
with strict loop prevention via entity fingerprinting, transform deduplication,
and real-time WebSocket progress broadcasting.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket import manager as ws_manager
from app.models.entity import Entity
from app.models.transform import TransformRun, TransformResult, TransformStatus
from app.repositories.entity import EntityRepository
from app.transforms.registry import transform_registry
from app.transforms.runner import TransformRunner

logger = logging.getLogger(__name__)


class AutoInvestigationTaskState:
    """State tracker for a running recursive investigation."""

    def __init__(self, investigation_id: str, max_depth: int = 10, max_entities: int = 500) -> None:
        self.investigation_id = investigation_id
        self.max_depth = max_depth
        self.max_entities = max_entities
        self.is_running = True
        self.is_paused = False
        self.current_depth = 0
        self.total_discovered = 0
        self.executed_transforms: set[str] = set()  # (entity_id, transform_id)
        self.processed_fingerprints: set[str] = set()  # entity_type:value


# In-memory registry of active auto-investigations
_active_investigations: dict[str, AutoInvestigationTaskState] = {}


def get_auto_investigation_state(investigation_id: str) -> AutoInvestigationTaskState | None:
    return _active_investigations.get(investigation_id)


def stop_auto_investigation(investigation_id: str) -> bool:
    state = _active_investigations.get(investigation_id)
    if state:
        state.is_running = False
        return True
    return False


class AutoInvestigationEngine:
    """Recursive OSINT discovery engine."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.entity_repo = EntityRepository(session)
        self.runner = TransformRunner(session)

    async def start_recursive_investigation(
        self,
        investigation_id: str,
        root_entity_id: str | None = None,
        max_depth: int = 10,
        max_entities: int = 500,
        user_id: str | None = None,
        allowed_transforms: list[str] | None = None,
    ) -> AutoInvestigationTaskState:
        """Start or resume a background recursive investigation.

        Args:
            investigation_id: Investigation ID
            root_entity_id: Optional root entity to expand from (if None, discovers all entities)
            max_depth: Maximum recursion depth (1 to 10 layers)
            max_entities: Hard cap on total entities created to prevent runaway graphs
            user_id: ID of user launching investigation

        Returns:
            AutoInvestigationTaskState tracking progress
        """
        state = AutoInvestigationTaskState(
            investigation_id=investigation_id,
            max_depth=min(10, max(1, max_depth)),
            max_entities=max_entities,
        )
        _active_investigations[investigation_id] = state

        # Fetch initial queue entities
        if root_entity_id:
            root_ent = await self.entity_repo.get_by_id(root_entity_id)
            initial_entities = [root_ent] if root_ent else []
        else:
            initial_entities = await self.entity_repo.get_by_investigation(investigation_id, limit=100)

        all_existing = await self.entity_repo.get_by_investigation(investigation_id, limit=10000)

        # Broadcast start event over WebSocket
        await ws_manager.broadcast(
            investigation_id,
            {
                "type": "auto_investigation_started",
                "investigation_id": investigation_id,
                "max_depth": state.max_depth,
                "max_entities": state.max_entities,
            },
        )

        # 4. Launch recursive queue loop
        current_layer_entities = [e for e in initial_entities if e]

        for depth in range(1, state.max_depth + 1):
            if not state.is_running or not current_layer_entities:
                break

            if state.total_discovered >= state.max_entities:
                logger.info("Auto-investigation reached max newly discovered entity limit: %d", state.max_entities)
                break

            state.current_depth = depth
            logger.info("Auto-investigation depth layer %d for investigation %s (%d candidate entities)", depth, investigation_id, len(current_layer_entities))

            next_layer_entities: list[Entity] = []

            for entity in current_layer_entities:
                if not state.is_running:
                    break

                # Query compatible transforms from registry for entity type
                compatible_transforms = transform_registry.get_by_input_type(entity.entity_type)
                if allowed_transforms is not None:
                    compatible_transforms = [t for t in compatible_transforms if t.id in allowed_transforms]

                for transform in compatible_transforms:
                    if not state.is_running:
                        break
                        
                    # Enforce recursive limits and availability status
                    if not getattr(transform, "supports_recursive_investigation", True):
                        continue
                    if not getattr(transform, "availability_status", "AVAILABLE").startswith("AVAILABLE"):
                        continue
                    # Never auto-execute ACTIVE_AUTHORIZED tools (e.g. Nmap)
                    if getattr(transform, "passive_or_active", "PASSIVE") == "ACTIVE_AUTHORIZED":
                        continue

                    key = f"{entity.id}:{transform.id}"
                    if key in state.executed_transforms:
                        continue  # Skip already executed transform (loop prevention)

                    state.executed_transforms.add(key)

                    try:
                        # Broadcast transform starting
                        await ws_manager.broadcast(
                            investigation_id,
                            {
                                "type": "transform_executing",
                                "investigation_id": investigation_id,
                                "transform_id": transform.id,
                                "entity_id": entity.id,
                                "entity_value": entity.value,
                                "depth": depth,
                            },
                        )

                        # Execute transform
                        run = await self.runner.execute_transform(
                            investigation_id=investigation_id,
                            transform_id=transform.id,
                            input_entity_id=entity.id,
                            user_id=user_id,
                        )

                        if run.status == TransformStatus.COMPLETED.value:
                            if run.entities_created > 0:
                                state.total_discovered += run.entities_created

                            # Broadcast graph updated event over WebSocket so canvas auto-renders!
                            await ws_manager.broadcast(
                                investigation_id,
                                {
                                    "type": "graph_updated",
                                    "investigation_id": investigation_id,
                                    "entities_created": run.entities_created,
                                    "relationships_created": run.relationships_created,
                                    "depth": depth,
                                },
                            )

                            # Retrieve newly created entities for this specific transform run
                            res_ents = await self.session.execute(
                                select(Entity)
                                .join(TransformResult, Entity.id == TransformResult.entity_id)
                                .where(TransformResult.transform_run_id == run.id)
                            )
                            newly_created_entities = res_ents.scalars().all()
                            for new_ent in newly_created_entities:
                                fp = f"{new_ent.entity_type}:{new_ent.value.lower()}"
                                if fp not in state.processed_fingerprints:
                                    state.processed_fingerprints.add(fp)
                                    next_layer_entities.append(new_ent)

                    except Exception as e:
                        ent_val = getattr(entity, "value", str(entity))
                        logger.warning("Error running %s on %s during auto-investigation: %s", transform.id, ent_val, e)
                        try:
                            await self.session.rollback()
                        except Exception:
                            pass

            current_layer_entities = next_layer_entities

        state.is_running = False

        # Broadcast completion
        await ws_manager.broadcast(
            investigation_id,
            {
                "type": "auto_investigation_completed",
                "investigation_id": investigation_id,
                "final_depth": state.current_depth,
                "total_discovered": state.total_discovered,
            },
        )

        # Remove from active investigations so it can be re-triggered
        _active_investigations.pop(investigation_id, None)

        logger.info(
            "Auto-investigation completed for %s: depth=%d, discovered=%d entities",
            investigation_id, state.current_depth, state.total_discovered,
        )

        return state
