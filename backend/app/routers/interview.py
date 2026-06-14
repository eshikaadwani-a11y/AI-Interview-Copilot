"""Interview simulator routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from app.core.deps import CurrentUser
from app.models.interview import (
    AnswerRequest,
    InterviewDetail,
    InterviewStart,
    InterviewState,
    InterviewSummary,
)
from app.services import interview_service

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start", response_model=InterviewState, status_code=status.HTTP_201_CREATED)
async def start(payload: InterviewStart, current_user: CurrentUser) -> InterviewState:
    """Start a new interview session and return the first question."""
    return await interview_service.start_interview(current_user.id, payload)


@router.post("/{interview_id}/answer", response_model=InterviewState)
async def answer(interview_id: str, payload: AnswerRequest, current_user: CurrentUser) -> InterviewState:
    """Submit an answer; returns the next question (or completion)."""
    return await interview_service.submit_answer(current_user.id, interview_id, payload.answer)


@router.post("/{interview_id}/finish", response_model=InterviewState)
async def finish(interview_id: str, current_user: CurrentUser) -> InterviewState:
    """End the interview early."""
    return await interview_service.finish_interview(current_user.id, interview_id)


@router.get("", response_model=List[InterviewSummary])
async def list_interviews(current_user: CurrentUser) -> List[InterviewSummary]:
    """List the user's interview sessions."""
    return await interview_service.list_interviews(current_user.id)


@router.get("/{interview_id}", response_model=InterviewDetail)
async def get_interview(interview_id: str, current_user: CurrentUser) -> InterviewDetail:
    """Get the full interview transcript."""
    return await interview_service.get_interview(current_user.id, interview_id)
