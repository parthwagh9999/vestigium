"""Entity API endpoints with CRUD, bulk operations, and search."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.repositories.entity import EntityRepository
from app.schemas.common import BulkOperationResponse, IDResponse, PaginatedResponse, SuccessResponse
from app.schemas.entity import (
    EntityBulkCreate,
    EntityBulkPositionUpdate,
    EntityCreate,
    EntityResponse,
    EntityUpdate,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EntityResponse])
async def list_entities(
    investigation_id: str = Query(...),
    entity_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=5000),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[EntityResponse]:
    """List entities for an investigation."""
    repo = EntityRepository(session)
    offset = (page - 1) * page_size
    entities = await repo.get_by_investigation(
        investigation_id, entity_type=entity_type, offset=offset, limit=page_size
    )
    total = await repo.count(
        filters=[repo.model.investigation_id == investigation_id]
    )

    items = []
    for entity in entities:
        resp = EntityResponse.model_validate(entity)
        if entity.properties:
            try:
                resp.properties = json.loads(entity.properties)
            except (json.JSONDecodeError, TypeError):
                resp.properties = None
        items.append(resp)

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_entity(
    data: EntityCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a new entity with automatic markdown and URL sanitization."""
    import re
    repo = EntityRepository(session)
    properties_json = json.dumps(data.properties) if data.properties else None

    raw_val = data.value.strip()
    label = data.label or raw_val
    clean_val = raw_val

    # Detect markdown link: [Label](https://...)
    md_match = re.search(r"\[(.*?)\]\((https?://[^\s)]+)\)", raw_val)
    if md_match:
        label = md_match.group(1).strip() or label
        clean_val = md_match.group(2).strip()

    # Clean domain / subdomain / IP
    if data.entity_type in ("domain", "subdomain", "ip_address"):
        clean_val = clean_val.replace("https://", "").replace("http://", "").split("/")[0].split("?")[0].strip().lower()
        if clean_val.startswith("www."):
            clean_val = clean_val[4:]
        if not md_match and not data.label:
            label = clean_val
    elif data.entity_type == "email":
        clean_val = clean_val.replace("mailto:", "").strip().lower()

    entity = await repo.upsert_entity(
        investigation_id=data.investigation_id,
        entity_type=data.entity_type,
        label=label,
        value=clean_val,
        properties=properties_json,
        confidence=data.confidence,
        source=data.source,
        icon=data.icon,
        color=data.color,
        position_x=data.position_x,
        position_y=data.position_y,
        notes_text=data.notes_text,
    )
    await session.commit()
    return IDResponse(id=entity.id, message="Entity created")


@router.post("/bulk", response_model=BulkOperationResponse, status_code=201)
async def bulk_create_entities(
    data: EntityBulkCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> BulkOperationResponse:
    """Create multiple entities in a single request."""
    repo = EntityRepository(session)
    created_ids: list[str] = []
    errors: list[dict[str, str]] = []

    for entity_data in data.entities:
        try:
            properties_json = json.dumps(entity_data.properties) if entity_data.properties else None
            entity = await repo.upsert_entity(
                investigation_id=data.investigation_id,
                entity_type=entity_data.entity_type,
                label=entity_data.label,
                value=entity_data.value,
                properties=properties_json,
                confidence=entity_data.confidence,
                source=entity_data.source,
                icon=entity_data.icon,
                color=entity_data.color,
                position_x=entity_data.position_x,
                position_y=entity_data.position_y,
            )
            created_ids.append(entity.id)
        except Exception as e:
            errors.append({"entity": entity_data.value, "error": str(e)})

    await session.commit()
    return BulkOperationResponse(
        success_count=len(created_ids),
        error_count=len(errors),
        errors=errors,
        created_ids=created_ids,
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> EntityResponse:
    """Get an entity by ID."""
    repo = EntityRepository(session)
    entity = await repo.get_by_id(entity_id)
    if not entity:
        raise NotFoundError("Entity", entity_id)

    resp = EntityResponse.model_validate(entity)
    if entity.properties:
        try:
            resp.properties = json.loads(entity.properties)
        except (json.JSONDecodeError, TypeError):
            resp.properties = None
    return resp


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    data: EntityUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> EntityResponse:
    """Update an entity."""
    repo = EntityRepository(session)
    update_data = data.model_dump(exclude_unset=True)

    if "properties" in update_data and update_data["properties"] is not None:
        update_data["properties"] = json.dumps(update_data["properties"])

    entity = await repo.update(entity_id, **update_data)
    if not entity:
        raise NotFoundError("Entity", entity_id)
    await session.commit()

    resp = EntityResponse.model_validate(entity)
    if entity.properties:
        try:
            resp.properties = json.loads(entity.properties)
        except (json.JSONDecodeError, TypeError):
            resp.properties = None
    return resp


@router.delete("/{entity_id}", response_model=SuccessResponse)
async def delete_entity(
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete an entity."""
    repo = EntityRepository(session)
    if not await repo.delete(entity_id):
        raise NotFoundError("Entity", entity_id)
    await session.commit()
    return SuccessResponse(message="Entity deleted")


@router.put("/positions/bulk", response_model=SuccessResponse)
async def bulk_update_positions(
    data: EntityBulkPositionUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Bulk update entity positions (drag/drop)."""
    repo = EntityRepository(session)
    count = await repo.bulk_update_positions(
        [p.model_dump() for p in data.positions]
    )
    await session.commit()
    return SuccessResponse(message=f"Updated {count} entity positions")


@router.get("/{entity_id}/neighbors", response_model=list[EntityResponse])
async def get_entity_neighbors(
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[EntityResponse]:
    """Get all entities directly connected to a given entity."""
    repo = EntityRepository(session)
    neighbors = await repo.get_neighbors(entity_id)
    return [EntityResponse.model_validate(n) for n in neighbors]
