"""RAG component factories (embedder + vector store), driven by settings."""

from __future__ import annotations

import os

from app.core.config import settings
from app.core.logging import get_logger
from app.services.rag.embeddings import LocalEmbedder
from app.services.rag.vector_store import InMemoryVectorStore

logger = get_logger(__name__)

_embedder = None
_vector_store = None


def get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder

    if settings.embedding_provider.lower() == "openai" and settings.openai_api_key:
        try:
            from app.services.rag.embeddings import OpenAIEmbedder

            _embedder = OpenAIEmbedder(settings.openai_api_key, settings.embedding_model_openai)
            logger.info("Using OpenAI embedder: %s", _embedder.name)
            return _embedder
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenAI embedder init failed (%s); using local.", exc)

    _embedder = LocalEmbedder()
    logger.info("Using local embedder: %s", _embedder.name)
    return _embedder


def get_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    try:
        from app.services.rag.vector_store import ChromaVectorStore

        _vector_store = ChromaVectorStore(settings.chroma_persist_dir, settings.chroma_collection)
        logger.info("Using ChromaDB vector store")
        return _vector_store
    except Exception as exc:  # pragma: no cover - chroma optional
        logger.warning("ChromaDB unavailable (%s); using in-memory store.", exc)

    persist_path = os.path.join(settings.chroma_persist_dir, "inmem_store.json")
    _vector_store = InMemoryVectorStore(persist_path=persist_path)
    return _vector_store
