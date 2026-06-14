"""Dashboard analytics aggregation service.

Builds a single summary from the user's stored resumes, jobs, matches,
interviews, and roadmaps — no recomputation, just aggregation of persisted
results — so the dashboard loads fast and reflects real activity.
"""

from __future__ import annotations

from collections import Counter
from typing import List, Optional

from app.core.logging import get_logger
from app.db.mongo import get_database
from app.models.dashboard import (
    Counts,
    DashboardSummary,
    LatestMatch,
    SkillCount,
    TrendPoint,
)

logger = get_logger(__name__)


def _short_date(dt) -> str:
    try:
        return dt.strftime("%b %d")
    except Exception:  # pragma: no cover
        return ""


async def get_summary(user_id: str) -> DashboardSummary:
    db = get_database()

    counts = Counts(
        resumes=await db["resumes"].count_documents({"user_id": user_id}),
        jobs=await db["jobs"].count_documents({"user_id": user_id}),
        matches=await db["matches"].count_documents({"user_id": user_id}),
        interviews=await db["interviews"].count_documents({"user_id": user_id}),
        roadmaps=await db["roadmaps"].count_documents({"user_id": user_id}),
    )

    # ── Matches (newest first) ──
    matches = await db["matches"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=50)

    latest_match: Optional[LatestMatch] = None
    hiring_probability: Optional[float] = None
    skill_gap: dict = {}
    top_missing: List[SkillCount] = []
    match_trend: List[TrendPoint] = []
    recommended_focus: List[str] = []

    if matches:
        newest = matches[0]
        pred = newest.get("prediction", {})
        latest_match = LatestMatch(
            id=str(newest["_id"]),
            job_title=newest.get("job_title"),
            fit_score=pred.get("fit_score", 0.0),
            interview_probability=pred.get("interview_probability", 0.0),
            recommendation=pred.get("recommendation", ""),
        )
        hiring_probability = pred.get("fit_score")

        gap = newest.get("skill_gap", {})
        skill_gap = {
            "missing_required": len(gap.get("missing_required", [])),
            "missing_preferred": len(gap.get("missing_preferred", [])),
            "strengths": len(gap.get("strengths", [])),
        }

        # Top missing skills across all matches (frequency).
        missing_counter: Counter = Counter()
        for m in matches:
            g = m.get("skill_gap", {})
            missing_counter.update(g.get("missing_required", []))
            missing_counter.update(g.get("missing_preferred", []))
        top_missing = [SkillCount(skill=s, count=c) for s, c in missing_counter.most_common(8)]
        recommended_focus = [s for s, _ in missing_counter.most_common(5)]

        # Trend (oldest -> newest) of fit scores.
        for m in reversed(matches[:10]):
            match_trend.append(
                TrendPoint(
                    label=(m.get("job_title") or "Match")[:18],
                    value=m.get("prediction", {}).get("fit_score", 0.0),
                    date=_short_date(m.get("created_at")),
                )
            )

    # ── Interviews with evaluations ──
    interviews = (
        await db["interviews"]
        .find({"user_id": user_id, "evaluation_aggregate": {"$ne": None}})
        .sort("created_at", -1)
        .to_list(length=50)
    )

    interview_readiness: Optional[float] = None
    success_probability: Optional[float] = None
    category_scores: dict = {}
    interview_trend: List[TrendPoint] = []

    if interviews:
        newest_iv = interviews[0]
        agg = newest_iv.get("evaluation_aggregate", {})
        interview_readiness = agg.get("overall")
        sp = newest_iv.get("success_probability")
        success_probability = round(sp * 100, 1) if sp is not None else None
        category_scores = newest_iv.get("category_scores", {})

        for iv in reversed(interviews[:10]):
            a = iv.get("evaluation_aggregate", {})
            interview_trend.append(
                TrendPoint(
                    label=iv.get("mode", "interview")[:18],
                    value=a.get("overall", 0.0),
                    date=_short_date(iv.get("created_at")),
                )
            )

    return DashboardSummary(
        counts=counts,
        hiring_probability=hiring_probability,
        interview_readiness=interview_readiness,
        success_probability=success_probability,
        latest_match=latest_match,
        skill_gap=skill_gap,
        top_missing_skills=top_missing,
        match_trend=match_trend,
        interview_trend=interview_trend,
        category_scores=category_scores,
        recommended_focus=recommended_focus,
    )
