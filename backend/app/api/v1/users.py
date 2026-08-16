"""User management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.dependencies import get_current_active_user, get_superuser
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_superuser),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[UserResponse]:
    """List all users (admin only)."""
    repo = UserRepository(session)
    offset = (page - 1) * page_size
    users = await repo.list(offset=offset, limit=page_size)
    total = await repo.count()
    return PaginatedResponse.create(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Get a user by ID."""
    from app.core.exceptions import NotFoundError
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user
