"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Application health check.

    Returns basic application status for load balancers
    and monitoring systems.
    """
    return {
        "status": "healthy",
        "service": "vestigium",
        "version": "0.1.0",
    }
