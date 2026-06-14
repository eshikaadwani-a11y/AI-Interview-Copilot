"""Interview simulator domain models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InterviewStart(BaseModel):
    mode: str = Field(default="software_engineer")
    categories: Optional[List[str]] = None
    num_questions: int = Field(default=6, ge=3, le=15)
    resume_id: Optional[str] = None
    job_id: Optional[str] = None
    # Extensibility: "technical" today; "coding" / "voice" / "company" planned.
    interview_type: str = Field(default="technical")
    company: Optional[str] = Field(default=None, max_length=120)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=8000)


class QuestionPublic(BaseModel):
    index: int
    category: str
    difficulty: Optional[str] = None
    text: str
    type: str  # "base" | "followup"


class QuestionFull(QuestionPublic):
    answer: Optional[str] = None


class InterviewState(BaseModel):
    """The client-facing view while taking an interview."""

    id: str
    mode: str
    mode_label: str
    status: str  # "active" | "completed"
    total: int
    answered: int
    current_index: int
    current_question: Optional[QuestionPublic] = None
    finished: bool = False


class InterviewSummary(BaseModel):
    id: str
    mode: str
    mode_label: str
    status: str
    total: int
    answered: int
    created_at: datetime


class InterviewDetail(BaseModel):
    id: str
    mode: str
    mode_label: str
    status: str
    questions: List[QuestionFull] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
