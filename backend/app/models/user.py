"""User domain models.

Separate schemas for input (registration/login), storage (with the password
hash), and public output (never exposes the hash). Token schemas describe the
auth response shape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)


class UserLogin(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    """User representation returned to clients (no secrets)."""

    id: str
    email: EmailStr
    full_name: str
    role: str = "user"
    created_at: datetime


class UserInDB(BaseModel):
    """Internal user record persisted to MongoDB."""

    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    full_name: str
    password_hash: str
    role: str = "user"
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None


class Token(BaseModel):
    """Auth response containing the access token and the user profile."""

    access_token: str
    token_type: str = "bearer"
    user: UserPublic
