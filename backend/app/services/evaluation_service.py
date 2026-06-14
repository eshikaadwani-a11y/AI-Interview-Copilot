"""Interview evaluation service.

Scores each answered question (deterministic rubric with per-dimension
explanations), aggregates results (overall + per-category), computes the
resume-vs-job match score via Model 1, and predicts interview success via
Model 2 using interview scores + match score + resume features.

Persists: model version, prediction confidence, feature contributions, and
feature importance. Produces a full, explainable performance report.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.ml.features import compute_features, features_to_vector
from app.ml.interview_features import (
    INTERVIEW_FEATURE_LABELS,
    compute_interview_features,
    interview_features_to_vector,
)
from app.ml.registry import get_interview_predictor, get_predictor
from app.models.evaluation import (
    AggregateScores,
    AnswerEvaluation,
    EvaluatedQuestion,
    FeatureContribution,
    InterviewReport,
    LearningItem,
)
from app.services import interview_bank, job_service, mentor_logic, resume_service
from app.services.evaluation_logic import evaluate_answer

logger = get_logger(__name__)

_COLLECTION = "interviews"


async def evaluate_interview(user_id: str, interview_id: str) -> InterviewReport:
    doc = await _get_owned(user_id, interview_id)
    questions = doc["questions"]

    evaluated = 0
    dim_totals = {"technical": 0.0, "communication": 0.0, "completeness": 0.0,
                  "confidence": 0.0, "overall": 0.0}
    cat_totals: Dict[str, List[float]] = defaultdict(list)
    all_strengths: List[str] = []
    all_weaknesses: List[str] = []
    all_suggestions: List[str] = []
    all_missed: List[str] = []

    for q in questions:
        answer = q.get("answer")
        if not answer:
            q["evaluation"] = None
            continue
        ev = evaluate_answer(q["category"], q["text"], answer)
        q["evaluation"] = ev
        evaluated += 1
        dim_totals["technical"] += ev["technical"]
        dim_totals["communication"] += ev["communication"]
        dim_totals["completeness"] += ev["completeness"]
        dim_totals["confidence"] += ev["confidence"]
        dim_totals["overall"] += ev["score"]
        cat_totals[q["category"]].append(ev["score"])
        all_strengths.extend(ev["strengths"])
        all_weaknesses.extend(ev["weaknesses"])
        all_suggestions.extend(ev["suggestions"])
        all_missed.extend(ev.get("missed_concepts", []))

    if evaluated == 0:
        aggregate = {k: 0.0 for k in dim_totals}
    else:
        aggregate = {k: round(v / evaluated, 1) for k, v in dim_totals.items()}
    category_scores = {c: round(sum(v) / len(v), 1) for c, v in cat_totals.items()}

    completion_ratio = evaluated / len(questions) if questions else 0.0
    match_score, resume_months, skill_count = await _resume_signals(
        user_id, doc.get("resume_id"), doc.get("job_id")
    )

    iv_features = compute_interview_features(
        aggregate, completion_ratio, match_score, resume_months, skill_count
    )
    iv_vector = interview_features_to_vector(iv_features)
    predictor = get_interview_predictor()
    prediction = predictor.predict(iv_vector)
    prob = prediction["probability"]
    prediction_confidence = round(max(prob, 1.0 - prob), 4)

    recommended = _learning_plan(all_missed, all_weaknesses)

    # Persist evaluation + model provenance.
    doc["evaluation_aggregate"] = aggregate
    doc["category_scores"] = category_scores
    doc["success_probability"] = prob
    doc["success_label"] = prediction["recommendation"]
    doc["prediction_confidence"] = prediction_confidence
    doc["model_backend"] = prediction["backend"]
    doc["model_version"] = predictor.metadata.get("version")
    doc["success_explanation"] = prediction.get("explanation", [])
    doc["feature_importance"] = predictor.feature_importance()
    doc["recommended_learning"] = [item.model_dump() for item in recommended]
    doc["evaluated_at"] = datetime.now(timezone.utc)
    await _save_evaluation(doc)

    return _assemble_report(
        doc, aggregate, category_scores, prediction, prediction_confidence,
        predictor, _top(all_strengths), _top(all_weaknesses), _top(all_suggestions), recommended,
    )


async def get_report(user_id: str, interview_id: str) -> InterviewReport:
    """Return a stored report, evaluating on the fly if not yet evaluated."""
    doc = await _get_owned(user_id, interview_id)
    if "success_probability" not in doc or doc.get("evaluation_aggregate") is None:
        return await evaluate_interview(user_id, interview_id)

    aggregate = doc["evaluation_aggregate"]
    prediction = {
        "probability": doc["success_probability"],
        "recommendation": doc.get("success_label", ""),
        "backend": doc.get("model_backend", ""),
        "explanation": doc.get("success_explanation", []),
    }
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []
    for q in doc["questions"]:
        ev = q.get("evaluation")
        if ev:
            strengths.extend(ev.get("strengths", []))
            weaknesses.extend(ev.get("weaknesses", []))
            suggestions.extend(ev.get("suggestions", []))
    recommended = [LearningItem.model_validate(x) for x in doc.get("recommended_learning", [])]
    return _assemble_report(
        doc, aggregate, doc.get("category_scores", {}), prediction,
        doc.get("prediction_confidence", 0.0), get_interview_predictor(),
        _top(strengths), _top(weaknesses), _top(suggestions), recommended,
        stored_importance=doc.get("feature_importance"),
    )


# ── Helpers ──────────────────────────────────────────────────────────────
async def _resume_signals(
    user_id: str, resume_id: Optional[str], job_id: Optional[str]
) -> Tuple[float, float, int]:
    """Return (match_score, resume_experience_months, resume_skill_count)."""
    if not resume_id:
        return 0.5, 0.0, 0
    try:
        resume = await resume_service.get_resume(user_id, resume_id)
    except NotFoundError:
        return 0.5, 0.0, 0
    profile = resume.profile.model_dump()
    months = float(profile.get("total_experience_months", 0) or 0)
    skill_count = len(profile.get("skills", []))

    match_score = 0.5
    if job_id:
        try:
            job = await job_service.get_job(user_id, job_id)
            features = compute_features(profile, job.profile.model_dump())
            match_score = float(get_predictor().predict(features_to_vector(features))["probability"])
        except NotFoundError:
            match_score = 0.5
    return match_score, months, skill_count


def _learning_plan(missed_concepts: List[str], weaknesses: List[str]) -> List[LearningItem]:
    """Map the most-missed concepts to concrete learning resources."""
    topics = [t for t, _ in Counter(missed_concepts).most_common(5)]
    items: List[LearningItem] = []
    for topic in topics:
        title, url = mentor_logic.resource_for(topic.title())
        items.append(LearningItem(topic=topic, title=title, url=url))
    return items


def _top(items: List[str], n: int = 5) -> List[str]:
    counts = Counter(items)
    return [item for item, _ in counts.most_common(n)]


def _assemble_report(
    doc, aggregate, category_scores, prediction, prediction_confidence,
    predictor, strengths, weaknesses, suggestions, recommended, *, stored_importance=None,
) -> InterviewReport:
    explanation = [
        FeatureContribution(
            feature=c["feature"],
            label=INTERVIEW_FEATURE_LABELS.get(c["feature"], c["feature"]),
            value=c.get("value", 0.0),
            contribution=c.get("contribution", 0.0),
        )
        for c in prediction.get("explanation", [])
    ]
    per_question = [
        EvaluatedQuestion(
            index=q["index"],
            category=q["category"],
            type=q["type"],
            question=q["text"],
            answer=q.get("answer"),
            evaluation=AnswerEvaluation.model_validate(q["evaluation"]) if q.get("evaluation") else None,
        )
        for q in doc["questions"]
    ]
    return InterviewReport(
        interview_id=str(doc["_id"]),
        mode_label=interview_bank.MODE_LABELS.get(doc["mode"], doc["mode"]),
        status=doc["status"],
        answered=sum(1 for q in doc["questions"] if q.get("answer")),
        total=len(doc["questions"]),
        aggregate=AggregateScores(
            technical=aggregate["technical"],
            communication=aggregate["communication"],
            completeness=aggregate["completeness"],
            confidence=aggregate["confidence"],
            overall=aggregate["overall"],
        ),
        category_scores=category_scores,
        success_probability=round(prediction["probability"], 4),
        success_label=prediction["recommendation"],
        prediction_confidence=prediction_confidence,
        model_backend=prediction["backend"],
        model_version=doc.get("model_version") or predictor.metadata.get("version"),
        success_explanation=explanation,
        feature_importance=stored_importance or predictor.feature_importance(),
        per_question=per_question,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions,
        recommended_learning=recommended,
        created_at=doc.get("evaluated_at") or doc["created_at"],
    )


async def _get_owned(user_id: str, interview_id: str) -> dict:
    if not ObjectId.is_valid(interview_id):
        raise NotFoundError("Interview not found")
    db = get_database()
    doc = await db[_COLLECTION].find_one({"_id": ObjectId(interview_id), "user_id": user_id})
    if doc is None:
        raise NotFoundError("Interview not found")
    return doc


async def _save_evaluation(doc: dict) -> None:
    db = get_database()
    await db[_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {
            "questions": doc["questions"],
            "evaluation_aggregate": doc["evaluation_aggregate"],
            "category_scores": doc["category_scores"],
            "success_probability": doc["success_probability"],
            "success_label": doc["success_label"],
            "prediction_confidence": doc["prediction_confidence"],
            "model_backend": doc["model_backend"],
            "model_version": doc["model_version"],
            "success_explanation": doc["success_explanation"],
            "feature_importance": doc["feature_importance"],
            "recommended_learning": doc["recommended_learning"],
            "evaluated_at": doc["evaluated_at"],
        }},
    )
