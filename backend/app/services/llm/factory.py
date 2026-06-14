"""LLM provider factory.

Selects a provider based on settings and key availability:
    - ``llm_provider="openai"`` / ``"anthropic"`` force that vendor (if keyed)
    - ``"auto"`` picks the first vendor with a configured key
    - otherwise (or on any import/credential failure) falls back to the local
      deterministic engine, so the app always has a working provider.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.local_provider import LocalLLMProvider

logger = get_logger(__name__)

_provider = None


def _build():
    choice = (settings.llm_provider or "auto").lower()

    def try_openai():
        if settings.openai_api_key:
            from app.services.llm.openai_provider import OpenAIProvider

            return OpenAIProvider(settings.openai_api_key, settings.openai_model)
        return None

    def try_anthropic():
        if settings.anthropic_api_key:
            from app.services.llm.anthropic_provider import AnthropicProvider

            return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
        return None

    try:
        if choice == "openai":
            provider = try_openai()
        elif choice == "anthropic":
            provider = try_anthropic()
        elif choice == "local":
            provider = None
        else:  # auto
            provider = try_openai() or try_anthropic()
        if provider is not None:
            logger.info("Using LLM provider: %s", provider.name)
            return provider
    except Exception as exc:  # pragma: no cover - credential/env dependent
        logger.warning("LLM provider init failed (%s); falling back to local.", exc)

    logger.info("Using local extractive LLM provider (offline).")
    return LocalLLMProvider()


def get_llm_provider():
    global _provider
    if _provider is None:
        _provider = _build()
    return _provider
