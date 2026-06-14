"""Tests for the deterministic job-description parser."""

from __future__ import annotations

from app.services.jd_parser import parse_job_text

SAMPLE = """Senior Machine Learning Engineer
Acme AI

Responsibilities
- Design and deploy machine learning models using Python and PyTorch
- Build scalable APIs with FastAPI and deploy on AWS with Docker
- Collaborate with data scientists on NLP and RAG pipelines

Required Qualifications
- 5+ years of experience in software engineering
- Strong proficiency in Python and SQL
- Bachelor's degree in Computer Science

Preferred / Nice to have
- Experience with Kubernetes and Kafka
- Familiarity with React and TypeScript is a plus
"""


def test_required_vs_preferred_skills() -> None:
    r = parse_job_text(SAMPLE)
    assert "Python" in r["required_skills"]
    assert "FastAPI" in r["required_skills"]
    assert "Kubernetes" in r["preferred_skills"]
    assert "React" in r["preferred_skills"]
    # No skill should appear in both buckets.
    assert not set(r["required_skills"]) & set(r["preferred_skills"])


def test_metadata_extraction() -> None:
    r = parse_job_text(SAMPLE)
    assert r["min_experience_years"] == 5
    assert r["education_required"] == "Bachelor's degree"
    assert r["seniority"] == "Senior"
    assert r["title"] == "Senior Machine Learning Engineer"


def test_responsibilities_are_bounded() -> None:
    r = parse_job_text(SAMPLE)
    # Exactly the 3 responsibility bullets — no bleed into qualifications.
    assert len(r["responsibilities"]) == 3
    assert all("years" not in x for x in r["responsibilities"])


def test_explicit_title_override() -> None:
    r = parse_job_text("We need a backend dev with Python and Django.", title="Backend Engineer")
    assert r["title"] == "Backend Engineer"
    assert "Python" in r["required_skills"]
    assert "Django" in r["required_skills"]


def test_empty_safe() -> None:
    r = parse_job_text("")
    assert r["required_skills"] == []
    assert r["min_experience_years"] is None
