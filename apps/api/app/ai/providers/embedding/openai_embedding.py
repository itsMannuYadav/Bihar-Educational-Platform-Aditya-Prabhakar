from openai import AsyncOpenAI


class OpenAIEmbeddingProvider:
    """Wraps text-embedding-3-small (1536 dims) — matches Vector(1536) in the
    resource_cache table (docs/02-database-schema.md §4).
    """

    def __init__(self, *, api_key: str, model: str = "text-embedding-3-small") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding
