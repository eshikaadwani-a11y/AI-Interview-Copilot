"""Pure-Python logistic regression classifier.

A dependency-free, genuinely-trained model (gradient descent + feature
standardisation + L2 regularisation) used as the offline-capable path and as a
graceful fallback when the scikit-learn/XGBoost artifact is unavailable.

Being a linear model, it is inherently explainable: the contribution of each
feature to a prediction is ``weight_i * standardized_x_i`` — the same idea SHAP
applies, computed exactly for linear models.
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Sequence


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


class LogisticRegressionLite:
    """Logistic regression trained with batch gradient descent."""

    def __init__(self, feature_names: List[str]) -> None:
        self.feature_names = list(feature_names)
        self.weights: List[float] = [0.0] * len(feature_names)
        self.bias: float = 0.0
        self.mean: List[float] = [0.0] * len(feature_names)
        self.std: List[float] = [1.0] * len(feature_names)
        self.trained: bool = False

    # ── Standardisation ──────────────────────────────────────────────
    def _fit_scaler(self, X: Sequence[Sequence[float]]) -> None:
        n = len(X)
        d = len(self.feature_names)
        means = [0.0] * d
        for row in X:
            for j in range(d):
                means[j] += row[j]
        means = [m / n for m in means]
        variances = [0.0] * d
        for row in X:
            for j in range(d):
                variances[j] += (row[j] - means[j]) ** 2
        stds = [math.sqrt(v / n) or 1.0 for v in variances]
        self.mean, self.std = means, stds

    def _scale(self, row: Sequence[float]) -> List[float]:
        return [(row[j] - self.mean[j]) / self.std[j] for j in range(len(row))]

    # ── Training ─────────────────────────────────────────────────────
    def fit(
        self,
        X: Sequence[Sequence[float]],
        y: Sequence[int],
        *,
        lr: float = 0.1,
        epochs: int = 400,
        l2: float = 0.001,
    ) -> "LogisticRegressionLite":
        self._fit_scaler(X)
        Xs = [self._scale(row) for row in X]
        n = len(Xs)
        d = len(self.feature_names)
        self.weights = [0.0] * d
        self.bias = 0.0

        for _ in range(epochs):
            grad_w = [0.0] * d
            grad_b = 0.0
            for i in range(n):
                pred = self._raw_proba(Xs[i])
                error = pred - y[i]
                for j in range(d):
                    grad_w[j] += error * Xs[i][j]
                grad_b += error
            for j in range(d):
                grad_w[j] = grad_w[j] / n + l2 * self.weights[j]
                self.weights[j] -= lr * grad_w[j]
            self.bias -= lr * (grad_b / n)

        self.trained = True
        return self

    def _raw_proba(self, scaled_row: Sequence[float]) -> float:
        z = self.bias + sum(self.weights[j] * scaled_row[j] for j in range(len(scaled_row)))
        return _sigmoid(z)

    # ── Inference ────────────────────────────────────────────────────
    def predict_proba(self, row: Sequence[float]) -> float:
        return self._raw_proba(self._scale(row))

    def predict(self, row: Sequence[float], threshold: float = 0.5) -> int:
        return 1 if self.predict_proba(row) >= threshold else 0

    def explain(self, row: Sequence[float]) -> List[Dict[str, float]]:
        """Per-feature contribution to the prediction logit (descending |value|)."""
        scaled = self._scale(row)
        contributions = [
            {
                "feature": self.feature_names[j],
                "value": round(row[j], 4),
                "contribution": round(self.weights[j] * scaled[j], 4),
            }
            for j in range(len(row))
        ]
        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        return contributions

    def feature_importance(self) -> List[Dict[str, float]]:
        """Global importance proxied by absolute standardised weights."""
        importance = [
            {"feature": self.feature_names[j], "importance": round(abs(self.weights[j]), 4)}
            for j in range(len(self.feature_names))
        ]
        importance.sort(key=lambda c: c["importance"], reverse=True)
        return importance

    # ── Persistence ──────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, object]:
        return {
            "type": "logistic_regression_lite",
            "feature_names": self.feature_names,
            "weights": self.weights,
            "bias": self.bias,
            "mean": self.mean,
            "std": self.std,
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "LogisticRegressionLite":
        model = cls(list(data["feature_names"]))  # type: ignore[arg-type]
        model.weights = list(data["weights"])  # type: ignore[arg-type]
        model.bias = float(data["bias"])  # type: ignore[arg-type]
        model.mean = list(data["mean"])  # type: ignore[arg-type]
        model.std = list(data["std"])  # type: ignore[arg-type]
        model.trained = True
        return model

    @classmethod
    def load(cls, path: str) -> "LogisticRegressionLite":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
