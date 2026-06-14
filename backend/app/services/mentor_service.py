"""AI Mentor service.

Three capabilities:
    1. resume_feedback  — strengths, missing sections, actionable suggestions.
    2. generate_roadmap — a weekly learning plan from a match's skill gaps.
    3. ask              — RAG-grounded Q&A (delegates to the RAG service).

All analysis is computed deterministically so the feature works fully offline;
when a real LLM provider is configured, the narrative summary is upgraded to a
generative one. This keeps the product demonstrable without keys while taking
advantage of OpenAI/Anthropic when available.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.models.mentor import (
    Roadmap,
    RoadmapResource,
    RoadmapSummary,
    RoadmapWeek,
    ResumeFeedback,
)
from app.services import match_service, resume_service
from app.services.llm.factory import get_llm_provider
from app.services import mentor_logic

logger = get_logger(__name__)

_ROADMAP_COLLECTION = "roadmaps"


def _resource_for(skill: str) -> RoadmapResource:
    title, url = mentor_logic.resource_for(skill)
    return RoadmapResource(title=title, url=url)


# ── Resume feedback ──────────────────────────────────────────────────────
async def resume_feedback(user_id: str, resume_id: str) -> ResumeFeedback:
    resume = await resume_service.get_resume(user_id, resume_id)
    profile = resume.profile.model_dump()
    strengths, missing, suggestions = mentor_logic.analyze_resume(profile)

    provider = get_llm_provider()
    overall = _feedback_summary(provider, profile, strengths, missing, suggestions)

    return ResumeFeedback(
        overall_summary=overall,
        strengths=strengths,
        missing_sections=missing,
        suggestions=suggestions,
        provider=provider.name,
    )


def _feedback_summary(provider, profile, strengths, missing, suggestions) -> str:
    """Generative summary when a real LLM is configured; template otherwise."""
    skill_count = len(profile.get("skills", []))
    months = profile.get("total_experience_months", 0) or 0

    if provider.name.startswith("local"):
        bits = [
            f"Your resume lists {skill_count} skills and about {round(months / 12, 1)} "
            "years of experience."
        ]
        if missing:
            bits.append("Consider adding: " + ", ".join(missing) + ".")
        if suggestions:
            bits.append("Top suggestion: " + suggestions[0])
        return " ".join(bits)

    system = (
        "You are an expert technical resume reviewer. Write a concise, encouraging "
        "2–3 sentence overall assessment. Be specific and constructive."
    )
    prompt = (
        f"Resume facts:\n- Skills: {skill_count}\n- Experience months: {months}\n"
        f"- Strengths: {strengths}\n- Missing sections: {missing}\n"
        f"- Suggestions: {suggestions}\n\nWrite the overall assessment."
    )
    try:
        return provider.generate(system, prompt, max_tokens=200).strip()
    except Exception as exc:  # pragma: no cover
        logger.warning("LLM feedback summary failed: %s", exc)
        return "Here is an assessment of your resume based on the detected sections."


# ── Learning roadmap ─────────────────────────────────────────────────────
async def generate_roadmap(user_id: str, match_id: str, weeks: int = 4) -> Roadmap:
    match = await match_service.get_match(user_id, match_id)
    gap = match.skill_gap

    # Required gaps first (highest priority), then preferred.
    ordered_skills = list(gap.missing_required) + [
        s for s in gap.missing_preferred if s not in gap.missing_required
    ]

    weekly = mentor_logic.distribute_into_weeks(ordered_skills, weeks)
    roadmap_weeks: List[RoadmapWeek] = []
    for i, skills in enumerate(weekly, start=1):
        if not skills:
            continue
        roadmap_weeks.append(
            RoadmapWeek(
                week=i,
                focus=mentor_logic.week_focus(skills),
                skills=skills,
                resources=[_resource_for(s) for s in skills],
            )
        )

    # If no gaps, provide a consolidation week.
    if not roadmap_weeks:
        roadmap_weeks.append(
            RoadmapWeek(
                week=1,
                focus="Polish and interview practice",
                skills=match.skill_gap.strengths[:4],
                resources=[_resource_for(s) for s in match.skill_gap.strengths[:4]],
            )
        )

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "match_id": match_id,
        "job_title": match.job_title,
        "target_fit_score": match.prediction.fit_score,
        "weeks": [w.model_dump() for w in roadmap_weeks],
        "created_at": now,
    }
    db = get_database()
    result = await db[_ROADMAP_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Generated roadmap %s for match %s", result.inserted_id, match_id)
    return _to_roadmap(doc)


async def list_roadmaps(user_id: str) -> List[RoadmapSummary]:
    db = get_database()
    cursor = db[_ROADMAP_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    out: List[RoadmapSummary] = []
    async for doc in cursor:
        out.append(
            RoadmapSummary(
                id=str(doc["_id"]),
                match_id=doc["match_id"],
                job_title=doc.get("job_title"),
                week_count=len(doc.get("weeks", [])),
                created_at=doc["created_at"],
            )
        )
    return out


async def get_roadmap(user_id: str, roadmap_id: str) -> Roadmap:
    if not ObjectId.is_valid(roadmap_id):
        raise NotFoundError("Roadmap not found")
    db = get_database()
    doc = await db[_ROADMAP_COLLECTION].find_one(
        {"_id": ObjectId(roadmap_id), "user_id": user_id}
    )
    if doc is None:
        raise NotFoundError("Roadmap not found")
    return _to_roadmap(doc)


def _to_roadmap(doc: dict) -> Roadmap:
    return Roadmap(
        id=str(doc["_id"]),
        match_id=doc["match_id"],
        job_title=doc.get("job_title"),
        target_fit_score=doc.get("target_fit_score"),
        weeks=[RoadmapWeek.model_validate(w) for w in doc.get("weeks", [])],
        created_at=doc["created_at"],
    )
