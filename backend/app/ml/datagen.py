"""Synthetic-but-grounded dataset generator for candidate-job fit.

Why synthetic? Real, labelled hiring-outcome data is proprietary and sensitive.
For a portfolio-grade ML system we generate realistic resume/JD pairs from the
shared skill taxonomy and role archetypes, then derive labels from a *latent
candidate quality* with controlled noise.

Crucially, features are computed by the SAME ``compute_features`` used at
inference, so the model learns the real feature→label relationship (signal +
noise) rather than memorising a closed-form rule. The README documents how to
swap in real labelled data later via the same interface.
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from app.ml.features import FEATURE_NAMES, compute_features, features_to_vector
from app.ml.taxonomy import SKILL_CATEGORIES

# Role archetypes: each maps to skill categories it draws core/optional skills from.
_ROLE_ARCHETYPES: Dict[str, Dict[str, List[str]]] = {
    "Software Engineer": {
        "core": ["languages", "cs_fundamentals", "backend"],
        "optional": ["databases", "cloud_devops", "tools"],
    },
    "Full Stack Developer": {
        "core": ["frontend", "backend", "languages"],
        "optional": ["databases", "cloud_devops", "tools"],
    },
    "AI Engineer": {
        "core": ["data_ml", "languages"],
        "optional": ["cloud_devops", "backend", "cs_fundamentals"],
    },
    "Data Scientist": {
        "core": ["data_ml", "languages"],
        "optional": ["databases", "cs_fundamentals", "tools"],
    },
}

_SENIORITIES = ["Junior", "Mid", "Senior", "Lead"]
_SENIORITY_YEARS = {"Junior": 1, "Mid": 3, "Senior": 5, "Lead": 7}
_EDUCATION_CHOICES = ["Bachelor's degree", "Master's degree", None]
_DEGREE_BY_LEVEL = {0: None, 1: "Diploma", 2: "B.Tech", 3: "M.Tech", 4: "PhD"}


def _skills_for_categories(categories: List[str]) -> List[str]:
    pool: List[str] = []
    for category in categories:
        pool.extend(SKILL_CATEGORIES.get(category, {}).keys())
    return pool


def _sample(rng: random.Random, items: List[str], k: int) -> List[str]:
    if k <= 0 or not items:
        return []
    k = min(k, len(items))
    return rng.sample(items, k)


def _make_job(rng: random.Random, archetype: str) -> Dict:
    spec = _ROLE_ARCHETYPES[archetype]
    core_pool = _skills_for_categories(spec["core"])
    opt_pool = _skills_for_categories(spec["optional"])

    required = _sample(rng, core_pool, rng.randint(4, 7))
    preferred = _sample(rng, [s for s in opt_pool if s not in required], rng.randint(2, 4))
    seniority = rng.choice(_SENIORITIES)
    return {
        "title": f"{seniority} {archetype}",
        "required_skills": required,
        "preferred_skills": preferred,
        "technologies": sorted(set(required) | set(preferred)),
        "min_experience_years": _SENIORITY_YEARS[seniority],
        "education_required": rng.choice(_EDUCATION_CHOICES),
        "seniority": seniority,
    }


def _make_resume(rng: random.Random, job: Dict, quality: float, archetype: str) -> Dict:
    """Generate a candidate resume whose strength scales with ``quality``."""
    required = job["required_skills"]
    preferred = job["preferred_skills"]

    # Candidate possesses a quality-scaled fraction of required skills.
    n_req = round(quality * len(required))
    have_required = _sample(rng, required, n_req)
    # Some preferred skills, fewer at low quality.
    have_preferred = _sample(rng, preferred, round(quality * len(preferred)))
    # Distractor skills from the broader archetype pool (noise / breadth).
    distractor_pool = _skills_for_categories(
        _ROLE_ARCHETYPES[archetype]["core"] + _ROLE_ARCHETYPES[archetype]["optional"]
    )
    distractors = _sample(rng, distractor_pool, rng.randint(2, 8))
    skills = sorted(set(have_required) | set(have_preferred) | set(distractors))

    # Experience scales with quality around the requirement.
    req_years = job["min_experience_years"]
    years = max(0.0, rng.gauss(req_years * (0.6 + quality), 1.2))
    months = int(years * 12)

    # Education scales with quality.
    req_level = {"Bachelor's degree": 2, "Master's degree": 3}.get(
        job["education_required"] or "", 2
    )
    cand_level = max(0, min(4, round(req_level - 1 + quality * 2 + rng.uniform(-0.5, 0.5))))
    education = [{"degree": _DEGREE_BY_LEVEL.get(cand_level)}] if cand_level else []

    # Projects with relevant tech (more relevant at higher quality).
    proj_tech = _sample(rng, sorted(set(required) | set(preferred)), round(quality * 4))
    projects = [{"tech": proj_tech}] if proj_tech else []

    certifications = ["cert"] * rng.randint(0, 3) if quality > 0.5 else []

    return {
        "skills": skills,
        "total_experience_months": months,
        "education": education,
        "projects": projects,
        "certifications": certifications,
    }


def _sigmoid(x: float) -> float:
    if x >= 0:
        import math
        return 1.0 / (1.0 + math.exp(-x))
    import math
    z = math.exp(x)
    return z / (1.0 + z)


def generate_dataset(
    n_samples: int = 4000, seed: int = 42
) -> Tuple[List[List[float]], List[int], List[str]]:
    """Generate (X, y, feature_names).

    ``X`` is a list of feature vectors (ordered by FEATURE_NAMES); ``y`` is the
    binary good-fit label. Labels come from a noisy function of latent quality
    and a few key features, so the relationship is learnable but not trivial.
    """
    rng = random.Random(seed)
    archetypes = list(_ROLE_ARCHETYPES.keys())

    X: List[List[float]] = []
    y: List[int] = []
    for _ in range(n_samples):
        archetype = rng.choice(archetypes)
        job = _make_job(rng, archetype)
        quality = rng.random()
        resume = _make_resume(rng, job, quality, archetype)

        feats = compute_features(resume, job)
        vec = features_to_vector(feats)

        # Latent fit score: weighted, interpretable combination + noise.
        logit = (
            3.2 * (feats["weighted_skill_overlap"] - 0.5)
            + 1.6 * (feats["experience_match"] - 0.7)
            + 1.1 * (feats["education_match"] - 0.6)
            + 1.0 * (feats["project_relevance"] - 0.3)
            - 1.4 * (feats["missing_required_ratio"] - 0.4)
            + 0.6 * (feats["preferred_skill_overlap"] - 0.3)
            + rng.gauss(0, 0.5)  # irreducible noise
        )
        prob = _sigmoid(2.5 * logit)
        label = 1 if rng.random() < prob else 0

        X.append(vec)
        y.append(label)

    return X, y, list(FEATURE_NAMES)
