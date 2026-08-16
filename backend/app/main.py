"""FastAPI application factory.

Creates and configures the main FastAPI application with all middleware,
routes, exception handlers, and startup/shutdown lifecycle events.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.core.exceptions import VestigiumError
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.engine import create_engine
from app.db.session import init_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager — handles startup and shutdown.

    Startup:
        - Initialize database engine and session factory
        - Create database tables if they don't exist
        - Seed default roles and permissions
        - Start background scheduler for auto-backups

    Shutdown:
        - Close database connections
        - Shut down background workers
    """
    settings: Settings = app.state.settings

    setup_logging(settings.log_level, settings.log_format)
    logger.info("Starting VESTIGIUM v%s", settings.app_version)

    engine = create_engine(settings)
    init_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    from app.services.seed import seed_defaults
    await seed_defaults()
    logger.info("Default roles and permissions seeded")

    from app.transforms.builtin import register_builtin_transforms
    register_builtin_transforms()
    logger.info("Built-in OSINT transforms registered")
    
    from app.services.tool_health import ToolHealthService
    await ToolHealthService.run_startup_checks()

    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.backup_path.mkdir(parents=True, exist_ok=True)
    settings.plugin_path.mkdir(parents=True, exist_ok=True)

    yield

    await engine.dispose()
    logger.info("VESTIGIUM shut down cleanly")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful for testing).

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Enterprise-grade open-source OSINT investigation platform with visual link-analysis",
        version=settings.app_version,
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = settings

    _setup_middleware(app, settings)
    _setup_exception_handlers(app)
    _setup_routes(app)

    return app


def _setup_middleware(app: FastAPI, settings: Settings) -> None:
    """Configure application middleware stack."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    )


def _setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(VestigiumError)
    async def vestigium_error_handler(request: Request, exc: VestigiumError) -> JSONResponse:
        """Handle all Vestigium-specific exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": 500,
            },
        )


def _setup_routes(app: FastAPI) -> None:
    """Register all API route modules."""
    from app.api.v1.router import api_v1_router
    from app.api.v1.ws import router as ws_router

    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(ws_router)
