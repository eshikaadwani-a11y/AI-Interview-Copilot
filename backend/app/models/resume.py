"""Resume domain models.

These mirror the structured dict produced by ``resume_parser`` and define the
API/storage contract for a parsed resume profile.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    months: int = 0
    bullets: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[int] = None
    gpa: Optional[str] = None


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    tech: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    """Structured resume profile extracted from the uploaded document."""

    contact: Contact = Field(default_factory=Contact)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    total_experience_months: int = 0


class ResumeSummary(BaseModel):
    """Lightweight resume record for list views."""

    id: str
    filename: str
    skill_count: int
    total_experience_months: int
    created_at: datetime


class ResumeDetail(BaseModel):
    """Full resume record including the structured profile."""

    id: str
    filename: str
    profile: ResumeProfile
    created_at: datetime
