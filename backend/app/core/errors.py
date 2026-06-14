"""Application-wide error types and exception handlers.

Every error returned by the API uses a consistent envelope:

    {"error": "<code>", "detail": "<human readable>", "request_id": "<id>"}

This makes client-side handling predictable and aids debugging via the
correlation ``request_id`` that the middleware attaches to each request.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, handled application errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "app_error"

    def __init__(self, detail: str, *, error_code: str | None = None,
                 status_code: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"


class ValidationAppError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"


def _envelope(request: Request, error_code: str, detail: Any) -> dict[str, Any]:
    return {
        "error": error_code,
        "detail": detail,
        "request_id": getattr(request.state, "request_id", None),
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.info("AppError [%s]: %s", exc.error_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(request, exc.error_code, exc.detail),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(request: Request,
                                 exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(request, "http_error", exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request,
                                 exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(request, "validation_error", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(request, "internal_error",
                              "An unexpected error occurred."),
        )
