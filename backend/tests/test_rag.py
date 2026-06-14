"""Tests for the RAG building blocks (pure-stdlib components)."""

from __future__ import annotations

from app.services.llm.local_provider import LocalLLMProvider
from app.services.rag.chunking import chunk_text
from app.services.rag.embeddings import LocalEmbedder
from app.services.rag.vector_store import InMemoryVectorStore


def _cosine(a, b):
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def test_chunking_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # Short text returns a single chunk.
    assert len(chunk_text("just a few words")) == 1
    assert chunk_text("") == []


def test_embedder_is_deterministic_and_normalized() -> None:
    emb = LocalEmbedder(dim=128)
    v1 = emb.embed("python fastapi backend")
    v2 = emb.embed("python fastapi backend")
    assert v1 == v2
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-6  # L2 normalized


def test_embedder_similarity_orders_by_relevance() -> None:
    emb = LocalEmbedder()
    query = emb.embed("machine learning with pytorch")
    related = emb.embed("we use pytorch for deep learning models")
    unrelated = emb.embed("the chef cooked a delicious pasta dinner")
    assert _cosine(query, related) > _cosine(query, unrelated)


def test_vector_store_query_filter_and_delete() -> None:
    emb = LocalEmbedder()
    store = InMemoryVectorStore()
    docs = ["python fastapi service", "react frontend app", "kubernetes on aws"]
    store.add(
        ids=["a", "b", "c"],
        embeddings=emb.embed_batch(docs),
        documents=docs,
        metadatas=[
            {"user_id": "u1", "source_id": "r1"},
            {"user_id": "u1", "source_id": "r1"},
            {"user_id": "u2", "source_id": "r2"},
        ],
    )
    # User scoping via metadata filter.
    hits = store.query(emb.embed("python api"), k=5, where={"user_id": "u1"})
    assert len(hits) == 2
    assert all(h["metadata"]["user_id"] == "u1" for h in hits)
    assert hits[0]["document"] == "python fastapi service"

    store.delete({"user_id": "u1", "source_id": "r1"})
    assert store.count() == 1


def test_local_provider_extracts_relevant_sentence() -> None:
    llm = LocalLLMProvider()
    context = (
        "The candidate knows Python and FastAPI. "
        "They deployed services on AWS with Kubernetes. "
        "They enjoy hiking on weekends."
    )
    answer = llm.generate("system", f"Context:\n{context}\n\nQuestion: What cloud skills?")
    assert "AWS" in answer or "Kubernetes" in answer
