"""Candidate-job matching engine.

Combines parsed resume + job profiles, the ML candidate-fit predictor, and a
deterministic skill-gap / recommendation analysis into a persisted match.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Tuple

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.ml.features import compute_features, features_to_vector
from app.ml.registry import get_predictor
from app.models.match import (
    Contribution,
    MatchDetail,
    MatchPrediction,
    MatchSummary,
    RecommendationItem,
    SkillGap,
)
from app.services import job_service, resume_service

logger = get_logger(__name__)

_COLLECTION = "matches"

# Human-friendly labels for model features (used in the explanation panel).
FEATURE_LABELS: Dict[str, str] = {
    "skill_overlap_ratio": "Required-skill coverage",
    "weighted_skill_overlap": "Weighted skill match",
    "preferred_skill_overlap": "Preferred-skill coverage",
    "missing_required_ratio": "Missing required skills",
    "experience_match": "Experience vs requirement",
    "education_match": "Education match",
    "project_relevance": "Project relevance",
    "certification_relevance": "Certifications",
    "seniority_gap": "Seniority alignment",
    "skill_breadth": "Overall skill breadth",
}


def _norm(items: List[str]) -> Dict[str, str]:
    """Map lowercased skill -> original display form."""
    return {s.strip().lower(): s for s in items if s and s.strip()}


def _analyze_skill_gap(resume_profile: Dict, job_profile: Dict) -> Tuple[SkillGap, List[RecommendationItem]]:
    resume_skills = _norm(resume_profile.get("skills", []))
    required = _norm(job_profile.get("required_skills", []))
    preferred = _norm(job_profile.get("preferred_skills", []))

    missing_required = [orig for key, orig in required.items() if key not in resume_skills]
    missing_preferred = [orig for key, orig in preferred.items() if key not in resume_skills]
    matched_required = [orig for key, orig in required.items() if key in resume_skills]
    matched_preferred = [orig for key, orig in preferred.items() if key in resume_skills]

    strengths = sorted(set(matched_required) | set(matched_preferred))
    weak_areas: List[str] = sorted(missing_required)

    # Derived (non-skill) signals enrich the analysis.
    if (resume_profile.get("total_experience_months") or 0) < (
        (job_profile.get("min_experience_years") or 0) * 12
    ):
        weak_areas.append("Years of experience")

    # Prioritised recommendations: required gaps first (High), then preferred (Medium).
    recommendations: List[RecommendationItem] = []
    for skill in sorted(missing_required):
        recommendations.append(
            RecommendationItem(
                skill=skill,
                priority="High",
                reason="Required by the job and missing from your resume.",
            )
        )
    for skill in sorted(missing_preferred):
        recommendations.append(
            RecommendationItem(
                skill=skill,
                priority="Medium",
                reason="Preferred skill that would strengthen your application.",
            )
        )

    gap = SkillGap(
        missing_required=sorted(missing_required),
        missing_preferred=sorted(missing_preferred),
        strengths=strengths,
        weak_areas=weak_areas,
    )
    return gap, recommendations


def _build_prediction(features: Dict[str, float]) -> MatchPrediction:
    vector = features_to_vector(features)
    result = get_predictor().predict(vector)
    explanation = [
        Contribution(
            feature=c["feature"],
            label=FEATURE_LABELS.get(c["feature"], c["feature"]),
            value=c["value"],
            contribution=c["contribution"],
        )
        for c in result.get("explanation", [])
    ]
    return MatchPrediction(
        fit_score=result["score"],
        interview_probability=result["probability"],
        recommendation=result["recommendation"],
        backend=result["backend"],
        explanation=explanation,
    )


async def create_match(user_id: str, resume_id: str, job_id: str) -> MatchDetail:
    """Compute and persist a resume-vs-job match."""
    resume = await resume_service.get_resume(user_id, resume_id)
    job = await job_service.get_job(user_id, job_id)

    resume_profile = resume.profile.model_dump()
    job_profile = job.profile.model_dump()

    features = compute_features(resume_profile, job_profile)
    prediction = _build_prediction(features)
    skill_gap, recommendations = _analyze_skill_gap(resume_profile, job_profile)

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "resume_id": resume_id,
        "job_id": job_id,
        "resume_filename": resume.filename,
        "job_title": job.title or job.profile.title,
        "features": features,
        "prediction": prediction.model_dump(),
        "skill_gap": skill_gap.model_dump(),
        "recommendations": [r.model_dump() for r in recommendations],
        "created_at": now,
    }
    db = get_database()
    result = await db[_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Created match %s (resume=%s job=%s)", result.inserted_id, resume_id, job_id)
    return _to_detail(doc)


async def list_matches(user_id: str) -> List[MatchSummary]:
    db = get_database()
    cursor = db[_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    out: List[MatchSummary] = []
    async for doc in cursor:
        out.append(
            MatchSummary(
                id=str(doc["_id"]),
                resume_filename=doc.get("resume_filename", "resume"),
                job_title=doc.get("job_title"),
                fit_score=doc["prediction"]["fit_score"],
                recommendation=doc["prediction"]["recommendation"],
                created_at=doc["created_at"],
            )
        )
    return out


async def get_match(user_id: str, match_id: str) -> MatchDetail:
    doc = await _get_owned(user_id, match_id)
    return _to_detail(doc)


async def delete_match(user_id: str, match_id: str) -> None:
    await _get_owned(user_id, match_id)
    db = get_database()
    await db[_COLLECTION].delete_one({"_id": ObjectId(match_id)})


async def _get_owned(user_id: str, match_id: str) -> dict:
    if not ObjectId.is_valid(match_id):
        raise NotFoundError("Match not found")
    db = get_database()
    doc = await db[_COLLECTION].find_one({"_id": ObjectId(match_id), "user_id": user_id})
    if doc is None:
        raise NotFoundError("Match not found")
    return doc


def _to_detail(doc: dict) -> MatchDetail:
    return MatchDetail(
        id=str(doc["_id"]),
        resume_id=doc["resume_id"],
        job_id=doc["job_id"],
        resume_filename=doc.get("resume_filename", "resume"),
        job_title=doc.get("job_title"),
        features=doc["features"],
        prediction=MatchPrediction.model_validate(doc["prediction"]),
        skill_gap=SkillGap.model_validate(doc["skill_gap"]),
        recommendations=[RecommendationItem.model_validate(r) for r in doc.get("recommendations", [])],
        created_at=doc["created_at"],
    )
