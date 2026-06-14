"""Feature engineering for candidate-job fit.

This module is the single source of truth for turning a (resume_profile,
job_profile) pair into a numeric feature vector. The SAME function is used for
training and for inference, which eliminates train/serve skew.

It is intentionally dependency-free (pure standard library) so it runs in any
environment and is trivially unit-testable.

Inputs are plain dicts matching ``ResumeProfile`` / ``JobProfile`` (i.e. the
result of ``model_dump()``), so the ML layer stays decoupled from Pydantic.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

# Ordered feature names — the canonical column order for every model.
FEATURE_NAMES: List[str] = [
    "skill_overlap_ratio",
    "weighted_skill_overlap",
    "preferred_skill_overlap",
    "missing_required_ratio",
    "experience_match",
    "education_match",
    "project_relevance",
    "certification_relevance",
    "seniority_gap",
    "skill_breadth",
]

# Ordinal education levels.
_EDUCATION_LEVELS = {
    "none": 0,
    "diploma": 1,
    "bachelor": 2,
    "bachelor's degree": 2,
    "master": 3,
    "master's degree": 3,
    "phd": 4,
    "doctorate": 4,
    "degree": 2,
}

# Expected years of experience by seniority label.
_SENIORITY_YEARS = {
    "intern": 0,
    "entry": 1,
    "junior": 1,
    "mid": 3,
    "senior": 5,
    "lead": 7,
    "staff": 8,
    "principal": 10,
}


def _norm_set(items: Sequence[str]) -> set[str]:
    return {str(i).strip().lower() for i in items if str(i).strip()}


def _safe_ratio(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def _degree_level(degree: str | None) -> int:
    if not degree:
        return 0
    d = degree.strip().lower()
    for key, level in sorted(_EDUCATION_LEVELS.items(), key=lambda kv: -len(kv[0])):
        if key in d:
            return level
    return 0


def _resume_education_level(resume: Dict) -> int:
    levels = [_degree_level(e.get("degree")) for e in resume.get("education", [])]
    return max(levels) if levels else 0


def _candidate_years(resume: Dict) -> float:
    months = resume.get("total_experience_months") or 0
    return round(months / 12.0, 2)


def _resume_tech(resume: Dict) -> set[str]:
    """All technologies a candidate demonstrates: skills + project tech."""
    tech = _norm_set(resume.get("skills", []))
    for project in resume.get("projects", []):
        tech |= _norm_set(project.get("tech", []))
    return tech


def compute_features(resume: Dict, job: Dict) -> Dict[str, float]:
    """Compute the full feature dict for a (resume, job) pair."""
    resume_skills = _norm_set(resume.get("skills", []))
    resume_tech = _resume_tech(resume)
    required = _norm_set(job.get("required_skills", []))
    preferred = _norm_set(job.get("preferred_skills", []))
    technologies = _norm_set(job.get("technologies", [])) or (required | preferred)

    # 1. Skill overlap with required skills.
    matched_required = resume_skills & required
    skill_overlap_ratio = _safe_ratio(len(matched_required), len(required), default=1.0)

    # 2. Weighted overlap (required weight 1.0, preferred 0.5).
    weight_total = len(required) * 1.0 + len(preferred) * 0.5
    weight_have = len(matched_required) * 1.0 + len(resume_skills & preferred) * 0.5
    weighted_skill_overlap = _safe_ratio(weight_have, weight_total, default=1.0)

    # 3. Preferred overlap.
    preferred_skill_overlap = _safe_ratio(
        len(resume_skills & preferred), len(preferred), default=0.0
    )

    # 4. Missing required ratio (lower is better).
    missing_required_ratio = _safe_ratio(
        len(required - resume_skills), len(required), default=0.0
    )

    # 5. Experience match vs requirement (capped at 1.5).
    required_years = job.get("min_experience_years")
    if required_years is None:
        seniority = (job.get("seniority") or "").strip().lower()
        required_years = _SENIORITY_YEARS.get(seniority, 2)
    cand_years = _candidate_years(resume)
    experience_match = min(_safe_ratio(cand_years, max(required_years, 1), default=1.0), 1.5)

    # 6. Education match (ordinal, partial credit when below requirement).
    req_level = _degree_level(job.get("education_required"))
    cand_level = _resume_education_level(resume)
    if req_level == 0:
        education_match = 1.0
    elif cand_level >= req_level:
        education_match = 1.0
    else:
        education_match = max(0.0, 1.0 - (req_level - cand_level) * 0.34)

    # 7. Project relevance: project tech overlap with job technologies.
    project_relevance = _safe_ratio(
        len(resume_tech & technologies), len(technologies), default=0.0
    )

    # 8. Certification relevance: presence/volume of certifications (capped).
    cert_count = len(resume.get("certifications", []))
    certification_relevance = min(cert_count / 3.0, 1.0)

    # 9. Seniority gap: candidate years vs expected for the role's seniority.
    seniority = (job.get("seniority") or "").strip().lower()
    expected_years = _SENIORITY_YEARS.get(seniority, max(required_years, 1))
    seniority_gap = min(_safe_ratio(cand_years, max(expected_years, 1), default=1.0), 1.5)

    # 10. Skill breadth (normalised; signals overall preparedness).
    skill_breadth = min(len(resume_skills) / 20.0, 1.0)

    return {
        "skill_overlap_ratio": round(skill_overlap_ratio, 4),
        "weighted_skill_overlap": round(weighted_skill_overlap, 4),
        "preferred_skill_overlap": round(preferred_skill_overlap, 4),
        "missing_required_ratio": round(missing_required_ratio, 4),
        "experience_match": round(experience_match, 4),
        "education_match": round(education_match, 4),
        "project_relevance": round(project_relevance, 4),
        "certification_relevance": round(certification_relevance, 4),
        "seniority_gap": round(seniority_gap, 4),
        "skill_breadth": round(skill_breadth, 4),
    }


def features_to_vector(features: Dict[str, float]) -> List[float]:
    """Convert a feature dict to an ordered vector using FEATURE_NAMES."""
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]


def compute_feature_vector(resume: Dict, job: Dict) -> List[float]:
    """Convenience: compute features and return the ordered vector."""
    return features_to_vector(compute_features(resume, job))
