"""Tests for the ML pipeline: features, dataset, metrics, and training.

All pure-Python and runnable without scikit-learn/numpy, so the core ML logic
is verified in any environment.
"""

from __future__ import annotations

from app.ml import metrics as M
from app.ml.datagen import generate_dataset
from app.ml.features import FEATURE_NAMES, compute_features, compute_feature_vector
from app.ml.model import LogisticRegressionLite
from app.ml.train import _stratified_split

STRONG_RESUME = {
    "skills": ["Python", "FastAPI", "PyTorch", "scikit-learn", "Docker", "AWS", "SQL"],
    "total_experience_months": 72,
    "education": [{"degree": "M.Tech"}],
    "projects": [{"tech": ["Python", "PyTorch", "Docker"]}],
    "certifications": ["a", "b"],
}
WEAK_RESUME = {
    "skills": ["HTML", "CSS"],
    "total_experience_months": 6,
    "education": [{"degree": "Diploma"}],
    "projects": [],
    "certifications": [],
}
JOB = {
    "required_skills": ["Python", "FastAPI", "PyTorch", "SQL", "Machine Learning"],
    "preferred_skills": ["Docker", "AWS"],
    "technologies": ["Python", "FastAPI", "PyTorch", "SQL", "Machine Learning", "Docker", "AWS"],
    "min_experience_years": 5,
    "education_required": "Master's degree",
    "seniority": "Senior",
}


def test_features_complete_and_bounded() -> None:
    feats = compute_features(STRONG_RESUME, JOB)
    assert set(feats.keys()) == set(FEATURE_NAMES)
    for name in ["skill_overlap_ratio", "education_match", "project_relevance"]:
        assert 0.0 <= feats[name] <= 1.5


def test_strong_beats_weak_on_overlap() -> None:
    strong = compute_features(STRONG_RESUME, JOB)
    weak = compute_features(WEAK_RESUME, JOB)
    assert strong["weighted_skill_overlap"] > weak["weighted_skill_overlap"]
    assert strong["missing_required_ratio"] < weak["missing_required_ratio"]


def test_feature_vector_order() -> None:
    vec = compute_feature_vector(STRONG_RESUME, JOB)
    assert len(vec) == len(FEATURE_NAMES)


def test_dataset_shapes_and_balance() -> None:
    X, y, names = generate_dataset(n_samples=500, seed=7)
    assert len(X) == 500 and len(y) == 500
    assert names == FEATURE_NAMES
    assert 0 in y and 1 in y  # both classes present
    assert all(len(row) == len(FEATURE_NAMES) for row in X)


def test_metrics_known_values() -> None:
    y_true = [1, 1, 0, 0]
    y_score = [0.9, 0.4, 0.3, 0.1]
    res = M.evaluate(y_true, y_score)
    # threshold 0.5 -> preds [1,0,0,0]; tp=1, fn=1, tn=2
    assert res["accuracy"] == 0.75
    assert res["precision"] == 1.0
    assert res["recall"] == 0.5
    assert res["roc_auc"] >= 0.75


def test_model_learns_signal() -> None:
    X, y, names = generate_dataset(n_samples=1500, seed=3)
    X_tr, X_te, y_tr, y_te = _stratified_split(X, y, seed=3)
    model = LogisticRegressionLite(names).fit(X_tr, y_tr, lr=0.2, epochs=300)
    scores = [model.predict_proba(r) for r in X_te]
    res = M.evaluate(y_te, scores)
    # A learnable signal should yield clearly better-than-chance performance.
    assert res["roc_auc"] > 0.8, res
    assert res["accuracy"] > 0.75, res


def test_model_roundtrip(tmp_path) -> None:
    X, y, names = generate_dataset(n_samples=400, seed=1)
    model = LogisticRegressionLite(names).fit(X, y, epochs=100)
    path = str(tmp_path / "m.json")
    model.save(path)
    loaded = LogisticRegressionLite.load(path)
    row = X[0]
    assert abs(loaded.predict_proba(row) - model.predict_proba(row)) < 1e-9
