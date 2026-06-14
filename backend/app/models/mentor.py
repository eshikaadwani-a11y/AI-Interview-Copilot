"""AI Mentor domain models: resume feedback and learning roadmap."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ResumeFeedback(BaseModel):
    overall_summary: str
    strengths: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    provider: str


class RoadmapResource(BaseModel):
    title: str
    url: str


class RoadmapWeek(BaseModel):
    week: int
    focus: str
    skills: List[str] = Field(default_factory=list)
    resources: List[RoadmapResource] = Field(default_factory=list)


class Roadmap(BaseModel):
    id: str
    match_id: str
    job_title: Optional[str] = None
    target_fit_score: Optional[float] = None
    weeks: List[RoadmapWeek] = Field(default_factory=list)
    created_at: datetime


class RoadmapSummary(BaseModel):
    id: str
    match_id: str
    job_title: Optional[str] = None
    week_count: int
    created_at: datetime
