from typing import Protocol


class STTProvider(Protocol):
    async def transcribe(
        self, audio: bytes, *, mime_type: str, language_hint: str | None = None
    ) -> str: ...
