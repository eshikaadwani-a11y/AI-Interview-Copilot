"""Feature engineering for the Interview Success Predictor (Model 2).

Combines mock-interview performance with the candidate's resume-vs-job fit into
a numeric feature vector. As with Model 1, the same function is used for
training and inference. Pure standard library.

Inputs are 0–100 dimension averages plus a 0–1 completion ratio and a 0–1
resume_fit (from Model 1, or 0.5 when unavailable).
"""

from __future__ import annotations

from typing import Dict, List

INTERVIEW_FEATURE_NAMES: List[str] = [
    "avg_technical",
    "avg_communication",
    "avg_completeness",
    "avg_confidence",
    "avg_overall",
    "completion_ratio",
    "resume_fit",
]


def compute_interview_features(
    aggregate: Dict[str, float],
    completion_ratio: float,
    resume_fit: float,
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
        "resume_fit": round(max(0.0, min(1.0, resume_fit)), 4),
    }


def interview_features_to_vector(features: Dict[str, float]) -> List[float]:
    return [float(features.get(name, 0.0)) for name in INTERVIEW_FEATURE_NAMES]
