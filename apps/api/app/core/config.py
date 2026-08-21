from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Shiksha Sathi API"
    environment: Literal["local", "staging", "production"] = "local"

    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shiksha_sathi"

    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""

    llm_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    # Caps how many generations one kit fires at once. The Gemini free tier
    # allows 5 requests/minute, and a kit fans out 6 - so an unbounded kit
    # exhausts the quota before its first resource lands. Raise this on a
    # paid tier, where the fan-out is the whole point of the graph.
    llm_max_concurrency: int = 2

    stt_provider: Literal["whisper"] = "whisper"
    whisper_model: str = "whisper-1"

    tts_provider: Literal["openai"] = "openai"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"

    # Embedding provider — used for semantic cache near-match (Phase 7).
    # Leave EMBEDDING_PROVIDER unset (or set to "none") to disable semantic
    # fallback; the exact-key cache still works fully without it.
    embedding_provider: Literal["openai", "none"] = "none"
    embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
