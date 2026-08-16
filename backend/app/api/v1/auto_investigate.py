"""API Endpoints for Auto-Investigation Engine."""

from __future__ import annotations

import asyncio
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session, get_session_factory
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.auto_investigation import (
    AutoInvestigationEngine,
    get_auto_investigation_state,
    stop_auto_investigation,
)

router = APIRouter(prefix="/investigations", tags=["Auto-Investigation Engine"])


class AutoInvestigateRequest(BaseModel):
    root_entity_id: str | None = Field(None, description="Optional starting entity ID")
    max_depth: int = Field(10, ge=1, le=10, description="Max recursion depth layer (1 to 10)")
    max_entities: int = Field(500, ge=10, le=10000, description="Max entities limit")
    allowed_transforms: list[str] | None = Field(None, description="Optional list of specific transform IDs to execute. If None, all compatible are executed.")


async def run_auto_investigation_background(
    investigation_id: str,
    root_entity_id: str | None,
    max_depth: int,
    max_entities: int,
    user_id: str,
    allowed_transforms: list[str] | None = None,
) -> None:
    """Background worker function for recursive investigation."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            engine = AutoInvestigationEngine(session)
            await engine.start_recursive_investigation(
                investigation_id=investigation_id,
                root_entity_id=root_entity_id,
                max_depth=max_depth,
                max_entities=max_entities,
                user_id=user_id,
                allowed_transforms=allowed_transforms,
            )
    except Exception as e:
        import traceback
        with open("crash.log", "a") as f:
            f.write(f"Crash in auto investigation:\n{traceback.format_exc()}\n")


@router.post("/{investigation_id}/auto-investigate", status_code=status.HTTP_202_ACCEPTED)
async def start_auto_investigation(
    investigation_id: str,
    body: AutoInvestigateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Start recursive N-layer OSINT discovery for an investigation."""
    existing_state = get_auto_investigation_state(investigation_id)
    if existing_state and existing_state.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Auto-investigation is already actively running for this investigation.",
        )

    background_tasks.add_task(
        run_auto_investigation_background,
        investigation_id,
        body.root_entity_id,
        body.max_depth,
        body.max_entities,
        current_user.id,
        body.allowed_transforms,
    )

    return {
        "status": "started",
        "investigation_id": investigation_id,
        "max_depth": body.max_depth,
        "max_entities": body.max_entities,
        "message": f"Recursive auto-investigation launched up to depth layer {body.max_depth}",
    }


@router.post("/{investigation_id}/auto-investigate/stop")
async def stop_auto_investigation_endpoint(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Stop/Pause active recursive auto-investigation."""
    success = stop_auto_investigation(investigation_id)
    if not success:
        return {"status": "not_running", "message": "No active auto-investigation found to stop."}
    return {"status": "stopping", "message": "Auto-investigation stop requested."}


@router.get("/{investigation_id}/auto-investigate/status")
async def get_auto_investigation_status(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get live status of auto-investigation."""
    state = get_auto_investigation_state(investigation_id)
    if not state:
        return {"is_running": False, "current_depth": 0, "total_discovered": 0}

    return {
        "is_running": state.is_running,
        "current_depth": state.current_depth,
        "max_depth": state.max_depth,
        "total_discovered": state.total_discovered,
        "max_entities": state.max_entities,
    }


class OrchestrateRequest(BaseModel):
    entity_id: str = Field(..., description="Target entity ID to orchestrate")

@router.post("/{investigation_id}/orchestrate")
async def orchestrate_target(
    investigation_id: str,
    body: OrchestrateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Orchestrate all safe passive OSINT tools simultaneously against a target entity."""
    from app.osint.orchestrator import InvestigationOrchestrator
    
    orchestrator = InvestigationOrchestrator(session, current_user.id)
    
    # We await this directly since it's just firing off tasks using asyncio.gather
    # If the transforms themselves are background-heavy, we could background this whole endpoint.
    # For now we'll run it and return the immediate result summaries.
    result = await orchestrator.run_all_safe_osint(investigation_id, body.entity_id)
    
    return result
