"""Deterministic local LLM provider (offline fallback).

This is NOT a language model — it is an extractive engine that produces
grounded, useful answers without any external API. It locates the question in
the prompt, scores context sentences by token overlap with the question, and
returns the most relevant sentences. This keeps every LLM-powered feature
demonstrable offline and provides a graceful degradation path in production.
"""

from __future__ import annotations

import re
from typing import List

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_TOKEN_RE = re.compile(r"[a-z0-9+#]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "this", "that", "it", "as", "at",
    "by", "from", "your", "you", "i", "we", "they", "what", "how", "why",
    "do", "does", "can", "should", "would", "my", "me",
}


def _tokens(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP]


class LocalLLMProvider:
    """Extractive, deterministic provider."""

    name = "local-extractive"

    def generate(self, system: str, prompt: str, *, max_tokens: int = 800) -> str:
        question, context = self._split(prompt)
        if not context.strip():
            return (
                "I don't have indexed context to answer that yet. "
                "Try ingesting your resume or the job description first."
            )

        q_tokens = set(_tokens(question))
        sentences = [s.strip() for s in _SENTENCE_RE.split(context) if len(s.strip()) > 20]
        scored = []
        for sent in sentences:
            overlap = len(q_tokens & set(_tokens(sent)))
            if overlap:
                scored.append((overlap, sent))
        scored.sort(key=lambda t: t[0], reverse=True)

        if not scored:
            top = sentences[:3]
        else:
            top = [s for _, s in scored[:4]]

        answer = " ".join(top)
        return (
            "Based on your indexed documents:\n\n"
            + answer
            + "\n\n(Generated offline by the local engine. Configure an LLM API "
            "key for richer, generative answers.)"
        )

    @staticmethod
    def _split(prompt: str) -> tuple[str, str]:
        """Separate the question from the context using known markers."""
        question = ""
        context = prompt
        if "Question:" in prompt:
            context, _, question = prompt.rpartition("Question:")
        if "Context:" in context:
            context = context.split("Context:", 1)[1]
        return question, context
