import io

from openai import AsyncOpenAI

_LANG_MAP: dict[str, str | None] = {
    "en": "en",
    "hi": "hi",
    # Hinglish is a code-switch mix; let Whisper auto-detect rather than
    # forcing Hindi and dropping the English half of the utterance.
    "hinglish": None,
}


class WhisperProvider:
    def __init__(self, *, api_key: str, model: str = "whisper-1") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def transcribe(
        self, audio: bytes, *, mime_type: str, language_hint: str | None = None
    ) -> str:
        iso_lang = _LANG_MAP.get(language_hint or "", None) if language_hint else None
        ext = "webm" if "webm" in mime_type else "mp4" if "mp4" in mime_type else "wav"
        file_tuple = (f"audio.{ext}", io.BytesIO(audio), mime_type)
        kwargs: dict = {"model": self._model, "file": file_tuple}
        if iso_lang:
            kwargs["language"] = iso_lang
        result = await self._client.audio.transcriptions.create(**kwargs)
        return result.text
