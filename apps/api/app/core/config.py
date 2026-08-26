import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Shiksha Sathi API"
    environment: Literal["local", "staging", "production"] = "local"

    # NoDecode: pydantic-settings' default env parsing for list[str] fields
    # runs the raw env var through json.loads() before this ever sees it, so
    # a dashboard-entered value like `https://foo.vercel.app` (a valid,
    # obvious thing to type, just not JSON) crashes the app on startup with
    # an opaque JSONDecodeError instead of a config error. The validator
    # below accepts both a JSON array (`["a","b"]`, what .env.example uses)
    # and a plain comma-separated string (what's easiest to type into a
    # platform's env var dashboard) or a single bare origin.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        raise TypeError(f"cors_origins must be a list or string, got {type(value)!r}")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shiksha_sathi"

    @field_validator("database_url", mode="after")
    @classmethod
    def _require_asyncpg_driver(cls, value: str) -> str:
        # Supabase (and every other host) hands out a plain `postgresql://`
        # or `postgres://` connection string — the natural thing to paste
        # into a dashboard env var. SQLAlchemy then defaults to the sync
        # psycopg2 driver, which isn't even installed (this app is
        # async-only), and create_async_engine() dies with
        # `ModuleNotFoundError: No module named 'psycopg2'` instead of a
        # clear "wrong driver" error. Every code path here uses
        # create_async_engine, so silently normalizing to +asyncpg is
        # correct, not just convenient — there's no case where the bare
        # scheme was the actually-intended driver.
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

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
