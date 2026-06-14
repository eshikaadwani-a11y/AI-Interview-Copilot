"""Text embedders.

``LocalEmbedder`` is a dependency-free hashing embedder (the "hashing trick"
with signed buckets) that produces deterministic, L2-normalised vectors. It
works fully offline and gives meaningful cosine similarity for token overlap —
ideal for the sandbox and as a fallback.

``OpenAIEmbedder`` calls the OpenAI embeddings API (lazy import) and is used
when a key is configured.

Both expose the same interface: ``embed(text) -> list[float]`` and
``embed_batch(texts) -> list[list[float]]``.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List, Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


@runtime_checkable
class Embedder(Protocol):
    dim: int
    name: str

    def embed(self, text: str) -> List[float]: ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]: ...


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class LocalEmbedder:
    """Deterministic hashing embedder (offline)."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim
        self.name = f"local-hash-{dim}"

    def _tokens(self, text: str) -> List[str]:
        return _TOKEN_RE.findall(text.lower())

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in self._tokens(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        return _l2_normalize(vec)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


class OpenAIEmbedder:
    """OpenAI embeddings (used when an API key is configured)."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        from openai import OpenAI  # lazy

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.name = f"openai-{model}"
        self.dim = 1536  # text-embedding-3-small

    def embed(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]
