from typing import Protocol


class TTSProvider(Protocol):
    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes: ...
