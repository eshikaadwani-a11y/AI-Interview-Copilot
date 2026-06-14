"""Training orchestrator for both ML models.

Run with:  ``python -m app.ml.train``

Trains:
    1. Candidate Fit Predictor      (fit_predictor)
    2. Interview Success Predictor  (interview_predictor)

Tries the production scikit-learn/XGBoost trainer first; if those libraries are
not installed, it transparently falls back to the dependency-free pure-Python
logistic regression so the pipeline produces trained models and real metrics in
ANY environment. Each model writes ``<stem>_metadata.json``.
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
from app.ml.interview_datagen import generate_interview_dataset
from app.ml.model import LogisticRegressionLite

logger = logging.getLogger("app.ml.train")

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

    return (
        [X[i] for i in train_idx],
        [X[i] for i in test_idx],
        [y[i] for i in train_idx],
        [y[i] for i in test_idx],
    )


def _train_pure_python(
    X: Sequence[Sequence[float]],
    y: Sequence[int],
    feature_names: List[str],
    models_dir: str,
    *,
    model_name: str,
    file_stem: str,
) -> Dict[str, object]:
    """Fallback trainer: pure-Python logistic regression + stdlib metrics."""
    X_train, X_test, y_train, y_test = _stratified_split(X, y)

    model = LogisticRegressionLite(feature_names)
    model.fit(X_train, y_train, lr=0.2, epochs=500, l2=0.001)

    scores_test = [model.predict_proba(row) for row in X_test]
    eval_metrics = M.evaluate(y_test, scores_test)

    os.makedirs(models_dir, exist_ok=True)
    model.save(os.path.join(models_dir, f"{file_stem}.json"))

    metadata = {
        "name": model_name,
        "version": "1.0.0",
        "backend": "pure_python::logistic_regression",
        "model_file": f"{file_stem}.json",
        "feature_names": feature_names,
        "metrics": {k: v for k, v in eval_metrics.items() if k != "confusion_matrix"},
        "confusion_matrix": eval_metrics["confusion_matrix"],
        "feature_importance": model.feature_importance(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(models_dir, f"{file_stem}_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    return metadata


def _train_one(
    X, y, feature_names, models_dir, *, model_name, file_stem, seed
) -> Dict[str, object]:
    try:
        from app.ml import train_sklearn  # lazy, optional deps

        logger.info("[%s] scikit-learn available — training production model.", file_stem)
        return train_sklearn.train_and_save(
            X, y, feature_names, models_dir,
            model_name=model_name, file_stem=file_stem, random_state=seed,
        )
    except ImportError:
        logger.warning("[%s] scikit-learn not installed — pure-Python fallback.", file_stem)
        return _train_pure_python(
            X, y, feature_names, models_dir, model_name=model_name, file_stem=file_stem
        )


def train(models_dir: str | None = None, seed: int = 42) -> Dict[str, object]:
    """Generate data and train both models; return their metadata."""
    models_dir = models_dir or DEFAULT_MODELS_DIR

    logger.info("Training Candidate Fit Predictor…")
    Xf, yf, fit_features = generate_dataset(n_samples=4000, seed=seed)
    fit_meta = _train_one(
        Xf, yf, fit_features, models_dir,
        model_name="candidate_fit_predictor", file_stem="fit_predictor", seed=seed,
    )
    logger.info("Fit model: backend=%s metrics=%s", fit_meta["backend"], fit_meta["metrics"])

    logger.info("Training Interview Success Predictor…")
    Xi, yi, iv_features = generate_interview_dataset(n_samples=3000, seed=seed + 1)
    iv_meta = _train_one(
        Xi, yi, iv_features, models_dir,
        model_name="interview_success_predictor", file_stem="interview_predictor", seed=seed,
    )
    logger.info("Interview model: backend=%s metrics=%s", iv_meta["backend"], iv_meta["metrics"])

    return {"fit": fit_meta, "interview": iv_meta}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    result = train()
    print(json.dumps(result, indent=2))
