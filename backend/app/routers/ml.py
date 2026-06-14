"""Machine-learning routes: model metadata and direct fit prediction.

These expose the trained candidate-fit predictor for inspection and for
ad-hoc/demo predictions from a raw feature dict. The full resume-vs-job match
endpoint is added in Milestone 6 on top of this model.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser
from app.ml.features import FEATURE_NAMES, features_to_vector
from app.ml.registry import get_predictor

router = APIRouter(prefix="/ml", tags=["ml"])


class ModelInfo(BaseModel):
    is_trained: bool
    backend: str
    feature_names: List[str]
    metrics: Dict[str, object] = Field(default_factory=dict)
    feature_importance: List[Dict[str, object]] = Field(default_factory=list)
    version: Optional[str] = None
    trained_at: Optional[str] = None


class FeatureInput(BaseModel):
    """Raw feature values keyed by feature name (missing keys default to 0)."""

    features: Dict[str, float]


class Contribution(BaseModel):
    feature: str
    value: float
    contribution: float


class PredictResult(BaseModel):
    fit_score: float
    interview_probability: float
    recommendation: str
    backend: str
    explanation: List[Contribution] = Field(default_factory=list)


@router.get("/model-info", response_model=ModelInfo)
async def model_info(current_user: CurrentUser) -> ModelInfo:
    """Return metadata, metrics, and feature importance for the active model."""
    predictor = get_predictor()
    meta = predictor.metadata
    return ModelInfo(
        is_trained=predictor.is_trained,
        backend=predictor.backend,
        feature_names=predictor.feature_names,
        metrics=meta.get("metrics", {}),
        feature_importance=predictor.feature_importance(),
        version=meta.get("version"),
        trained_at=meta.get("trained_at"),
    )


@router.post("/predict", response_model=PredictResult)
async def predict(payload: FeatureInput, current_user: CurrentUser) -> PredictResult:
    """Predict candidate fit from a raw feature dict (demo/debug endpoint)."""
    vector = features_to_vector(payload.features)
    result = get_predictor().predict(vector)
    return PredictResult(**result)


@router.get("/feature-schema", response_model=List[str])
async def feature_schema(current_user: CurrentUser) -> List[str]:
    """List the feature names the model expects (ordered)."""
    return FEATURE_NAMES
