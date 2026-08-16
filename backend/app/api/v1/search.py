"""Search API endpoints — global, entity, and relationship search."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.repositories.entity import EntityRepository
from app.schemas.common import PaginatedResponse
from app.schemas.entity import EntityResponse, EntitySearchRequest

router = APIRouter()


@router.post("/entities", response_model=PaginatedResponse[EntityResponse])
async def search_entities(
    data: EntitySearchRequest,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[EntityResponse]:
    """Search entities across investigations with filters."""
    repo = EntityRepository(session)
    offset = (page - 1) * page_size

    entities, total = await repo.search(
        investigation_id=data.investigation_id,
        query=data.query,
        entity_types=data.entity_types,
        min_confidence=data.min_confidence,
        max_confidence=data.max_confidence,
        offset=offset,
        limit=page_size,
    )

    items = [EntityResponse.model_validate(e) for e in entities]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/global")
async def global_search(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Global search across all entities."""
    repo = EntityRepository(session)
    offset = (page - 1) * page_size

    entities, total = await repo.search(
        query=q,
        offset=offset,
        limit=page_size,
    )

    return {
        "query": q,
        "total": total,
        "page": page,
        "results": [EntityResponse.model_validate(e).model_dump() for e in entities],
    }
