"""Candidate-job match routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from app.core.deps import CurrentUser
from app.models.match import MatchCreate, MatchDetail, MatchSummary
from app.services import match_service

router = APIRouter(prefix="/match", tags=["match"])


@router.post("", response_model=MatchDetail, status_code=status.HTTP_201_CREATED)
async def create_match(payload: MatchCreate, current_user: CurrentUser) -> MatchDetail:
    """Match a resume against a job and return ML score + skill gap."""
    return await match_service.create_match(
        current_user.id, payload.resume_id, payload.job_id
    )


@router.get("", response_model=List[MatchSummary])
async def list_matches(current_user: CurrentUser) -> List[MatchSummary]:
    """List the user's match history."""
    return await match_service.list_matches(current_user.id)


@router.get("/{match_id}", response_model=MatchDetail)
async def get_match(match_id: str, current_user: CurrentUser) -> MatchDetail:
    """Get a single match's full result."""
    return await match_service.get_match(current_user.id, match_id)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(match_id: str, current_user: CurrentUser) -> None:
    """Delete a match."""
    await match_service.delete_match(current_user.id, match_id)
