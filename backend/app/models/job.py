"""Job-description domain models.

Mirrors the structured dict produced by ``jd_parser`` and defines the
API/storage contract for a parsed job profile.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Payload for submitting a job description as text."""

    title: Optional[str] = Field(default=None, max_length=160)
    company: Optional[str] = Field(default=None, max_length=160)
    description: str = Field(min_length=30, max_length=30_000)


class JobProfile(BaseModel):
    """Structured job profile extracted from the description."""

    title: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    min_experience_years: Optional[int] = None
    education_required: Optional[str] = None
    seniority: Optional[str] = None


class JobSummary(BaseModel):
    """Lightweight job record for list views."""

    id: str
    title: Optional[str]
    company: Optional[str]
    required_skill_count: int
    created_at: datetime


class JobDetail(BaseModel):
    """Full job record including the structured profile."""

    id: str
    title: Optional[str]
    company: Optional[str]
    profile: JobProfile
    created_at: datetime
