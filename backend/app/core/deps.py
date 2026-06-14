"""Shared FastAPI dependencies.

``get_current_user`` extracts and validates the bearer token, loads the user,
and is reused by every protected route. ``CurrentUser`` is an annotated alias
for clean signatures: ``def route(user: CurrentUser): ...``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import UserPublic
from app.services.auth_service import get_user_by_id

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UserPublic:
    """Resolve the authenticated user from the Authorization header."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Not authenticated")

    payload = decode_access_token(credentials.credentials)
    user = await get_user_by_id(payload["sub"])
    if user is None:
        raise UnauthorizedError("User no longer exists")
    return user


CurrentUser = Annotated[UserPublic, Depends(get_current_user)]
