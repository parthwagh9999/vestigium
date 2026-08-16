"""Evidence Locker API endpoints for chain of custody and evidence management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.evidence import Evidence
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.common import IDResponse, PaginatedResponse, SuccessResponse

router = APIRouter()


class EvidenceCreate(BaseModel):
    investigation_id: str
    title: str
    description: str | None = None
    evidence_type: str = "document"
    source: str | None = None
    source_url: str | None = None
    raw_data: str | None = None
    file_path: str | None = None
    file_size_bytes: int | None = None
    file_mime_type: str | None = None
    file_hash_sha256: str | None = None
    entity_id: str | None = None


class EvidenceResponse(BaseModel):
    id: str
    investigation_id: str
    title: str
    description: str | None = None
    evidence_type: str
    source: str | None = None
    source_url: str | None = None
    raw_data: str | None = None
    confidence: float = 1.0
    entity_id: str | None = None
    file_path: str | None = None
    file_hash_sha256: str | None = None
    collected_by_id: str | None = None
    collected_at: Any | None = None
    created_at: Any | None = None


@router.get("", response_model=PaginatedResponse[EvidenceResponse])
async def list_evidence(
    investigation_id: str = Query(...),
    entity_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[EvidenceResponse]:
    """List evidence items for an investigation."""
    repo = BaseRepository(Evidence, session)
    offset = (page - 1) * page_size
    filters = [repo.model.investigation_id == investigation_id]
    
    if entity_id:
        filters.append(repo.model.entity_id == entity_id)

    items_list = await repo.list(filters=filters, offset=offset, limit=page_size, sort_by="created_at")
    total = await repo.count(filters=filters)

    items = [EvidenceResponse.model_validate(e) for e in items_list]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_evidence(
    data: EvidenceCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Log a new evidence item to the evidence locker."""
    repo = BaseRepository(Evidence, session)
    evidence = await repo.create(
        investigation_id=data.investigation_id,
        title=data.title,
        description=data.description,
        evidence_type=data.evidence_type,
        source=data.source,
        source_url=data.source_url,
        raw_data=data.raw_data,
        file_path=data.file_path,
        file_size_bytes=data.file_size_bytes,
        file_mime_type=data.file_mime_type,
        file_hash_sha256=data.file_hash_sha256,
        entity_id=data.entity_id,
        collected_by_id=current_user.id,
    )
    await session.commit()
    return IDResponse(id=evidence.id, message="Evidence logged successfully")


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> EvidenceResponse:
    """Get details for a specific evidence item."""
    repo = BaseRepository(Evidence, session)
    item = await repo.get_by_id(evidence_id)
    if not item:
        raise NotFoundError("Evidence", evidence_id)
    return EvidenceResponse.model_validate(item)


@router.delete("/{evidence_id}", response_model=SuccessResponse)
async def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete an evidence record."""
    repo = BaseRepository(Evidence, session)
    if not await repo.delete(evidence_id):
        raise NotFoundError("Evidence", evidence_id)
    await session.commit()
    return SuccessResponse(message="Evidence deleted successfully")

@router.get("/entity/{entity_id}/contradictions")
async def get_entity_contradictions(
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Detect contradictions in evidence for a specific entity."""
    from app.osint.contradiction import ContradictionEngine
    engine = ContradictionEngine(session)
    conflicts = await engine.detect_conflicts(entity_id)
    return {"conflicts": conflicts}
