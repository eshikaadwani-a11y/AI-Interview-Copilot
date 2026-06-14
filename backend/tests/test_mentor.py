"""Tests for the pure mentor logic (resume analysis + roadmap construction)."""

from __future__ import annotations

from app.services import mentor_logic


def test_analyze_weak_resume_flags_missing_sections() -> None:
    profile = {
        "skills": ["Python", "SQL"],
        "experience": [{"bullets": []}],
        "projects": [],
        "education": [],
        "certifications": [],
        "summary": None,
        "contact": {"links": []},
        "total_experience_months": 6,
    }
    strengths, missing, suggestions = mentor_logic.analyze_resume(profile)
    assert "Professional summary" in missing
    assert "Projects" in missing
    assert "Certifications" in missing
    assert any("summary" in s.lower() for s in suggestions)


def test_analyze_strong_resume_surfaces_strengths() -> None:
    profile = {
        "skills": ["Python", "FastAPI", "Docker", "AWS", "SQL", "React", "PyTorch", "Kubernetes"],
        "experience": [{"bullets": ["Cut latency by 30%"]}],
        "projects": [{"tech": ["Python"]}, {"tech": ["React"]}],
        "education": [{"degree": "B.Tech"}],
        "certifications": ["AWS SA"],
        "summary": "Engineer",
        "contact": {"links": ["github.com/x"]},
        "total_experience_months": 48,
    }
    strengths, missing, suggestions = mentor_logic.analyze_resume(profile)
    assert any("Broad skill set" in s for s in strengths)
    assert any("years of experience" in s for s in strengths)
    assert "Projects" not in missing


def test_quantified_bullets_detected() -> None:
    assert mentor_logic.has_quantified_bullets([{"bullets": ["Improved speed by 40%"]}])
    assert not mentor_logic.has_quantified_bullets([{"bullets": ["Improved speed"]}])


def test_roadmap_distribution_balanced_and_ordered() -> None:
    skills = ["PyTorch", "TensorFlow", "Kubernetes", "Kafka", "Redis"]
    weeks = mentor_logic.distribute_into_weeks(skills, 4)
    assert len(weeks) == 4
    flat = [s for w in weeks for s in w]
    assert flat == skills  # order preserved, no loss/dup
    assert weeks[0][0] == "PyTorch"  # required gaps first


def test_resource_lookup_and_fallback() -> None:
    title, url = mentor_logic.resource_for("PyTorch")
    assert "pytorch.org" in url
    fallback_title, fallback_url = mentor_logic.resource_for("Obscure Skill")
    assert "search" in fallback_url


def test_week_focus_phrasing() -> None:
    assert mentor_logic.week_focus(["Docker"]) == "Master Docker"
    assert "and" in mentor_logic.week_focus(["Docker", "AWS"])
