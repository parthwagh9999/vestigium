"""Tasks API endpoints for investigation case management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.task import Task
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.common import IDResponse, PaginatedResponse, SuccessResponse

router = APIRouter()


class TaskCreate(BaseModel):
    investigation_id: str
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    assigned_to_id: str | None = None
    entity_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to_id: str | None = None


class TaskResponse(BaseModel):
    id: str
    investigation_id: str
    title: str
    description: str | None = None
    status: str
    priority: str
    assigned_to_id: str | None = None
    created_by_id: str | None = None
    entity_id: str | None = None
    created_at: Any | None = None
    updated_at: Any | None = None


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    investigation_id: str = Query(...),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[TaskResponse]:
    """List tasks for an investigation."""
    repo = BaseRepository(Task, session)
    offset = (page - 1) * page_size
    filters = [repo.model.investigation_id == investigation_id]
    if status:
        filters.append(repo.model.status == status)

    tasks = await repo.list(filters=filters, offset=offset, limit=page_size, sort_by="created_at")
    total = await repo.count(filters=filters)

    items = [TaskResponse.model_validate(t) for t in tasks]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=IDResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> IDResponse:
    """Create a new case task."""
    repo = BaseRepository(Task, session)
    task = await repo.create(
        investigation_id=data.investigation_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assigned_to_id=data.assigned_to_id,
        entity_id=data.entity_id,
        created_by_id=current_user.id,
    )
    await session.commit()
    return IDResponse(id=task.id, message="Task created successfully")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> TaskResponse:
    """Update a task status or priority."""
    repo = BaseRepository(Task, session)
    task = await repo.update(task_id, **data.model_dump(exclude_unset=True))
    if not task:
        raise NotFoundError("Task", task_id)
    await session.commit()
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", response_model=SuccessResponse)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse:
    """Delete a task."""
    repo = BaseRepository(Task, session)
    if not await repo.delete(task_id):
        raise NotFoundError("Task", task_id)
    await session.commit()
    return SuccessResponse(message="Task deleted successfully")
