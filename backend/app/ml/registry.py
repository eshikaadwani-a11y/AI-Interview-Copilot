"""Model registry — loads the trained candidate-fit predictor for inference.

Provides a single ``Predictor`` abstraction over either backend:
    - scikit-learn/XGBoost artifact (``fit_predictor.joblib``) with SHAP, or
    - pure-Python logistic regression (``fit_predictor.json``).

The model is loaded once and cached. If no artifact exists yet, prediction
falls back to the deterministic feature-average heuristic so the API never
hard-fails before training has run.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.features import FEATURE_NAMES
from app.ml.model import LogisticRegressionLite

logger = get_logger(__name__)


def _recommendation(prob: float) -> str:
    if prob >= 0.7:
        return "Strong Fit"
    if prob >= 0.45:
        return "Consider"
    return "Unlikely Fit"


class Predictor:
    """Unified inference wrapper for the candidate-fit predictor."""

    def __init__(self) -> None:
        self.backend: str = "heuristic"
        self.feature_names: List[str] = list(FEATURE_NAMES)
        self.metadata: Dict[str, object] = {}
        self._lite: Optional[LogisticRegressionLite] = None
        self._sklearn_artifact: Optional[dict] = None

    # ── Loading ──────────────────────────────────────────────────────
    def load(self) -> "Predictor":
        models_dir = settings.models_dir
        meta_path = os.path.join(models_dir, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as fh:
                self.metadata = json.load(fh)
            self.feature_names = list(self.metadata.get("feature_names", FEATURE_NAMES))

        joblib_path = os.path.join(models_dir, "fit_predictor.joblib")
        json_path = os.path.join(models_dir, "fit_predictor.json")

        if os.path.exists(joblib_path):
            try:
                import joblib  # lazy: only when artifact present

                self._sklearn_artifact = joblib.load(joblib_path)
                self.backend = str(self.metadata.get("backend", "sklearn"))
                logger.info("Loaded sklearn model (%s)", self.backend)
                return self
            except Exception as exc:  # pragma: no cover - env dependent
                logger.warning("Failed to load sklearn artifact: %s", exc)

        if os.path.exists(json_path):
            self._lite = LogisticRegressionLite.load(json_path)
            self.feature_names = self._lite.feature_names
            self.backend = "pure_python::logistic_regression"
            logger.info("Loaded pure-Python model")
            return self

        logger.warning("No trained model found in %s — using heuristic fallback.", models_dir)
        return self

    @property
    def is_trained(self) -> bool:
        return self.backend != "heuristic"

    # ── Inference ────────────────────────────────────────────────────
    def predict(self, vector: List[float]) -> Dict[str, object]:
        """Return fit score, interview probability, recommendation, explanation."""
        prob, contributions = self._proba_and_explain(vector)
        return {
            "fit_score": round(prob * 100, 1),
            "interview_probability": round(prob, 4),
            "recommendation": _recommendation(prob),
            "explanation": contributions,
            "backend": self.backend,
        }

    def _proba_and_explain(self, vector: List[float]):
        if self._sklearn_artifact is not None:
            return self._sklearn_proba(vector)
        if self._lite is not None:
            return self._lite.predict_proba(vector), self._lite.explain(vector)
        return self._heuristic(vector)

    def _sklearn_proba(self, vector: List[float]):
        import numpy as np  # lazy

        artifact = self._sklearn_artifact
        arr = np.asarray([vector], dtype=float)
        prob = float(artifact["model"].predict_proba(arr)[:, 1][0])

        contributions: List[Dict[str, float]] = []
        try:
            shap_values = artifact["explainer"].shap_values(arr)
            values = shap_values[1] if isinstance(shap_values, list) else shap_values
            row = values[0]
            for i, name in enumerate(self.feature_names):
                contributions.append(
                    {"feature": name, "value": round(vector[i], 4),
                     "contribution": round(float(row[i]), 4)}
                )
            contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        except Exception as exc:  # pragma: no cover - shap env dependent
            logger.debug("SHAP explanation unavailable: %s", exc)
        return prob, contributions

    def _heuristic(self, vector: List[float]):
        """Average of the (already 0..1-ish) features as a sane default."""
        prob = sum(vector) / len(vector) if vector else 0.0
        prob = max(0.0, min(prob, 1.0))
        return prob, []

    def feature_importance(self) -> List[Dict[str, float]]:
        if self.metadata.get("feature_importance"):
            return self.metadata["feature_importance"]  # type: ignore[return-value]
        if self._lite is not None:
            return self._lite.feature_importance()
        return []


# Process-wide singleton.
_predictor: Optional[Predictor] = None


def get_predictor() -> Predictor:
    global _predictor
    if _predictor is None:
        _predictor = Predictor().load()
    return _predictor


def reload_predictor() -> Predictor:
    """Force a reload (e.g. after retraining)."""
    global _predictor
    _predictor = Predictor().load()
    return _predictor
