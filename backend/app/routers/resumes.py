"""Resume upload and retrieval routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, Response, UploadFile, status

from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.errors import ValidationAppError
from app.models.resume import ResumeDetail, ResumeSummary
from app.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ResumeDetail:
    """Upload a PDF resume; returns the parsed structured profile."""
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise ValidationAppError("Only PDF files are supported.")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) == 0:
        raise ValidationAppError("Uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"File exceeds the {settings.max_upload_mb}MB limit."
        )

    return await resume_service.create_resume_from_pdf(
        current_user.id, file.filename or "resume.pdf", data
    )


@router.get("", response_model=List[ResumeSummary])
async def list_resumes(current_user: CurrentUser) -> List[ResumeSummary]:
    """List the current user's uploaded resumes."""
    return await resume_service.list_resumes(current_user.id)


@router.get("/{resume_id}", response_model=ResumeDetail)
async def get_resume(resume_id: str, current_user: CurrentUser) -> ResumeDetail:
    """Get a single resume's full structured profile."""
    return await resume_service.get_resume(current_user.id, resume_id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: str, current_user: CurrentUser) -> Response:
    """Delete a resume."""
    await resume_service.delete_resume(current_user.id, resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
