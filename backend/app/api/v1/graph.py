"""Graph analysis API endpoints — statistics, pathfinding, layouts, centrality."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.services.graph import GraphService

router = APIRouter()


@router.get("/{investigation_id}/statistics")
async def get_graph_statistics(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get graph statistics for an investigation."""
    service = GraphService(session)
    return await service.get_statistics(investigation_id)


@router.get("/{investigation_id}/shortest-path")
async def find_shortest_path(
    investigation_id: str,
    source_id: str = Query(...),
    target_id: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Find shortest path between two entities."""
    service = GraphService(session)
    path = await service.find_shortest_path(investigation_id, source_id, target_id)
    return {"path": path, "length": len(path) - 1 if path else None}


@router.get("/{investigation_id}/centrality")
async def get_centrality(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, dict[str, float]]:
    """Compute centrality measures for all entities."""
    service = GraphService(session)
    return await service.get_centrality(investigation_id)


@router.post("/{investigation_id}/layout")
async def compute_layout(
    investigation_id: str,
    algorithm: str = Query(default="spring"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, dict[str, float]]:
    """Compute auto-layout positions for entities."""
    service = GraphService(session)
    return await service.compute_layout(investigation_id, algorithm=algorithm)


@router.get("/{investigation_id}/communities")
async def find_communities(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[list[str]]:
    """Detect communities/clusters in the graph."""
    service = GraphService(session)
    return await service.find_communities(investigation_id)
