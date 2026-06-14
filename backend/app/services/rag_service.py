"""RAG orchestration service.

Pipeline:
    ingest:  text -> chunk -> embed -> upsert into the vector store (with
             per-user, per-source metadata)
    query:   question -> embed -> retrieve top-k (user-scoped) -> assemble a
             grounded prompt -> LLM provider -> answer + citations

The embedder, vector store, and LLM provider are resolved via factories so the
same logic runs offline (local embedder + in-memory store + local engine) or in
production (OpenAI/Chroma) with no code change.
"""

from __future__ import annotations

from typing import List, Optional

from app.core.logging import get_logger
from app.models.rag import Citation, IngestResponse, QueryResponse
from app.services import job_service, resume_service
from app.services.llm.factory import get_llm_provider
from app.services.rag.chunking import chunk_text
from app.services.rag.factory import get_embedder, get_vector_store

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are an AI interview-prep mentor. Answer the user's question using ONLY "
    "the provided context from their resume and the job description. Be concise, "
    "specific, and actionable. If the context does not contain the answer, say so "
    "honestly rather than inventing details."
)


async def ingest_resume(user_id: str, resume_id: str) -> IngestResponse:
    filename, raw_text = await resume_service.get_resume_text(user_id, resume_id)
    count = _index(user_id, "resume", resume_id, filename, raw_text)
    return IngestResponse(
        source_type="resume", source_id=resume_id, title=filename, indexed_chunks=count
    )


async def ingest_job(user_id: str, job_id: str) -> IngestResponse:
    title, raw_text = await job_service.get_job_text(user_id, job_id)
    count = _index(user_id, "job", job_id, title, raw_text)
    return IngestResponse(
        source_type="job", source_id=job_id, title=title, indexed_chunks=count
    )


def _index(user_id: str, source_type: str, source_id: str, title: str, text: str) -> int:
    """Chunk, embed, and upsert a document into the vector store."""
    store = get_vector_store()
    embedder = get_embedder()

    # Replace any previous chunks for this source (idempotent re-ingest).
    store.delete({"user_id": user_id, "source_id": source_id})

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = embedder.embed_batch(chunks)
    ids = [f"{user_id}:{source_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "user_id": user_id,
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    store.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    logger.info("Indexed %d chunks for %s %s", len(chunks), source_type, source_id)
    return len(chunks)


async def query(
    user_id: str,
    question: str,
    k: int = 5,
    source_types: Optional[List[str]] = None,
) -> QueryResponse:
    store = get_vector_store()
    embedder = get_embedder()
    provider = get_llm_provider()

    query_emb = embedder.embed(question)
    # Retrieve a few extra to allow optional source-type filtering.
    raw_hits = store.query(query_emb, k=k * 2, where={"user_id": user_id})
    if source_types:
        wanted = set(source_types)
        raw_hits = [h for h in raw_hits if h["metadata"].get("source_type") in wanted]
    hits = raw_hits[:k]

    if not hits:
        return QueryResponse(
            answer=(
                "I couldn't find anything relevant in your indexed documents. "
                "Make sure you've ingested your resume and the job description."
            ),
            provider=provider.name,
            citations=[],
        )

    context_blocks = []
    citations: List[Citation] = []
    for hit in hits:
        meta = hit["metadata"]
        doc = hit["document"]
        context_blocks.append(f"[{meta.get('source_type')}: {meta.get('title')}]\n{doc}")
        citations.append(
            Citation(
                source_type=meta.get("source_type", "unknown"),
                source_id=meta.get("source_id", ""),
                title=meta.get("title"),
                snippet=doc[:240] + ("…" if len(doc) > 240 else ""),
                score=hit["score"],
            )
        )

    context = "\n\n".join(context_blocks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = provider.generate(_SYSTEM_PROMPT, prompt)

    return QueryResponse(answer=answer, provider=provider.name, citations=citations)
