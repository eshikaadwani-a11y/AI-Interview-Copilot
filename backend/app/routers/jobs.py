"""Job-description submission and retrieval routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.errors import ValidationAppError
from app.models.job import JobCreate, JobDetail, JobSummary
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, current_user: CurrentUser) -> JobDetail:
    """Submit a job description as text; returns the parsed job profile."""
    return await job_service.create_job_from_text(
        current_user.id,
        payload.description,
        title=payload.title,
        company=payload.company,
    )


@router.post("/upload", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
async def upload_job(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> JobDetail:
    """Upload a job description as a PDF."""
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise ValidationAppError("Only PDF files are supported.")
    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) == 0:
        raise ValidationAppError("Uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValidationAppError(f"File exceeds the {settings.max_upload_mb}MB limit.")
    return await job_service.create_job_from_pdf(
        current_user.id, file.filename or "job.pdf", data
    )


@router.get("", response_model=List[JobSummary])
async def list_jobs(current_user: CurrentUser) -> List[JobSummary]:
    """List the current user's submitted job descriptions."""
    return await job_service.list_jobs(current_user.id)


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, current_user: CurrentUser) -> JobDetail:
    """Get a single job's full structured profile."""
    return await job_service.get_job(current_user.id, job_id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, current_user: CurrentUser) -> None:
    """Delete a job description."""
    await job_service.delete_job(current_user.id, job_id)
