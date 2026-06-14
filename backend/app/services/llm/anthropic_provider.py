"""Anthropic (Claude) provider (lazy import)."""

from __future__ import annotations


class AnthropicProvider:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        import anthropic  # lazy

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.name = f"anthropic-{model}"

    def generate(self, system: str, prompt: str, *, max_tokens: int = 800) -> str:
        message = self._client.messages.create(
            model=self.model,
            system=system,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
        return "".join(parts)
