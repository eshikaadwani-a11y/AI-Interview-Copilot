"""Tests for the interview question bank and selection/follow-up logic."""

from __future__ import annotations

from app.services import interview_bank


def test_resolve_categories_defaults_by_mode() -> None:
    cats = interview_bank.resolve_categories("ai_engineer", None)
    assert "ML" in cats
    # Explicit valid categories are respected.
    assert interview_bank.resolve_categories("software_engineer", ["DSA"]) == ["DSA"]
    # Invalid categories fall back to the mode default.
    assert "DSA" in interview_bank.resolve_categories("software_engineer", ["Nonsense"])


def test_select_questions_count_and_shape() -> None:
    qs = interview_bank.select_questions("software_engineer", count=6, seed=1)
    assert len(qs) == 6
    for q in qs:
        assert set(q.keys()) == {"category", "difficulty", "text"}
        assert q["category"] in interview_bank.QUESTION_BANK


def test_select_questions_is_deterministic_with_seed() -> None:
    a = interview_bank.select_questions("ai_engineer", count=5, seed=42)
    b = interview_bank.select_questions("ai_engineer", count=5, seed=42)
    assert a == b


def test_projects_question_personalized() -> None:
    qs = interview_bank.select_questions(
        "software_engineer", categories=["Projects"], count=2, seed=3,
        project_names=["AI Interview Copilot"],
    )
    assert any("AI Interview Copilot" in q["text"] for q in qs)


def test_followup_requires_substantive_answer() -> None:
    assert interview_bank.deterministic_followup("DSA", "idk") is None
    fu = interview_bank.deterministic_followup(
        "DSA", "I would use a hash map to store counts and then sort by frequency.", seed=1
    )
    assert isinstance(fu, str) and len(fu) > 0
