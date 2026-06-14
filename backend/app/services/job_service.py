"""Job-description persistence and orchestration service."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId

from app.core.errors import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.models.job import JobDetail, JobProfile, JobSummary
from app.services.jd_parser import parse_job_text
from app.services.resume_parser import extract_text_from_pdf

logger = get_logger(__name__)

_COLLECTION = "jobs"


async def create_job_from_text(
    user_id: str,
    description: str,
    *,
    title: Optional[str] = None,
    company: Optional[str] = None,
) -> JobDetail:
    """Parse a job description and persist its structured profile."""
    profile_dict = parse_job_text(description, title=title)
    profile = JobProfile.model_validate(profile_dict)
    resolved_title = title or profile.title
    return await _persist(user_id, description, resolved_title, company, profile)


async def create_job_from_pdf(
    user_id: str, filename: str, data: bytes
) -> JobDetail:
    """Extract text from a JD PDF and persist its structured profile."""
    text = extract_text_from_pdf(data)
    if not text or len(text.strip()) < 30:
        raise ValidationAppError("Could not extract readable text from the PDF.")
    profile_dict = parse_job_text(text)
    profile = JobProfile.model_validate(profile_dict)
    return await _persist(user_id, text, profile.title or filename, None, profile)


async def _persist(
    user_id: str,
    raw_text: str,
    title: Optional[str],
    company: Optional[str],
    profile: JobProfile,
) -> JobDetail:
    db = get_database()
    file_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    existing = await db[_COLLECTION].find_one(
        {"user_id": user_id, "file_hash": file_hash}
    )
    if existing is not None:
        return _to_detail(existing)

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "title": title,
        "company": company,
        "file_hash": file_hash,
        "raw_text": raw_text,
        "profile": profile.model_dump(),
        "created_at": now,
    }
    result = await db[_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Stored job %s for user %s", result.inserted_id, user_id)
    return _to_detail(doc)


async def list_jobs(user_id: str) -> List[JobSummary]:
    db = get_database()
    cursor = db[_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    jobs: List[JobSummary] = []
    async for doc in cursor:
        profile = doc.get("profile", {})
        jobs.append(
            JobSummary(
                id=str(doc["_id"]),
                title=doc.get("title"),
                company=doc.get("company"),
                required_skill_count=len(profile.get("required_skills", [])),
                created_at=doc["created_at"],
            )
        )
    return jobs


async def get_job(user_id: str, job_id: str) -> JobDetail:
    doc = await _get_owned(user_id, job_id)
    return _to_detail(doc)


async def delete_job(user_id: str, job_id: str) -> None:
    await _get_owned(user_id, job_id)
    db = get_database()
    await db[_COLLECTION].delete_one({"_id": ObjectId(job_id)})
    logger.info("Deleted job %s for user %s", job_id, user_id)


async def _get_owned(user_id: str, job_id: str) -> dict:
    if not ObjectId.is_valid(job_id):
        raise NotFoundError("Job not found")
    db = get_database()
    doc = await db[_COLLECTION].find_one({"_id": ObjectId(job_id), "user_id": user_id})
    if doc is None:
        raise NotFoundError("Job not found")
    return doc


def _to_detail(doc: dict) -> JobDetail:
    return JobDetail(
        id=str(doc["_id"]),
        title=doc.get("title"),
        company=doc.get("company"),
        profile=JobProfile.model_validate(doc.get("profile", {})),
        created_at=doc["created_at"],
    )
