"""Tests for the deterministic resume parser.

These exercise the pure-Python parsing logic (no PDF library or DB needed),
covering skill extraction, experience parsing with duration computation,
education, projects, and certifications.
"""

from __future__ import annotations

from app.services.resume_parser import parse_resume_text

SAMPLE = """Ada Lovelace
ada.lovelace@example.com | +1 415-555-0199 | github.com/ada

TECHNICAL SKILLS
Python, FastAPI, React, PyTorch, scikit-learn, XGBoost, Docker, MongoDB

WORK EXPERIENCE
Senior Software Engineer at Acme Corp
Jan 2021 - Dec 2022
- Built a recommendation service in Python and FastAPI
- Led migration to Kubernetes on AWS

Software Engineer, Globex
Jun 2018 - Dec 2020
- Developed REST APIs with Django and PostgreSQL

PROJECTS
AI Interview Copilot - ML-powered interview prep
- Built candidate-fit predictor with XGBoost

EDUCATION
B.Tech in Computer Science
Stanford University, 2018
CGPA: 8.9/10

CERTIFICATIONS
- AWS Certified Solutions Architect
- Deep Learning Specialization
"""


def test_contact_extraction() -> None:
    result = parse_resume_text(SAMPLE)
    assert result["contact"]["email"] == "ada.lovelace@example.com"
    assert result["contact"]["name"] == "Ada Lovelace"
    assert any("github" in link for link in result["contact"]["links"])


def test_skill_extraction() -> None:
    skills = parse_resume_text(SAMPLE)["skills"]
    for expected in ["Python", "FastAPI", "React", "PyTorch", "scikit-learn", "XGBoost"]:
        assert expected in skills


def test_experience_parsing_and_duration() -> None:
    result = parse_resume_text(SAMPLE)
    exp = result["experience"]
    assert len(exp) == 2
    assert exp[0]["title"] == "Senior Software Engineer"
    assert exp[0]["company"] == "Acme Corp"
    assert exp[0]["months"] == 23  # Jan 2021 -> Dec 2022
    assert exp[1]["company"] == "Globex"
    # Date-range line must not leak into bullets.
    assert all("2021" not in b for b in exp[0]["bullets"])
    assert result["total_experience_months"] == 23 + 30


def test_education_and_certifications() -> None:
    result = parse_resume_text(SAMPLE)
    assert result["education"][0]["year"] == 2018
    assert result["education"][0]["gpa"] == "8.9"
    assert len(result["certifications"]) == 2


def test_empty_input_is_safe() -> None:
    result = parse_resume_text("")
    assert result["skills"] == []
    assert result["experience"] == []
    assert result["total_experience_months"] == 0
