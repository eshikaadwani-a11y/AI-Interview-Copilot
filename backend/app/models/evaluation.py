"""Interview evaluation / performance report models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    technical: float
    communication: float
    completeness: float
    confidence: float
    score: float
    matched_concepts: List[str] = Field(default_factory=list)
    missed_concepts: List[str] = Field(default_factory=list)
    explanations: Dict[str, List[str]] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class EvaluatedQuestion(BaseModel):
    index: int
    category: str
    type: str
    question: str
    answer: Optional[str] = None
    evaluation: Optional[AnswerEvaluation] = None


class AggregateScores(BaseModel):
    technical: float
    communication: float
    completeness: float
    confidence: float
    overall: float


class FeatureContribution(BaseModel):
    feature: str
    label: str
    value: float
    contribution: float


class LearningItem(BaseModel):
    topic: str
    title: str
    url: str


class InterviewReport(BaseModel):
    interview_id: str
    mode_label: str
    status: str
    answered: int
    total: int
    aggregate: AggregateScores
    category_scores: Dict[str, float] = Field(default_factory=dict)
    success_probability: float
    success_label: str
    prediction_confidence: float
    model_backend: str
    model_version: Optional[str] = None
    success_explanation: List[FeatureContribution] = Field(default_factory=list)
    feature_importance: List[Dict[str, object]] = Field(default_factory=list)
    per_question: List[EvaluatedQuestion] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    recommended_learning: List[LearningItem] = Field(default_factory=list)
    created_at: datetime
