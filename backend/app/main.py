"""FastAPI application factory.

Wires together configuration, logging, middleware, exception handlers,
database lifecycle, and routers. Import ``app`` for ASGI servers, or call
``create_app`` for testing with isolated instances.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.routers import auth, health, jobs, resumes

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown side effects (DB connections, etc.)."""
    configure_logging()
    logger.info("Starting %s v%s (%s)", settings.app_name, __version__,
                settings.environment)
    try:
        await connect_to_mongo()
    except Exception as exc:  # pragma: no cover - allows boot without DB locally
        logger.warning("Could not connect to MongoDB on startup: %s", exc)
    yield
    await close_mongo_connection()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Build and configure a FastAPI application instance."""
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI Interview Copilot — resume analysis, ML candidate fit, "
                    "RAG mentor, and AI interview simulation.",
        docs_url="/docs",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # Middleware (order matters: CORS outermost).
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Routers.
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(resumes.router, prefix=settings.api_v1_prefix)
    app.include_router(jobs.router, prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
        }

    return app


app = create_app()
