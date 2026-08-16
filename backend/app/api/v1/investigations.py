"""Investigation API endpoints with full CRUD, versioning, and snapshots."""

import json
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.investigation import Investigation
from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.repositories.investigation import InvestigationRepository
from app.schemas.common import IDResponse, PaginatedResponse, SuccessResponse
from app.schemas.investigation import (
    BulkDeleteNodes,
    InvestigationCreate,
    InvestigationDetailResponse,
    InvestigationResponse,
    InvestigationSnapshotCreate,
    InvestigationSnapshotResponse,
    InvestigationUpdate,
    InvestigationVersionResponse,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[InvestigationResponse])
async def list_investigations(
    workspace_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[InvestigationResponse]:
    """List investigations with optional filtering."""
    repo = InvestigationRepository(session)
    offset = (page - 1) * page_size

    if workspace_id:
        investigations = await repo.get_by_workspace(
            workspace_id, offset=offset, limit=page_size, status=status
        )
    else:
        filters = []
        if status:
            from app.models.investigation import Investigation
            filters.append(Investigation.status == status)
        investigations = await repo.list(filters=filters, offset=offset, limit=page_size)

    total = await repo.count()

    items = []
    for inv in investigations:
        resp = InvestigationResponse.model_validate(inv)
        resp.entity_count = await repo.get_entity_count(inv.id)
        resp.relationship_count = await repo.get_relationship_count(inv.id)
        items.append(resp)

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_investigation(
    data: InvestigationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a new investigation."""
    repo = InvestigationRepository(session)
    investigation = await repo.create(
        name=data.name,
        description=data.description,
        workspace_id=data.workspace_id,
        owner_id=current_user.id,
        priority=data.priority,
        icon=data.icon,
        color=data.color,
        template_id=data.template_id,
    )

    # Auto-detect and create root target entity if name matches domain/IP/URL/email
    import re
    raw_name = data.name.strip()
    clean_target = raw_name.replace("https://", "").replace("http://", "").split("/")[0].split("?")[0].strip()
    if clean_target and "." in clean_target:
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", clean_target):
            e_type = "ip_address"
        elif "@" in clean_target:
            e_type = "email"
        else:
            e_type = "subdomain" if len(clean_target.split(".")) > 2 else "domain"

        from app.repositories.entity import EntityRepository
        entity_repo = EntityRepository(session)
        target_entity = await entity_repo.upsert_entity(
            investigation_id=investigation.id,
            entity_type=e_type,
            label=clean_target,
            value=clean_target,
            confidence=1.0,
            source="Target Initializer",
            position_x=0.0,
            position_y=0.0,
        )
        
        investigation.root_entity_id = target_entity.id

    await session.commit()
    return IDResponse(id=investigation.id, message="Investigation created")


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
async def get_investigation(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> InvestigationDetailResponse:
    """Get investigation details including graph state."""
    repo = InvestigationRepository(session)
    investigation = await repo.get_by_id(investigation_id)
    if not investigation:
        raise NotFoundError("Investigation", investigation_id)

    resp = InvestigationDetailResponse.model_validate(investigation)
    resp.entity_count = await repo.get_entity_count(investigation_id)
    resp.relationship_count = await repo.get_relationship_count(investigation_id)
    return resp


@router.put("/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: str,
    data: InvestigationUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> InvestigationResponse:
    """Update an investigation."""
    repo = InvestigationRepository(session)
    investigation = await repo.update(
        investigation_id,
        **data.model_dump(exclude_unset=True),
    )
    if not investigation:
        raise NotFoundError("Investigation", investigation_id)
    await session.commit()
    return InvestigationResponse.model_validate(investigation)


@router.delete("/{investigation_id}", response_model=SuccessResponse)
async def delete_investigation(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete an investigation completely (hard delete) along with its data."""
    repo = InvestigationRepository(session)
    
    # Check if exists
    inv = await repo.get_by_id(investigation_id)
    if not inv:
        raise NotFoundError("Investigation", investigation_id)
        
    # Hard delete entities and relationships first (bypass soft delete)
    await session.execute(delete(EntityRelationship).where(EntityRelationship.investigation_id == investigation_id))
    await session.execute(delete(Entity).where(Entity.investigation_id == investigation_id))
    
    # Hard delete the investigation itself
    if not await repo.delete(investigation_id, hard=True):
        raise NotFoundError("Investigation", investigation_id)
        
    await session.commit()
    return SuccessResponse(message="Investigation and all its data deleted completely")


@router.post("/{investigation_id}/snapshots", response_model=InvestigationSnapshotResponse, status_code=201)
async def create_snapshot(
    investigation_id: str,
    data: InvestigationSnapshotCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> InvestigationSnapshotResponse:
    """Create a named snapshot of the current investigation state."""
    repo = InvestigationRepository(session)
    investigation = await repo.get_by_id(investigation_id)
    if not investigation:
        raise NotFoundError("Investigation", investigation_id)

    snapshot = await repo.create_snapshot(
        investigation_id=investigation_id,
        name=data.name,
        graph_state=investigation.graph_state or "{}",
        description=data.description,
        canvas_viewport=investigation.canvas_viewport,
        created_by_id=current_user.id,
    )
    await session.commit()
    return InvestigationSnapshotResponse.model_validate(snapshot)


@router.get("/{investigation_id}/export/json")
async def export_investigation_json(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Export investigation as structured JSON."""
    from app.services.export_import import ExportImportService
    service = ExportImportService(session)
    data = await service.export_json(investigation_id)
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.json"'},
    )


@router.get("/{investigation_id}/export/csv")
async def export_investigation_csv(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Export investigation entities as CSV."""
    from app.services.export_import import ExportImportService
    service = ExportImportService(session)
    csv_data = await service.export_csv(investigation_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.csv"'},
    )


@router.get("/{investigation_id}/export/graphml")
async def export_investigation_graphml(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Export investigation graph as GraphML XML standard format."""
    from app.services.export_import import ExportImportService
    service = ExportImportService(session)
    xml_data = await service.export_graphml(investigation_id)
    return Response(
        content=xml_data,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.graphml"'},
    )


@router.get("/{investigation_id}/export/markdown")
async def export_investigation_markdown(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Export comprehensive OSINT investigation report as Markdown."""
    from app.services.export_service import generate_markdown_report
    md_data = await generate_markdown_report(session, investigation_id)
    return Response(
        content=md_data,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}_report.md"'},
    )


@router.post("/import/json", response_model=InvestigationResponse, status_code=201)
async def import_investigation_json(
    workspace_id: str = Query(...),
    file_data: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> InvestigationResponse:
    """Import investigation from JSON payload."""
    from app.services.export_import import ExportImportService
    service = ExportImportService(session)
    inv = await service.import_json(workspace_id=workspace_id, data=file_data, user_id=current_user.id)
    return InvestigationResponse.model_validate(inv)


@router.delete("/{investigation_id}/nodes")
async def bulk_delete_nodes(
    investigation_id: str,
    payload: BulkDeleteNodes,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Bulk delete nodes and their relationships from an investigation."""
    inv = await session.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    node_ids = payload.node_ids
    if not node_ids:
        return {"deleted": 0}
        
    # Delete relationships where source or target is in node_ids
    stmt_rels = delete(EntityRelationship).where(
        (EntityRelationship.investigation_id == investigation_id) &
        ((EntityRelationship.source_id.in_(node_ids)) | (EntityRelationship.target_id.in_(node_ids)))
    )
    await session.execute(stmt_rels)
    
    # Delete entities
    stmt_ents = delete(Entity).where(
        (Entity.investigation_id == investigation_id) &
        (Entity.id.in_(node_ids))
    )
    res = await session.execute(stmt_ents)
    await session.commit()
    
    return {"deleted": res.rowcount}


@router.delete("/{investigation_id}/clear")
async def clear_investigation_graph(
    investigation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete all nodes and relationships from an investigation."""
    inv = await session.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    # Delete all relationships
    await session.execute(delete(EntityRelationship).where(EntityRelationship.investigation_id == investigation_id))
    
    # Delete all entities
    res = await session.execute(delete(Entity).where(Entity.investigation_id == investigation_id))
    await session.commit()
    
    return {"deleted": res.rowcount}
