"""Interview evaluation / performance report models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    technical: float
    communication: float
    completeness: float
    confidence: float
    score: float
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class EvaluatedQuestion(BaseModel):
    index: int
    category: str
    type: str
    question: str
    answer: Optional[str] = None
    evaluation: Optional[AnswerEvaluation] = None


class AggregateScores(BaseModel):
    technical: float
    communication: float
    completeness: float
    confidence: float
    overall: float


class InterviewReport(BaseModel):
    interview_id: str
    mode_label: str
    status: str
    answered: int
    total: int
    aggregate: AggregateScores
    success_probability: float
    success_label: str
    model_backend: str
    per_question: List[EvaluatedQuestion] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime
