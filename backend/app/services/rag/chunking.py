"""Token-aware (word-based) text chunking with overlap.

Splitting on words with a sliding overlap keeps related context together and
preserves continuity across chunk boundaries, which improves retrieval recall.
Pure standard library.
"""

from __future__ import annotations

import re
from typing import List

_WORD_RE = re.compile(r"\S+")


def chunk_text(text: str, chunk_size: int = 180, overlap: int = 40) -> List[str]:
    """Split text into overlapping word chunks.

    Args:
        text: input text.
        chunk_size: target words per chunk.
        overlap: words shared between consecutive chunks.
    """
    if not text or not text.strip():
        return []
    if overlap >= chunk_size:
        overlap = chunk_size // 3

    words = _WORD_RE.findall(text)
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks: List[str] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks
