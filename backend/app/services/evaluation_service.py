"""Interview evaluation service.

Scores each answered question (deterministic rubric), aggregates the results,
computes a resume-fit signal via Model 1, and predicts interview success via
Model 2 (the Interview Success Predictor). Produces and persists a full
performance report.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.ml.features import compute_features, features_to_vector
from app.ml.interview_features import (
    compute_interview_features,
    interview_features_to_vector,
)
from app.ml.registry import get_interview_predictor, get_predictor
from app.models.evaluation import (
    AggregateScores,
    AnswerEvaluation,
    EvaluatedQuestion,
    InterviewReport,
)
from app.services import interview_bank, job_service, resume_service
from app.services.evaluation_logic import evaluate_answer

logger = get_logger(__name__)

_COLLECTION = "interviews"


async def evaluate_interview(user_id: str, interview_id: str) -> InterviewReport:
    doc = await _get_owned(user_id, interview_id)
    questions = doc["questions"]

    evaluated = 0
    dim_totals = {"technical": 0.0, "communication": 0.0, "completeness": 0.0,
                  "confidence": 0.0, "overall": 0.0}
    all_strengths: List[str] = []
    all_weaknesses: List[str] = []
    all_suggestions: List[str] = []

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
        all_strengths.extend(ev["strengths"])
        all_weaknesses.extend(ev["weaknesses"])
        all_suggestions.extend(ev["suggestions"])

    if evaluated == 0:
        aggregate = {k: 0.0 for k in dim_totals}
    else:
        aggregate = {k: round(v / evaluated, 1) for k, v in dim_totals.items()}

    completion_ratio = evaluated / len(questions) if questions else 0.0
    resume_fit = await _resume_fit(user_id, doc.get("resume_id"), doc.get("job_id"))

    iv_features = compute_interview_features(aggregate, completion_ratio, resume_fit)
    iv_vector = interview_features_to_vector(iv_features)
    prediction = get_interview_predictor().predict(iv_vector)

    doc["evaluation_aggregate"] = aggregate
    doc["success_probability"] = prediction["probability"]
    doc["success_label"] = prediction["recommendation"]
    doc["model_backend"] = prediction["backend"]
    doc["evaluated_at"] = datetime.now(timezone.utc)
    await _save_evaluation(doc)

    return _assemble_report(
        doc, aggregate, prediction, _top(all_strengths), _top(all_weaknesses), _top(all_suggestions)
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
    return _assemble_report(doc, aggregate, prediction, _top(strengths), _top(weaknesses), _top(suggestions))


# ── Helpers ──────────────────────────────────────────────────────────────
async def _resume_fit(user_id: str, resume_id: Optional[str], job_id: Optional[str]) -> float:
    """Compute the candidate's resume-vs-job fit (Model 1) or a neutral 0.5."""
    if not resume_id or not job_id:
        return 0.5
    try:
        resume = await resume_service.get_resume(user_id, resume_id)
        job = await job_service.get_job(user_id, job_id)
    except NotFoundError:
        return 0.5
    features = compute_features(resume.profile.model_dump(), job.profile.model_dump())
    result = get_predictor().predict(features_to_vector(features))
    return float(result["probability"])


def _top(items: List[str], n: int = 5) -> List[str]:
    """Most frequent distinct items, preserving order of first appearance."""
    counts = Counter(items)
    return [item for item, _ in counts.most_common(n)]


def _assemble_report(doc, aggregate, prediction, strengths, weaknesses, suggestions) -> InterviewReport:
    answered = sum(1 for q in doc["questions"] if q.get("answer"))
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
        answered=answered,
        total=len(doc["questions"]),
        aggregate=AggregateScores(
            technical=aggregate["technical"],
            communication=aggregate["communication"],
            completeness=aggregate["completeness"],
            confidence=aggregate["confidence"],
            overall=aggregate["overall"],
        ),
        success_probability=round(prediction["probability"], 4),
        success_label=prediction["recommendation"],
        model_backend=prediction["backend"],
        per_question=per_question,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions,
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
            "success_probability": doc["success_probability"],
            "success_label": doc["success_label"],
            "model_backend": doc["model_backend"],
            "evaluated_at": doc["evaluated_at"],
        }},
    )
