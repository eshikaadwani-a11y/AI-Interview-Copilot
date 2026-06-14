"""Resume persistence and orchestration service.

Coordinates PDF text extraction, deterministic parsing, and MongoDB storage.
Resumes are de-duplicated per user via a content hash so re-uploading the same
file returns the existing record instead of creating duplicates.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List

from bson import ObjectId

from app.core.errors import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.models.resume import ResumeDetail, ResumeProfile, ResumeSummary
from app.services.resume_parser import extract_text_from_pdf, parse_resume_text

logger = get_logger(__name__)

_COLLECTION = "resumes"


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def create_resume_from_pdf(
    user_id: str, filename: str, data: bytes
) -> ResumeDetail:
    """Parse a PDF resume and persist its structured profile."""
    text = extract_text_from_pdf(data)
    if not text or len(text.strip()) < 30:
        raise ValidationAppError(
            "Could not extract readable text from the PDF. "
            "Is it a scanned image rather than a text-based PDF?"
        )

    profile_dict = parse_resume_text(text)
    profile = ResumeProfile.model_validate(profile_dict)

    db = get_database()
    file_hash = _content_hash(data)

    existing = await db[_COLLECTION].find_one(
        {"user_id": user_id, "file_hash": file_hash}
    )
    if existing is not None:
        logger.info("Resume already exists for user %s (hash match)", user_id)
        return _to_detail(existing)

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "filename": filename,
        "file_hash": file_hash,
        "raw_text": text,
        "profile": profile.model_dump(),
        "created_at": now,
    }
    result = await db[_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Stored resume %s for user %s", result.inserted_id, user_id)
    return _to_detail(doc)


async def list_resumes(user_id: str) -> List[ResumeSummary]:
    """Return all resumes for a user, newest first."""
    db = get_database()
    cursor = db[_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    summaries: List[ResumeSummary] = []
    async for doc in cursor:
        profile = doc.get("profile", {})
        summaries.append(
            ResumeSummary(
                id=str(doc["_id"]),
                filename=doc["filename"],
                skill_count=len(profile.get("skills", [])),
                total_experience_months=profile.get("total_experience_months", 0),
                created_at=doc["created_at"],
            )
        )
    return summaries


async def get_resume(user_id: str, resume_id: str) -> ResumeDetail:
    """Return a single resume owned by the user."""
    doc = await _get_owned(user_id, resume_id)
    return _to_detail(doc)


async def delete_resume(user_id: str, resume_id: str) -> None:
    """Delete a resume owned by the user."""
    await _get_owned(user_id, resume_id)
    db = get_database()
    await db[_COLLECTION].delete_one({"_id": ObjectId(resume_id)})
    logger.info("Deleted resume %s for user %s", resume_id, user_id)


async def _get_owned(user_id: str, resume_id: str) -> dict:
    if not ObjectId.is_valid(resume_id):
        raise NotFoundError("Resume not found")
    db = get_database()
    doc = await db[_COLLECTION].find_one(
        {"_id": ObjectId(resume_id), "user_id": user_id}
    )
    if doc is None:
        raise NotFoundError("Resume not found")
    return doc


def _to_detail(doc: dict) -> ResumeDetail:
    return ResumeDetail(
        id=str(doc["_id"]),
        filename=doc["filename"],
        profile=ResumeProfile.model_validate(doc.get("profile", {})),
        created_at=doc["created_at"],
    )
