"""Health and readiness endpoints.

``/health`` is a lightweight liveness probe; ``/ready`` additionally checks
that downstream dependencies (MongoDB) are reachable.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.db.mongo import ping

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — process is up."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }


@router.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe — dependencies are reachable."""
    mongo_ok = await ping()
    return {
        "status": "ready" if mongo_ok else "degraded",
        "dependencies": {"mongodb": "up" if mongo_ok else "down"},
    }
