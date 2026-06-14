"""Synthetic dataset generator for the Interview Success Predictor (Model 2).

A latent candidate ability drives both the simulated interview scores and the
success label (with controlled noise), so the model learns a realistic,
non-trivial mapping from performance features to interview success.
"""

from __future__ import annotations

import math
import random
from typing import List, Tuple

from app.ml.interview_features import (
    INTERVIEW_FEATURE_NAMES,
    compute_interview_features,
    interview_features_to_vector,
)


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def generate_interview_dataset(
    n_samples: int = 3000, seed: int = 123
) -> Tuple[List[List[float]], List[int], List[str]]:
    rng = random.Random(seed)
    X: List[List[float]] = []
    y: List[int] = []

    for _ in range(n_samples):
        ability = rng.random()  # latent candidate ability

        def score_around(center: float, spread: float = 14.0) -> float:
            return max(0.0, min(100.0, rng.gauss(center * 100, spread)))

        technical = score_around(ability)
        communication = score_around(_clamp01(ability + rng.uniform(-0.15, 0.15)))
        completeness = score_around(_clamp01(ability + rng.uniform(-0.1, 0.1)))
        confidence = score_around(_clamp01(ability + rng.uniform(-0.2, 0.2)))
        overall = 0.4 * technical + 0.2 * communication + 0.25 * completeness + 0.15 * confidence

        completion_ratio = _clamp01(rng.gauss(0.6 + 0.4 * ability, 0.15))
        match_score = _clamp01(rng.gauss(ability, 0.18))
        resume_experience_months = max(0.0, rng.gauss(ability * 90, 18))  # up to ~10y
        resume_skill_count = max(0, int(rng.gauss(ability * 18 + 4, 4)))

        aggregate = {
            "technical": technical,
            "communication": communication,
            "completeness": completeness,
            "confidence": confidence,
            "overall": overall,
        }
        feats = compute_interview_features(
            aggregate, completion_ratio, match_score,
            resume_experience_months, resume_skill_count,
        )
        vec = interview_features_to_vector(feats)

        logit = (
            2.4 * (feats["avg_overall"] - 0.55)
            + 1.2 * (feats["avg_technical"] - 0.55)
            + 1.0 * (feats["match_score"] - 0.5)
            + 0.5 * (feats["completion_ratio"] - 0.6)
            + 0.4 * (feats["resume_experience"] - 0.4)
            + rng.gauss(0, 0.45)
        )
        prob = _sigmoid(3.0 * logit)
        label = 1 if rng.random() < prob else 0

        X.append(vec)
        y.append(label)

    return X, y, list(INTERVIEW_FEATURE_NAMES)
