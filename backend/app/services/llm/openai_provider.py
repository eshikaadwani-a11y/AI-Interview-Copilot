"""OpenAI chat completion provider (lazy import)."""

from __future__ import annotations


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI  # lazy

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.name = f"openai-{model}"

    def generate(self, system: str, prompt: str, *, max_tokens: int = 800) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""
