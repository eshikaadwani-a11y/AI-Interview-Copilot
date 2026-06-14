"""Tests for interview-answer evaluation and Model-2 features."""

from __future__ import annotations

from app.ml.interview_datagen import generate_interview_dataset
from app.ml.interview_features import (
    INTERVIEW_FEATURE_NAMES,
    compute_interview_features,
    interview_features_to_vector,
)
from app.ml.metrics import evaluate as eval_metrics
from app.ml.model import LogisticRegressionLite
from app.services.evaluation_logic import evaluate_answer


def test_strong_answer_scores_higher_than_weak() -> None:
    strong = evaluate_answer(
        "DSA",
        "How does a hash map work?",
        "A hash map stores key-value pairs using a hash function to compute an "
        "index into an array of buckets. Collisions are handled with chaining or "
        "open addressing. Average time complexity for lookup is O(1), worst case O(n). "
        "For example, Python dicts use open addressing.",
    )
    weak = evaluate_answer("DSA", "How does a hash map work?", "maybe it stores stuff, i think")
    assert strong["score"] > weak["score"]
    assert strong["technical"] > weak["technical"]
    assert weak["confidence"] < strong["confidence"]  # hedging penalised


def test_evaluation_dimensions_bounded() -> None:
    ev = evaluate_answer("ML", "Explain overfitting", "Overfitting is when a model memorizes training data.")
    for key in ["technical", "communication", "completeness", "confidence", "score"]:
        assert 0.0 <= ev[key] <= 100.0


def test_interview_features_shape_and_norm() -> None:
    agg = {"technical": 80, "communication": 70, "completeness": 75, "confidence": 65, "overall": 74}
    feats = compute_interview_features(
        agg, completion_ratio=0.9, match_score=0.8,
        resume_experience_months=48, resume_skill_count=10,
    )
    assert set(feats.keys()) == set(INTERVIEW_FEATURE_NAMES)
    assert feats["avg_technical"] == 0.8
    assert feats["match_score"] == 0.8
    assert feats["resume_skill_breadth"] == 0.5
    assert all(0.0 <= v <= 1.0 for v in interview_features_to_vector(feats))


def test_answer_has_per_dimension_explanations() -> None:
    ev = evaluate_answer(
        "CN",
        "Explain TCP",
        "TCP uses a three-way handshake to establish a connection. It is reliable "
        "and ordered. The protocol guarantees delivery using acknowledgements.",
    )
    assert "technical" in ev["explanations"]
    # Mentions are surfaced; missed concepts are listed too.
    assert any("Mentioned" in r for r in ev["explanations"]["technical"])
    assert isinstance(ev["missed_concepts"], list)


def test_interview_success_model_learns_signal() -> None:
    X, y, names = generate_interview_dataset(n_samples=1500, seed=5)
    split = int(len(X) * 0.8)
    model = LogisticRegressionLite(names).fit(X[:split], y[:split], lr=0.2, epochs=300)
    scores = [model.predict_proba(r) for r in X[split:]]
    res = eval_metrics(y[split:], scores)
    assert res["roc_auc"] > 0.8, res
