from openai import AsyncOpenAI
from pydantic import BaseModel

from app.db.models.enums import AppLanguage


class OpenAIProvider:
    """LLMProvider backed by OpenAI's Responses API structured-output mode
    (`responses.parse` / `.output_parsed`) — verified against the installed
    SDK version rather than assumed, since this surface has moved before.
    """

    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self, prompt: str, *, language: AppLanguage, response_schema: type[BaseModel]
    ) -> BaseModel:
        response = await self._client.responses.parse(
            model=self._model,
            input=prompt,
            text_format=response_schema,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI response did not include parsed structured output")
        return parsed
