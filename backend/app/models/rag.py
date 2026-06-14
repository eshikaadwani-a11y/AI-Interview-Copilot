"""RAG request/response models."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    source_type: str
    source_id: str
    title: Optional[str] = None
    indexed_chunks: int


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    k: int = Field(default=5, ge=1, le=20)
    source_types: Optional[List[str]] = None  # e.g. ["resume", "job"]


class Citation(BaseModel):
    source_type: str
    source_id: str
    title: Optional[str] = None
    snippet: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    provider: str
    citations: List[Citation] = Field(default_factory=list)
