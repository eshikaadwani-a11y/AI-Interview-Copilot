"""LLM provider interface.

All providers implement ``generate(system, prompt) -> str``. This single,
narrow interface lets the RAG service, mentor, and feedback features swap
between OpenAI, Anthropic, and the deterministic local engine transparently.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def generate(self, system: str, prompt: str, *, max_tokens: int = 800) -> str:
        """Return a completion for the given system + user prompt."""
        ...
