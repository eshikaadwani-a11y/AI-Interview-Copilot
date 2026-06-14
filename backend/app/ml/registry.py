"""Model registry — loads trained predictors for inference.

Provides a generic ``Predictor`` over either backend (scikit-learn/XGBoost
joblib artifact with SHAP, or pure-Python logistic regression JSON) and two
cached singletons:

    get_predictor()            -> Candidate Fit Predictor   (Model 1)
    get_interview_predictor()  -> Interview Success Predictor (Model 2)

If no artifact exists yet, prediction falls back to a feature-average heuristic
so the API never hard-fails before training has run.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.features import FEATURE_NAMES
from app.ml.interview_features import INTERVIEW_FEATURE_NAMES
from app.ml.model import LogisticRegressionLite

logger = get_logger(__name__)

_RECOMMENDATION_LABELS = {
    "fit": [(0.7, "Strong Fit"), (0.45, "Consider"), (0.0, "Unlikely Fit")],
    "interview": [(0.7, "High likelihood"), (0.45, "Borderline"), (0.0, "Needs work")],
}


def _label(prob: float, kind: str) -> str:
    for threshold, label in _RECOMMENDATION_LABELS.get(kind, _RECOMMENDATION_LABELS["fit"]):
        if prob >= threshold:
            return label
    return "Unknown"


class Predictor:
    """Unified inference wrapper for a binary classifier."""

    def __init__(self, file_stem: str, default_features: List[str], kind: str) -> None:
        self.file_stem = file_stem
        self.kind = kind
        self.backend = "heuristic"
        self.feature_names = list(default_features)
        self.metadata: Dict[str, object] = {}
        self._lite: Optional[LogisticRegressionLite] = None
        self._sklearn_artifact: Optional[dict] = None

    def load(self) -> "Predictor":
        models_dir = settings.models_dir
        meta_path = os.path.join(models_dir, f"{self.file_stem}_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as fh:
                self.metadata = json.load(fh)
            self.feature_names = list(self.metadata.get("feature_names", self.feature_names))

        joblib_path = os.path.join(models_dir, f"{self.file_stem}.joblib")
        json_path = os.path.join(models_dir, f"{self.file_stem}.json")

        if os.path.exists(joblib_path):
            try:
                import joblib

                self._sklearn_artifact = joblib.load(joblib_path)
                self.backend = str(self.metadata.get("backend", "sklearn"))
                logger.info("Loaded %s model (%s)", self.file_stem, self.backend)
                return self
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to load %s joblib: %s", self.file_stem, exc)

        if os.path.exists(json_path):
            self._lite = LogisticRegressionLite.load(json_path)
            self.feature_names = self._lite.feature_names
            self.backend = "pure_python::logistic_regression"
            logger.info("Loaded %s model (pure-Python)", self.file_stem)
            return self

        logger.warning("No %s artifact — using heuristic fallback.", self.file_stem)
        return self

    @property
    def is_trained(self) -> bool:
        return self.backend != "heuristic"

    def predict(self, vector: List[float]) -> Dict[str, object]:
        prob, contributions = self._proba_and_explain(vector)
        return {
            "score": round(prob * 100, 1),
            "probability": round(prob, 4),
            "recommendation": _label(prob, self.kind),
            "explanation": contributions,
            "backend": self.backend,
        }

    def _proba_and_explain(self, vector: List[float]):
        if self._sklearn_artifact is not None:
            return self._sklearn_proba(vector)
        if self._lite is not None:
            return self._lite.predict_proba(vector), self._lite.explain(vector)
        prob = max(0.0, min(sum(vector) / len(vector), 1.0)) if vector else 0.0
        return prob, []

    def _sklearn_proba(self, vector: List[float]):
        import numpy as np

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
        except Exception as exc:  # pragma: no cover
            logger.debug("SHAP unavailable: %s", exc)
        return prob, contributions

    def feature_importance(self) -> List[Dict[str, float]]:
        if self.metadata.get("feature_importance"):
            return self.metadata["feature_importance"]  # type: ignore[return-value]
        if self._lite is not None:
            return self._lite.feature_importance()
        return []


_fit_predictor: Optional[Predictor] = None
_interview_predictor: Optional[Predictor] = None


def get_predictor() -> Predictor:
    global _fit_predictor
    if _fit_predictor is None:
        _fit_predictor = Predictor("fit_predictor", FEATURE_NAMES, "fit").load()
    return _fit_predictor


def get_interview_predictor() -> Predictor:
    global _interview_predictor
    if _interview_predictor is None:
        _interview_predictor = Predictor(
            "interview_predictor", INTERVIEW_FEATURE_NAMES, "interview"
        ).load()
    return _interview_predictor


def reload_predictors() -> None:
    global _fit_predictor, _interview_predictor
    _fit_predictor = None
    _interview_predictor = None
