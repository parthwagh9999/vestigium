"""API v1 router — aggregates all v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.entities import router as entities_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.notes import router as notes_router
from app.api.v1.relationships import router as relationships_router
from app.api.v1.search import router as search_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.transforms import router as transforms_router
from app.api.v1.tools import router as tools_router
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.auto_investigate import router as auto_investigate_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
api_v1_router.include_router(investigations_router, prefix="/investigations", tags=["Investigations"])
api_v1_router.include_router(entities_router, prefix="/entities", tags=["Entities"])
api_v1_router.include_router(relationships_router, prefix="/relationships", tags=["Relationships"])
api_v1_router.include_router(graph_router, prefix="/graph", tags=["Graph"])
api_v1_router.include_router(search_router, prefix="/search", tags=["Search"])
api_v1_router.include_router(transforms_router, prefix="/transforms", tags=["Transforms"])
api_v1_router.include_router(tools_router, prefix="/tools", tags=["Tools"])
api_v1_router.include_router(notes_router, prefix="/notes", tags=["Notes"])
api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_v1_router.include_router(evidence_router, prefix="/evidence", tags=["Evidence"])
api_v1_router.include_router(auto_investigate_router)
