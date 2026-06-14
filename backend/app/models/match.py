"""Candidate-job match domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MatchCreate(BaseModel):
    """Request to match a resume against a job."""

    resume_id: str
    job_id: str


class Contribution(BaseModel):
    feature: str
    label: str
    value: float
    contribution: float


class MatchPrediction(BaseModel):
    fit_score: float
    interview_probability: float
    recommendation: str
    backend: str
    explanation: List[Contribution] = Field(default_factory=list)


class SkillGap(BaseModel):
    missing_required: List[str] = Field(default_factory=list)
    missing_preferred: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    skill: str
    priority: str  # "High" | "Medium"
    reason: str


class MatchSummary(BaseModel):
    id: str
    resume_filename: str
    job_title: Optional[str]
    fit_score: float
    recommendation: str
    created_at: datetime


class MatchDetail(BaseModel):
    id: str
    resume_id: str
    job_id: str
    resume_filename: str
    job_title: Optional[str]
    features: Dict[str, float]
    prediction: MatchPrediction
    skill_gap: SkillGap
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    created_at: datetime
