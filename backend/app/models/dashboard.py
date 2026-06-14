"""Analytics dashboard models."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Counts(BaseModel):
    resumes: int = 0
    jobs: int = 0
    matches: int = 0
    interviews: int = 0
    roadmaps: int = 0


class LatestMatch(BaseModel):
    id: str
    job_title: Optional[str] = None
    fit_score: float
    interview_probability: float
    recommendation: str


class TrendPoint(BaseModel):
    label: str
    value: float
    date: str


class SkillCount(BaseModel):
    skill: str
    count: int


class DashboardSummary(BaseModel):
    counts: Counts
    hiring_probability: Optional[float] = None        # 0–100 (latest match fit score)
    interview_readiness: Optional[float] = None       # 0–100 (latest interview overall)
    success_probability: Optional[float] = None       # 0–100 (latest interview success)
    latest_match: Optional[LatestMatch] = None
    skill_gap: Dict[str, int] = Field(default_factory=dict)   # required/preferred/strength counts
    top_missing_skills: List[SkillCount] = Field(default_factory=list)
    match_trend: List[TrendPoint] = Field(default_factory=list)
    interview_trend: List[TrendPoint] = Field(default_factory=list)
    category_scores: Dict[str, float] = Field(default_factory=dict)
    recommended_focus: List[str] = Field(default_factory=list)
