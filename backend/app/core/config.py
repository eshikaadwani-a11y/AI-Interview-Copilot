"""Application configuration.

Centralised, validated settings loaded from environment variables (and an
optional ``.env`` file). Using ``pydantic-settings`` gives us type coercion,
defaults, and a single source of truth that the whole app imports.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    app_name: str = "AI Interview Copilot"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = "/api/v1"

    # ── Server ────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── CORS ──────────────────────────────────────────────────
    # Stored as a plain string (comma-separated) to avoid pydantic-settings'
    # automatic JSON decoding of list-typed env vars (which fails on a non-JSON
    # value like "http://localhost:3000"). Use ``cors_origins_list`` to read it.
    cors_origins: str = Field(default="http://localhost:3000")

    # ── MongoDB ───────────────────────────────────────────────
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="ai_interview_copilot")

    # ── Security / JWT ────────────────────────────────────────
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # ── Vector store (Chroma) ─────────────────────────────────
    chroma_persist_dir: str = Field(default="./.chroma")
    chroma_collection: str = Field(default="aic_documents")

    # ── Embeddings ────────────────────────────────────────────
    # "local" uses a dependency-free hashing embedder (offline friendly);
    # "openai" uses the OpenAI embeddings API when a key is present.
    embedding_provider: str = Field(default="local")
    embedding_model_local: str = "local-hash-256"
    embedding_model_openai: str = "text-embedding-3-small"

    # ── LLM providers ─────────────────────────────────────────
    # "auto" picks the first provider with a configured key,
    # otherwise falls back to a deterministic local engine.
    llm_provider: str = Field(default="auto")
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # ── ML model registry ─────────────────────────────────────
    models_dir: str = Field(default="./models")

    # ── Uploads ───────────────────────────────────────────────
    upload_dir: str = Field(default="./uploads")
    max_upload_mb: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (single load per process)."""
    return Settings()


settings = get_settings()
