"""Feature engineering for the Interview Success Predictor (Model 2).

Per the product spec, Model 2 combines THREE signal groups:
    1. Interview scores  — avg technical/communication/completeness/confidence/overall
    2. Match score       — the candidate's resume-vs-job fit (Model 1 output)
    3. Resume features   — experience and skill breadth

The same function is used for training and inference (no train/serve skew).
Pure standard library.
"""

from __future__ import annotations

from typing import Dict, List

INTERVIEW_FEATURE_NAMES: List[str] = [
    # Interview scores
    "avg_technical",
    "avg_communication",
    "avg_completeness",
    "avg_confidence",
    "avg_overall",
    "completion_ratio",
    # Match score (Model 1)
    "match_score",
    # Resume features
    "resume_experience",
    "resume_skill_breadth",
]

# Human-readable labels for the "why this prediction" explanation.
INTERVIEW_FEATURE_LABELS: Dict[str, str] = {
    "avg_technical": "Avg technical accuracy",
    "avg_communication": "Avg communication",
    "avg_completeness": "Avg completeness",
    "avg_confidence": "Avg confidence",
    "avg_overall": "Avg overall answer score",
    "completion_ratio": "Interview completion",
    "match_score": "Resume–job match score",
    "resume_experience": "Years of experience",
    "resume_skill_breadth": "Resume skill breadth",
}


def compute_interview_features(
    aggregate: Dict[str, float],
    completion_ratio: float,
    match_score: float,
    resume_experience_months: float = 0.0,
    resume_skill_count: int = 0,
) -> Dict[str, float]:
    """Build the Model-2 feature dict (all features normalised to 0–1)."""
    def n(key: str) -> float:
        return max(0.0, min(1.0, float(aggregate.get(key, 0.0)) / 100.0))

    return {
        "avg_technical": round(n("technical"), 4),
        "avg_communication": round(n("communication"), 4),
        "avg_completeness": round(n("completeness"), 4),
        "avg_confidence": round(n("confidence"), 4),
        "avg_overall": round(n("overall"), 4),
        "completion_ratio": round(max(0.0, min(1.0, completion_ratio)), 4),
        "match_score": round(max(0.0, min(1.0, match_score)), 4),
        "resume_experience": round(min(resume_experience_months / 120.0, 1.0), 4),  # cap 10y
        "resume_skill_breadth": round(min(resume_skill_count / 20.0, 1.0), 4),
    }


def interview_features_to_vector(features: Dict[str, float]) -> List[float]:
    return [float(features.get(name, 0.0)) for name in INTERVIEW_FEATURE_NAMES]
