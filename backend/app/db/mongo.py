"""Async MongoDB connection management.

A thin singleton wrapper around Motor's ``AsyncIOMotorClient``. The client is
created on application startup and closed on shutdown. Index creation is
centralised here so collections are correctly constrained from day one.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoManager:
    """Holds the process-wide Motor client and database handle."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongo = MongoManager()


async def connect_to_mongo() -> None:
    """Open the MongoDB connection and ensure indexes exist."""
    logger.info("Connecting to MongoDB at %s", settings.mongodb_uri)
    mongo.client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")
    mongo.db = mongo.client[settings.mongodb_db_name]
    await _ensure_indexes()
    logger.info("MongoDB connected (db=%s)", settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    """Close the MongoDB connection on shutdown."""
    if mongo.client is not None:
        mongo.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database, raising if not yet connected."""
    if mongo.db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return mongo.db


async def ping() -> bool:
    """Return True if the database responds to a ping."""
    if mongo.client is None:
        return False
    try:
        await mongo.client.admin.command("ping")
        return True
    except Exception as exc:  # pragma: no cover - network/db dependent
        logger.warning("MongoDB ping failed: %s", exc)
        return False


async def _ensure_indexes() -> None:
    """Create indexes for all collections (idempotent)."""
    db = get_database()

    await db["users"].create_indexes([
        IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
    ])
    await db["resumes"].create_indexes([
        IndexModel([("user_id", ASCENDING)], name="resumes_user"),
    ])
    await db["jobs"].create_indexes([
        IndexModel([("user_id", ASCENDING)], name="jobs_user"),
    ])
    await db["matches"].create_indexes([
        IndexModel([("user_id", ASCENDING)], name="matches_user"),
        IndexModel(
            [("resume_id", ASCENDING), ("job_id", ASCENDING)],
            name="matches_resume_job",
        ),
    ])
    await db["interviews"].create_indexes([
        IndexModel([("user_id", ASCENDING)], name="interviews_user"),
    ])
    await db["roadmaps"].create_indexes([
        IndexModel([("user_id", ASCENDING)], name="roadmaps_user"),
    ])
    logger.debug("MongoDB indexes ensured")
