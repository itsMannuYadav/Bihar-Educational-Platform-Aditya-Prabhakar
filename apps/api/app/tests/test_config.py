import pytest

from app.core.config import Settings


def test_cors_origins_accepts_json_array(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["https://a.example.com", "https://b.example.com"]')

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_accepts_comma_separated_string(monkeypatch: pytest.MonkeyPatch) -> None:
    # The easy, obvious thing to type into a platform's env var dashboard —
    # not valid JSON, which used to crash the app on startup with an opaque
    # JSONDecodeError instead of just... working.
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.com, https://b.example.com")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_accepts_single_bare_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://shiksha-sathi.vercel.app")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.cors_origins == ["https://shiksha-sathi.vercel.app"]


def test_cors_origins_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.cors_origins == ["http://localhost:3000"]


def test_database_url_adds_asyncpg_driver_to_bare_postgresql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The connection string a host actually hands out — the app is
    # async-only, so a bare `postgresql://` used to reach
    # create_async_engine() and blow up on the sync psycopg2 driver, which
    # isn't even installed.
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"


def test_database_url_adds_asyncpg_driver_to_bare_postgres(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pw@host:5432/db")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"


def test_database_url_leaves_explicit_driver_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pw@host:5432/db")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"
