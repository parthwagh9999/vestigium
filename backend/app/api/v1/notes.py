"""Notes API endpoints for analyst annotations."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.note import Note
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.common import IDResponse, PaginatedResponse, SuccessResponse

router = APIRouter()


class NoteCreate(BaseModel):
    investigation_id: str
    entity_id: str | None = None
    title: str | None = None
    content: str
    is_pinned: bool = False
    color: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_pinned: bool | None = None
    color: str | None = None


class NoteResponse(BaseModel):
    id: str
    investigation_id: str
    entity_id: str | None = None
    title: str | None = None
    content: str
    is_pinned: bool
    author_id: str | None = None
    color: str | None = None
    created_at: Any | None = None
    updated_at: Any | None = None


@router.get("", response_model=PaginatedResponse[NoteResponse])
async def list_notes(
    investigation_id: str = Query(...),
    entity_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[NoteResponse]:
    """List notes for an investigation or entity."""
    repo = BaseRepository(Note, session)
    offset = (page - 1) * page_size
    filters = [repo.model.investigation_id == investigation_id]
    if entity_id:
        filters.append(repo.model.entity_id == entity_id)

    notes = await repo.list(filters=filters, offset=offset, limit=page_size, sort_by="created_at")
    total = await repo.count(filters=filters)

    items = [NoteResponse.model_validate(n) for n in notes]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a new analyst note."""
    repo = BaseRepository(Note, session)
    note = await repo.create(
        investigation_id=data.investigation_id,
        entity_id=data.entity_id,
        title=data.title,
        content=data.content,
        is_pinned=data.is_pinned,
        color=data.color,
        author_id=current_user.id,
    )
    await session.commit()
    return IDResponse(id=note.id, message="Note created successfully")


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    data: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> NoteResponse:
    """Update a note."""
    repo = BaseRepository(Note, session)
    note = await repo.update(note_id, **data.model_dump(exclude_unset=True))
    if not note:
        raise NotFoundError("Note", note_id)
    await session.commit()
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", response_model=SuccessResponse)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete a note."""
    repo = BaseRepository(Note, session)
    if not await repo.delete(note_id):
        raise NotFoundError("Note", note_id)
    await session.commit()
    return SuccessResponse(message="Note deleted successfully")
