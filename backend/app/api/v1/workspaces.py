"""Workspace API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse, IDResponse, SuccessResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[WorkspaceResponse])
async def list_workspaces(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[WorkspaceResponse]:
    """List workspaces accessible to the current user."""
    repo = BaseRepository(Workspace, session)
    offset = (page - 1) * page_size
    workspaces = await repo.list(offset=offset, limit=page_size)
    total = await repo.count()
    return PaginatedResponse.create(
        items=[WorkspaceResponse.model_validate(w) for w in workspaces],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=IDResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a new workspace."""
    repo = BaseRepository(Workspace, session)
    workspace = await repo.create(
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color,
        owner_id=current_user.id,
    )
    await session.commit()
    return IDResponse(id=workspace.id, message="Workspace created successfully")


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Workspace:
    """Get a workspace by ID."""
    repo = BaseRepository(Workspace, session)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace", workspace_id)
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Workspace:
    """Update a workspace."""
    repo = BaseRepository(Workspace, session)
    workspace = await repo.update(
        workspace_id,
        **data.model_dump(exclude_unset=True),
    )
    if not workspace:
        raise NotFoundError("Workspace", workspace_id)
    await session.commit()
    return workspace


@router.delete("/{workspace_id}", response_model=SuccessResponse)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete a workspace (soft delete)."""
    repo = BaseRepository(Workspace, session)
    deleted = await repo.delete(workspace_id)
    if not deleted:
        raise NotFoundError("Workspace", workspace_id)
    await session.commit()
    return SuccessResponse(message="Workspace deleted successfully")
