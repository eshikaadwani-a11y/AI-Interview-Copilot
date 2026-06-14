"""Interview simulator service.

Owns the interview session state machine and persistence. Conducts a dynamic
interview: selects base questions, records answers, and injects follow-up
questions (LLM-generated when a provider is configured, deterministic
otherwise). Scoring/evaluation is added in Milestone 10.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId

from app.core.errors import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.db.mongo import get_database
from app.models.interview import (
    InterviewDetail,
    InterviewStart,
    InterviewState,
    InterviewSummary,
    QuestionFull,
    QuestionPublic,
)
from app.services import interview_bank, resume_service
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)

_COLLECTION = "interviews"


async def start_interview(user_id: str, payload: InterviewStart) -> InterviewState:
    if payload.mode not in interview_bank.MODE_CATEGORIES:
        raise ValidationAppError(f"Unknown interview mode: {payload.mode}")

    project_names: List[str] = []
    if payload.resume_id:
        try:
            resume = await resume_service.get_resume(user_id, payload.resume_id)
            project_names = [p.name for p in resume.profile.projects if p.name]
        except NotFoundError:
            project_names = []

    selected = interview_bank.select_questions(
        payload.mode,
        payload.categories,
        count=payload.num_questions,
        project_names=project_names,
    )
    questions = [
        {
            "index": i,
            "category": q["category"],
            "difficulty": q["difficulty"],
            "text": q["text"],
            "type": "base",
            "answer": None,
            "followed_up": False,
        }
        for i, q in enumerate(selected)
    ]

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "mode": payload.mode,
        "categories": interview_bank.resolve_categories(payload.mode, payload.categories),
        "resume_id": payload.resume_id,
        "job_id": payload.job_id,
        "status": "active",
        "questions": questions,
        "current_index": 0,
        "created_at": now,
        "completed_at": None,
    }
    db = get_database()
    result = await db[_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Started interview %s (mode=%s, %d questions)", result.inserted_id, payload.mode, len(questions))
    return _to_state(doc)


async def submit_answer(user_id: str, interview_id: str, answer: str) -> InterviewState:
    doc = await _get_owned(user_id, interview_id)
    if doc["status"] != "active":
        raise ValidationAppError("This interview is already completed.")

    questions = doc["questions"]
    idx = doc["current_index"]
    if idx >= len(questions):
        doc["status"] = "completed"
        doc["completed_at"] = datetime.now(timezone.utc)
        await _save(doc)
        return _to_state(doc)

    current = questions[idx]
    current["answer"] = answer

    # Generate a single follow-up for base questions with a substantive answer.
    if current["type"] == "base" and not current.get("followed_up"):
        followup_text = _generate_followup(current["category"], current["text"], answer)
        current["followed_up"] = True
        if followup_text:
            followup = {
                "index": len(questions),
                "category": current["category"],
                "difficulty": current.get("difficulty"),
                "text": followup_text,
                "type": "followup",
                "answer": None,
                "followed_up": True,
            }
            questions.insert(idx + 1, followup)

    doc["current_index"] = idx + 1
    if doc["current_index"] >= len(questions):
        doc["status"] = "completed"
        doc["completed_at"] = datetime.now(timezone.utc)

    await _save(doc)
    return _to_state(doc)


async def finish_interview(user_id: str, interview_id: str) -> InterviewState:
    doc = await _get_owned(user_id, interview_id)
    doc["status"] = "completed"
    doc["completed_at"] = datetime.now(timezone.utc)
    await _save(doc)
    return _to_state(doc)


async def get_interview(user_id: str, interview_id: str) -> InterviewDetail:
    doc = await _get_owned(user_id, interview_id)
    return InterviewDetail(
        id=str(doc["_id"]),
        mode=doc["mode"],
        mode_label=interview_bank.MODE_LABELS.get(doc["mode"], doc["mode"]),
        status=doc["status"],
        questions=[
            QuestionFull(
                index=q["index"],
                category=q["category"],
                difficulty=q.get("difficulty"),
                text=q["text"],
                type=q["type"],
                answer=q.get("answer"),
            )
            for q in doc["questions"]
        ],
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
    )


async def list_interviews(user_id: str) -> List[InterviewSummary]:
    db = get_database()
    cursor = db[_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    out: List[InterviewSummary] = []
    async for doc in cursor:
        answered = sum(1 for q in doc["questions"] if q.get("answer"))
        out.append(
            InterviewSummary(
                id=str(doc["_id"]),
                mode=doc["mode"],
                mode_label=interview_bank.MODE_LABELS.get(doc["mode"], doc["mode"]),
                status=doc["status"],
                total=len(doc["questions"]),
                answered=answered,
                created_at=doc["created_at"],
            )
        )
    return out


# ── Helpers ──────────────────────────────────────────────────────────────
def _generate_followup(category: str, question: str, answer: str) -> Optional[str]:
    provider = get_llm_provider()
    if provider.name.startswith("local"):
        return interview_bank.deterministic_followup(category, answer)

    system = (
        "You are a technical interviewer. Given a question and the candidate's "
        "answer, ask ONE concise, probing follow-up question. Return only the "
        "question text."
    )
    prompt = f"Question: {question}\nCandidate answer: {answer}\n\nFollow-up question:"
    try:
        text = provider.generate(system, prompt, max_tokens=80).strip()
        return text or interview_bank.deterministic_followup(category, answer)
    except Exception as exc:  # pragma: no cover
        logger.warning("LLM follow-up failed: %s", exc)
        return interview_bank.deterministic_followup(category, answer)


def _to_state(doc: dict) -> InterviewState:
    questions = doc["questions"]
    idx = doc["current_index"]
    answered = sum(1 for q in questions if q.get("answer"))
    finished = doc["status"] != "active" or idx >= len(questions)
    current = None
    if not finished and idx < len(questions):
        q = questions[idx]
        current = QuestionPublic(
            index=q["index"],
            category=q["category"],
            difficulty=q.get("difficulty"),
            text=q["text"],
            type=q["type"],
        )
    return InterviewState(
        id=str(doc["_id"]),
        mode=doc["mode"],
        mode_label=interview_bank.MODE_LABELS.get(doc["mode"], doc["mode"]),
        status=doc["status"],
        total=len(questions),
        answered=answered,
        current_index=idx,
        current_question=current,
        finished=finished,
    )


async def _get_owned(user_id: str, interview_id: str) -> dict:
    if not ObjectId.is_valid(interview_id):
        raise NotFoundError("Interview not found")
    db = get_database()
    doc = await db[_COLLECTION].find_one({"_id": ObjectId(interview_id), "user_id": user_id})
    if doc is None:
        raise NotFoundError("Interview not found")
    return doc


async def _save(doc: dict) -> None:
    db = get_database()
    await db[_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {
            "questions": doc["questions"],
            "current_index": doc["current_index"],
            "status": doc["status"],
            "completed_at": doc.get("completed_at"),
        }},
    )
