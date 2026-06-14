"""Training orchestrator for the candidate-fit predictor.

Run with:  ``python -m app.ml.train``

Tries the production scikit-learn/XGBoost trainer first; if those libraries are
not installed, it transparently falls back to the dependency-free pure-Python
logistic regression so the pipeline produces a trained model and real metrics
in ANY environment. Both paths write a consistent ``metadata.json``.
"""

from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Sequence, Tuple

from app.ml import metrics as M
from app.ml.datagen import generate_dataset
from app.ml.model import LogisticRegressionLite

logger = logging.getLogger("app.ml.train")

# Default model output directory (overridable via env or function arg).
DEFAULT_MODELS_DIR = os.environ.get("MODELS_DIR", "./models")


def _stratified_split(
    X: Sequence[Sequence[float]],
    y: Sequence[int],
    test_size: float = 0.2,
    seed: int = 42,
) -> Tuple[List, List, List, List]:
    """Stratified train/test split (pure Python)."""
    rng = random.Random(seed)
    idx_pos = [i for i, label in enumerate(y) if label == 1]
    idx_neg = [i for i, label in enumerate(y) if label == 0]
    rng.shuffle(idx_pos)
    rng.shuffle(idx_neg)

    def cut(indices: List[int]) -> Tuple[List[int], List[int]]:
        k = int(len(indices) * test_size)
        return indices[k:], indices[:k]

    train_pos, test_pos = cut(idx_pos)
    train_neg, test_neg = cut(idx_neg)
    train_idx = train_pos + train_neg
    test_idx = test_pos + test_neg
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    return X_train, X_test, y_train, y_test


def _train_pure_python(
    X: Sequence[Sequence[float]],
    y: Sequence[int],
    feature_names: List[str],
    models_dir: str,
) -> Dict[str, object]:
    """Fallback trainer: pure-Python logistic regression + stdlib metrics."""
    X_train, X_test, y_train, y_test = _stratified_split(X, y)

    model = LogisticRegressionLite(feature_names)
    model.fit(X_train, y_train, lr=0.2, epochs=500, l2=0.001)

    scores_test = [model.predict_proba(row) for row in X_test]
    eval_metrics = M.evaluate(y_test, scores_test)

    os.makedirs(models_dir, exist_ok=True)
    model.save(os.path.join(models_dir, "fit_predictor.json"))

    metadata = {
        "name": "candidate_fit_predictor",
        "version": "1.0.0",
        "backend": "pure_python::logistic_regression",
        "model_file": "fit_predictor.json",
        "feature_names": feature_names,
        "metrics": {k: v for k, v in eval_metrics.items() if k != "confusion_matrix"},
        "confusion_matrix": eval_metrics["confusion_matrix"],
        "feature_importance": model.feature_importance(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(models_dir, "metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    return metadata


def train(models_dir: str | None = None, n_samples: int = 4000, seed: int = 42) -> Dict[str, object]:
    """Generate data, train, evaluate, and persist the model."""
    models_dir = models_dir or DEFAULT_MODELS_DIR
    logger.info("Generating dataset (n=%d, seed=%d)…", n_samples, seed)
    X, y, feature_names = generate_dataset(n_samples=n_samples, seed=seed)
    positive_rate = sum(y) / len(y)
    logger.info("Dataset ready: %d samples, positive rate %.3f", len(y), positive_rate)

    try:
        from app.ml import train_sklearn  # noqa: WPS433 (lazy, optional deps)

        logger.info("scikit-learn/XGBoost available — training production model.")
        metadata = train_sklearn.train_and_save(X, y, feature_names, models_dir, random_state=seed)
    except ImportError:
        logger.warning(
            "scikit-learn/XGBoost not installed — training pure-Python fallback model."
        )
        metadata = _train_pure_python(X, y, feature_names, models_dir)

    logger.info("Training complete. Backend=%s metrics=%s", metadata["backend"], metadata["metrics"])
    return metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    result = train()
    print(json.dumps(result, indent=2))
