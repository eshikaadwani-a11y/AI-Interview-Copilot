"""RAG routes: document ingestion and grounded querying."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.models.rag import IngestResponse, QueryRequest, QueryResponse
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest/resume/{resume_id}", response_model=IngestResponse)
async def ingest_resume(resume_id: str, current_user: CurrentUser) -> IngestResponse:
    """Index a resume's text into the vector store."""
    return await rag_service.ingest_resume(current_user.id, resume_id)


@router.post("/ingest/job/{job_id}", response_model=IngestResponse)
async def ingest_job(job_id: str, current_user: CurrentUser) -> IngestResponse:
    """Index a job description's text into the vector store."""
    return await rag_service.ingest_job(current_user.id, job_id)


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest, current_user: CurrentUser) -> QueryResponse:
    """Answer a question grounded in the user's indexed documents."""
    return await rag_service.query(
        current_user.id, payload.question, k=payload.k, source_types=payload.source_types
    )
