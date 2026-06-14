"""Authentication routes: register, login, and current-user profile."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser
from app.models.user import Token, UserCreate, UserLogin, UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate) -> Token:
    """Create a new account and return an access token."""
    return await auth_service.register_user(payload)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin) -> Token:
    """Authenticate with email + password and return an access token."""
    return await auth_service.authenticate_user(payload)


@router.get("/me", response_model=UserPublic)
async def me(current_user: CurrentUser) -> UserPublic:
    """Return the authenticated user's profile."""
    return current_user
