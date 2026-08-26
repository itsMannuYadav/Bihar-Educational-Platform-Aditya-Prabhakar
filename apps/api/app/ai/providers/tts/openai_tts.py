from openai import AsyncOpenAI

# OpenAI TTS voices — alloy is gender-neutral and works well for both Hindi
# and English narration; shimmer is warmer for storytelling mode.
DEFAULT_VOICE = "alloy"


class OpenAITTSProvider:
    def __init__(self, *, api_key: str, model: str = "tts-1", voice: str = DEFAULT_VOICE) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._default_voice = voice

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        response = await self._client.audio.speech.create(
            model=self._model,
            voice=voice or self._default_voice,  # type: ignore[arg-type]
            input=text,
            response_format="mp3",
        )
        # HttpxBinaryResponseContent — `.content` holds the raw bytes after the
        # response is fully received (OpenAI TTS is not a true streaming endpoint
        # at 1–5 minute lengths; the whole file lands in one go).
        return response.content
