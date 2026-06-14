"""Authentication service.

Encapsulates all user persistence and auth logic against MongoDB so routers
stay thin. Returns domain-friendly dicts / ``UserPublic`` models and raises
``AppError`` subclasses for expected failures.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from app.core.errors import ConflictError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongo import get_database
from app.models.user import Token, UserCreate, UserLogin, UserPublic

logger = get_logger(__name__)

_COLLECTION = "users"


def _to_public(doc: dict) -> UserPublic:
    """Map a Mongo user document to the public model."""
    return UserPublic(
        id=str(doc["_id"]),
        email=doc["email"],
        full_name=doc["full_name"],
        role=doc.get("role", "user"),
        created_at=doc["created_at"],
    )


async def register_user(payload: UserCreate) -> Token:
    """Create a new user and return an access token + public profile."""
    db = get_database()
    email = payload.email.lower().strip()

    existing = await db[_COLLECTION].find_one({"email": email})
    if existing is not None:
        raise ConflictError("An account with this email already exists.")

    now = datetime.now(timezone.utc)
    doc = {
        "email": email,
        "full_name": payload.full_name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "user",
        "created_at": now,
        "updated_at": now,
        "last_login": None,
    }
    result = await db[_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Registered user %s", email)

    user = _to_public(doc)
    token = create_access_token(user.id)
    return Token(access_token=token, user=user)


async def authenticate_user(payload: UserLogin) -> Token:
    """Validate credentials and return an access token + public profile."""
    db = get_database()
    email = payload.email.lower().strip()

    doc = await db[_COLLECTION].find_one({"email": email})
    if doc is None or not verify_password(payload.password, doc["password_hash"]):
        # Identical error for missing user and wrong password (no enumeration).
        raise UnauthorizedError("Invalid email or password.")

    await db[_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )
    logger.info("User %s logged in", email)

    user = _to_public(doc)
    token = create_access_token(user.id)
    return Token(access_token=token, user=user)


async def get_user_by_id(user_id: str) -> UserPublic | None:
    """Fetch a user's public profile by id, or None if not found."""
    if not ObjectId.is_valid(user_id):
        return None
    db = get_database()
    doc = await db[_COLLECTION].find_one({"_id": ObjectId(user_id)})
    return _to_public(doc) if doc else None
