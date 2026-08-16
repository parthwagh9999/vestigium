"""Transform API endpoints for listing and executing transforms."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.transform import TransformRun
from app.repositories.base import BaseRepository
from app.schemas.common import PaginatedResponse
from app.transforms.registry import transform_registry
from app.transforms.runner import TransformRunner

router = APIRouter()


class TransformParamSchema(BaseModel):
    name: str
    display_name: str
    param_type: str
    description: str | None = None
    required: bool
    default: Any = None
    options: list[str] | None = None


class TransformSchema(BaseModel):
    id: str
    name: str
    description: str
    category: str
    author: str
    version: str
    input_entity_types: list[str]
    output_entity_types: list[str]
    params: list[TransformParamSchema]
    requires_api_key: bool


class ExecuteTransformRequest(BaseModel):
    investigation_id: str
    transform_id: str
    input_entity_id: str
    params: dict[str, Any] | None = None


class TransformRunResponse(BaseModel):
    id: str
    investigation_id: str
    transform_id: str
    transform_name: str
    status: str
    input_entity_id: str | None = None
    entities_created: int
    relationships_created: int
    duration_seconds: float | None = None
    output_summary: str | None = None
    error_message: str | None = None
    created_at: Any | None = None


@router.get("", response_model=list[TransformSchema])
async def list_transforms(
    input_type: str | None = Query(default=None, description="Filter transforms by input entity type"),
    current_user: User = Depends(get_current_active_user),
) -> list[TransformSchema]:
    """List all available transforms, optionally filtered by input entity type."""
    if input_type:
        transforms = transform_registry.get_by_input_type(input_type)
    else:
        transforms = transform_registry.list_all()

    output = []
    for t in transforms:
        output.append(
            TransformSchema(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category,
                author=t.author,
                version=t.version,
                input_entity_types=t.input_entity_types,
                output_entity_types=t.output_entity_types,
                params=[
                    TransformParamSchema(
                        name=p.name,
                        display_name=p.display_name,
                        param_type=p.param_type,
                        description=p.description,
                        required=p.required,
                        default=p.default,
                        options=p.options,
                    )
                    for p in t.params
                ],
                requires_api_key=t.requires_api_key,
            )
        )
    return output


@router.post("/execute", response_model=TransformRunResponse)
async def execute_transform(
    request: ExecuteTransformRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> TransformRunResponse:
    """Execute a transform on an entity within an investigation."""
    runner = TransformRunner(session)
    run = await runner.execute_transform(
        investigation_id=request.investigation_id,
        transform_id=request.transform_id,
        input_entity_id=request.input_entity_id,
        params=request.params,
        user_id=current_user.id,
    )

    return TransformRunResponse(
        id=run.id,
        investigation_id=run.investigation_id,
        transform_id=run.transform_id,
        transform_name=run.transform_name,
        status=run.status,
        input_entity_id=run.input_entity_id,
        entities_created=run.entities_created,
        relationships_created=run.relationships_created,
        duration_seconds=run.duration_seconds,
        output_summary=run.output_summary,
        error_message=run.error_message,
        created_at=run.created_at,
    )


@router.get("/runs", response_model=PaginatedResponse[TransformRunResponse])
async def list_transform_runs(
    investigation_id: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[TransformRunResponse]:
    """List execution history of transforms for an investigation."""
    repo = BaseRepository(TransformRun, session)
    offset = (page - 1) * page_size
    runs = await repo.list(
        filters=[repo.model.investigation_id == investigation_id],
        offset=offset,
        limit=page_size,
        sort_by="created_at",
    )
    total = await repo.count(filters=[repo.model.investigation_id == investigation_id])

    items = [
        TransformRunResponse(
            id=run.id,
            investigation_id=run.investigation_id,
            transform_id=run.transform_id,
            transform_name=run.transform_name,
            status=run.status,
            input_entity_id=run.input_entity_id,
            entities_created=run.entities_created,
            relationships_created=run.relationships_created,
            duration_seconds=run.duration_seconds,
            output_summary=run.output_summary,
            error_message=run.error_message,
            created_at=run.created_at,
        )
        for run in runs
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
