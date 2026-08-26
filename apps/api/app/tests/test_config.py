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
