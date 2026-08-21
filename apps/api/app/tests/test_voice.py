import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import get_stt_provider
from app.main import app


class FakeSTTProvider:
    def __init__(self, text: str = "photosynthesis Class 8 Science") -> None:
        self.call_count = 0
        self._text = text

    async def transcribe(
        self, audio: bytes, *, mime_type: str, language_hint: str | None = None
    ) -> str:
        self.call_count += 1
        return self._text


@pytest.fixture
def stt_provider() -> FakeSTTProvider:
    return FakeSTTProvider()


@pytest.fixture
def client_with_stt(client: TestClient, stt_provider: FakeSTTProvider) -> TestClient:
    app.dependency_overrides[get_stt_provider] = lambda: stt_provider
    yield client
    # clear is handled by the parent `client` fixture's finally block,
    # but we still remove our own override to be safe
    app.dependency_overrides.pop(get_stt_provider, None)


def test_transcribe_returns_text(client_with_stt: TestClient, stt_provider: FakeSTTProvider) -> None:  # noqa: E501
    res = client_with_stt.post(
        "/api/v1/voice/transcribe",
        files={"file": ("recording.webm", b"\x1aFake audio bytes", "audio/webm")},
    )
    assert res.status_code == 200
    assert res.json() == {"text": "photosynthesis Class 8 Science"}
    assert stt_provider.call_count == 1


def test_transcribe_passes_language_hint(
    client_with_stt: TestClient, stt_provider: FakeSTTProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[str | None] = []
    original_transcribe = stt_provider.transcribe

    async def capturing_transcribe(
        audio: bytes, *, mime_type: str, language_hint: str | None = None
    ) -> str:
        captured.append(language_hint)
        return await original_transcribe(audio, mime_type=mime_type, language_hint=language_hint)

    monkeypatch.setattr(stt_provider, "transcribe", capturing_transcribe)

    res = client_with_stt.post(
        "/api/v1/voice/transcribe?language=hi",
        files={"file": ("recording.webm", b"\x1aFake audio bytes", "audio/webm")},
    )
    assert res.status_code == 200
    assert captured == ["hi"]


def test_transcribe_rejects_empty_file(client_with_stt: TestClient) -> None:
    res = client_with_stt.post(
        "/api/v1/voice/transcribe",
        files={"file": ("recording.webm", b"", "audio/webm")},
    )
    assert res.status_code == 422


def test_transcribe_rejects_non_audio(client_with_stt: TestClient) -> None:
    res = client_with_stt.post(
        "/api/v1/voice/transcribe",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert res.status_code == 422


def test_transcribe_large_file_rejected(client_with_stt: TestClient) -> None:
    """Files over the 25 MB limit should get a 413."""
    big = b"\x00" * (25 * 1024 * 1024 + 1)
    res = client_with_stt.post(
        "/api/v1/voice/transcribe",
        files={"file": ("recording.webm", big, "audio/webm")},
    )
    assert res.status_code == 413
