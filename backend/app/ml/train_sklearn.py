"""Production trainer using scikit-learn + XGBoost + SHAP.

This module is imported lazily by ``train.py`` and only when those libraries
are installed (e.g. inside Docker / a full environment). It trains a
RandomForest baseline and an XGBoost model, selects the better by
cross-validated ROC-AUC, calibrates probabilities, evaluates on a hold-out
set, and fits a SHAP explainer for per-prediction explanations.

Artifacts written to ``models_dir``:
    - fit_predictor.joblib   (calibrated model + SHAP explainer + feature names)
    - metadata.json          (metrics, feature importance, provenance)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Sequence

import joblib
import numpy as np
import shap
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from xgboost import XGBClassifier


def train_and_save(
    X: Sequence[Sequence[float]],
    y: Sequence[int],
    feature_names: List[str],
    models_dir: str,
    *,
    model_name: str = "candidate_fit_predictor",
    file_stem: str = "fit_predictor",
    random_state: int = 42,
) -> Dict[str, object]:
    """Train, evaluate, and persist a binary classifier (XGBoost/RandomForest)."""
    os.makedirs(models_dir, exist_ok=True)
    X_arr = np.asarray(X, dtype=float)
    y_arr = np.asarray(y, dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X_arr, y_arr, test_size=0.2, stratify=y_arr, random_state=random_state
    )

    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=8, random_state=random_state, n_jobs=-1
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=random_state,
        ),
    }

    # Select the better model by cross-validated ROC-AUC.
    cv_scores: Dict[str, float] = {}
    for name, clf in candidates.items():
        scores = cross_val_score(clf, X_train, y_train, cv=5, scoring="roc_auc")
        cv_scores[name] = float(scores.mean())
    best_name = max(cv_scores, key=cv_scores.get)
    best_model = candidates[best_name]

    # Calibrate probabilities for trustworthy fit/interview scores.
    calibrated = CalibratedClassifierCV(best_model, cv=5, method="isotonic")
    calibrated.fit(X_train, y_train)

    # Evaluate on the hold-out set.
    proba_test = calibrated.predict_proba(X_test)[:, 1]
    pred_test = (proba_test >= 0.5).astype(int)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, pred_test)), 4),
        "precision": round(float(precision_score(y_test, pred_test, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred_test, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred_test, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba_test)), 4),
        "n_samples": int(len(y_test)),
    }

    # Fit the underlying tree model on all training data for SHAP/importance.
    best_model.fit(X_train, y_train)
    explainer = shap.TreeExplainer(best_model)
    importances = best_model.feature_importances_
    feature_importance = sorted(
        (
            {"feature": feature_names[i], "importance": round(float(importances[i]), 4)}
            for i in range(len(feature_names))
        ),
        key=lambda d: d["importance"],
        reverse=True,
    )

    artifact = {
        "type": f"sklearn::{best_name}",
        "model": calibrated,
        "tree_model": best_model,
        "explainer": explainer,
        "feature_names": feature_names,
    }
    model_path = os.path.join(models_dir, f"{file_stem}.joblib")
    joblib.dump(artifact, model_path)

    metadata = {
        "name": model_name,
        "version": "1.0.0",
        "backend": f"sklearn::{best_name}",
        "model_file": f"{file_stem}.joblib",
        "feature_names": feature_names,
        "metrics": metrics,
        "cv_roc_auc": {k: round(v, 4) for k, v in cv_scores.items()},
        "feature_importance": feature_importance,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(models_dir, f"{file_stem}_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    return metadata
