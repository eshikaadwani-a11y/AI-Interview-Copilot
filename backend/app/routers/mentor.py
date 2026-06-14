"""AI Mentor routes: resume feedback, learning roadmap, and grounded Q&A."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from app.core.deps import CurrentUser
from app.models.mentor import Roadmap, RoadmapSummary, ResumeFeedback
from app.models.rag import QueryRequest, QueryResponse
from app.services import mentor_service, rag_service

router = APIRouter(prefix="/mentor", tags=["mentor"])


@router.post("/resume-feedback/{resume_id}", response_model=ResumeFeedback)
async def resume_feedback(resume_id: str, current_user: CurrentUser) -> ResumeFeedback:
    """Generate strengths, missing sections, and improvement suggestions."""
    return await mentor_service.resume_feedback(current_user.id, resume_id)


@router.post("/roadmap/{match_id}", response_model=Roadmap, status_code=status.HTTP_201_CREATED)
async def generate_roadmap(match_id: str, current_user: CurrentUser) -> Roadmap:
    """Generate a weekly learning roadmap from a match's skill gaps."""
    return await mentor_service.generate_roadmap(current_user.id, match_id)


@router.get("/roadmaps", response_model=List[RoadmapSummary])
async def list_roadmaps(current_user: CurrentUser) -> List[RoadmapSummary]:
    """List the user's generated roadmaps."""
    return await mentor_service.list_roadmaps(current_user.id)


@router.get("/roadmap/{roadmap_id}", response_model=Roadmap)
async def get_roadmap(roadmap_id: str, current_user: CurrentUser) -> Roadmap:
    """Get a single roadmap."""
    return await mentor_service.get_roadmap(current_user.id, roadmap_id)


@router.post("/ask", response_model=QueryResponse)
async def ask(payload: QueryRequest, current_user: CurrentUser) -> QueryResponse:
    """Ask the AI mentor a question grounded in your indexed documents."""
    return await rag_service.query(
        current_user.id, payload.question, k=payload.k, source_types=payload.source_types
    )
