from typing import Protocol

from pydantic import BaseModel

from app.db.models.enums import AppLanguage


class LLMProvider(Protocol):
    async def generate(
        self, prompt: str, *, language: AppLanguage, response_schema: type[BaseModel]
    ) -> BaseModel: ...
