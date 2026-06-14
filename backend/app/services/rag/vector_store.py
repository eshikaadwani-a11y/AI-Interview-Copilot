"""Vector stores for RAG.

``InMemoryVectorStore`` is a dependency-free store with JSON persistence and
cosine-similarity search + metadata filtering. It runs anywhere and is the
sandbox default.

``ChromaVectorStore`` wraps a persistent ChromaDB collection (lazy import) and
is used in production. Both share the same interface so the RAG service is
agnostic to the backend.
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Optional, Protocol


class VectorStore(Protocol):
    name: str

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict],
    ) -> None: ...

    def query(
        self, embedding: List[float], k: int, where: Optional[dict] = None
    ) -> List[dict]: ...

    def delete(self, where: dict) -> None: ...


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _matches(metadata: dict, where: Optional[dict]) -> bool:
    if not where:
        return True
    return all(metadata.get(key) == value for key, value in where.items())


class InMemoryVectorStore:
    """In-memory vector store with optional JSON persistence."""

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self.name = "in-memory"
        self._persist_path = persist_path
        self._items: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self._persist_path and os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r", encoding="utf-8") as fh:
                    self._items = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._items = {}

    def _save(self) -> None:
        if not self._persist_path:
            return
        os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
        with open(self._persist_path, "w", encoding="utf-8") as fh:
            json.dump(self._items, fh)

    def add(self, ids, embeddings, documents, metadatas) -> None:
        for id_, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self._items[id_] = {"embedding": emb, "document": doc, "metadata": meta}
        self._save()

    def query(self, embedding, k=5, where=None) -> List[dict]:
        scored = []
        for id_, item in self._items.items():
            if not _matches(item["metadata"], where):
                continue
            score = _cosine(embedding, item["embedding"])
            scored.append(
                {
                    "id": id_,
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "score": round(score, 4),
                }
            )
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]

    def delete(self, where) -> None:
        to_delete = [id_ for id_, item in self._items.items() if _matches(item["metadata"], where)]
        for id_ in to_delete:
            self._items.pop(id_, None)
        self._save()

    def count(self) -> int:
        return len(self._items)


class ChromaVectorStore:
    """Persistent ChromaDB-backed vector store (production)."""

    def __init__(self, persist_dir: str, collection: str) -> None:
        import chromadb  # lazy

        self.name = "chromadb"
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    def add(self, ids, embeddings, documents, metadatas) -> None:
        self._collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(self, embedding, k=5, where=None) -> List[dict]:
        result = self._collection.query(
            query_embeddings=[embedding], n_results=k, where=where or None
        )
        out: List[dict] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for i in range(len(ids)):
            out.append(
                {
                    "id": ids[i],
                    "document": docs[i],
                    "metadata": metas[i],
                    "score": round(1.0 - float(dists[i]), 4),  # cosine distance -> similarity
                }
            )
        return out

    def delete(self, where) -> None:
        self._collection.delete(where=where)
