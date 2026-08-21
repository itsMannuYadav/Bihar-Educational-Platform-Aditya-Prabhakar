import asyncio
import logging
import re

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from app.db.models.enums import AppLanguage

logger = logging.getLogger(__name__)

# A teaching kit fans out 6+ generations at once, so a single overloaded-model
# blip would otherwise fail the whole kit. Both of these are observed against
# the live API, not defensive guesswork: flash returns 503 UNAVAILABLE ("high
# demand") sporadically, and the free tier's per-minute request quota is low
# enough (5 RPM on gemini-3.6-flash) that an unthrottled kit exhausts it before
# the first resource lands.
_RETRY_STATUS = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 5
_BASE_BACKOFF_SECONDS = 2.0
_MAX_BACKOFF_SECONDS = 60.0

# Gemini reports its own wait on a quota error, e.g. "Please retry in 21.1s".
# Honouring it beats guessing: exponential backoff from 2s takes several
# useless round trips to clear a 21-second window.
_RETRY_AFTER_PATTERN = re.compile(r"retry in ([0-9.]+)s", re.IGNORECASE)

# Keywords Gemini uses in its daily-quota error messages.
_DAILY_LIMIT_PATTERN = re.compile(r"per.?day|per_day|\brpd\b|daily", re.IGNORECASE)


def _suggested_delay(exc: genai_errors.APIError) -> float | None:
    match = _RETRY_AFTER_PATTERN.search(str(exc.message or exc))
    if match is None:
        return None
    return min(float(match.group(1)) + 1.0, _MAX_BACKOFF_SECONDS)


def _is_daily_limit(exc: genai_errors.APIError) -> bool:
    msg = str(exc.message or exc)
    if _DAILY_LIMIT_PATTERN.search(msg):
        return True
    # Gemini suggests a very long retry (>1 h) only for daily caps.
    raw_match = _RETRY_AFTER_PATTERN.search(msg)
    return bool(raw_match and float(raw_match.group(1)) > 3600)


class GeminiProvider:
    """LLMProvider backed by the Gemini API's structured-output mode.

    `google-genai` accepts a Pydantic model directly as `response_schema` and
    hands back an instance on `response.parsed`, so this mirrors
    OpenAIProvider's contract exactly - same Protocol, same return type.

    Verified against the installed SDK (google-genai 2.18.1) and live calls:
    the async surface is `client.aio.models`, and `GenerateContentConfig`
    carries both `response_mime_type` and `response_schema`.
    """

    def __init__(self, *, api_key: str, model: str, max_concurrency: int = 2) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        # Per-provider-instance, and one instance is built per request, so this
        # bounds a single kit's fan-out rather than global server throughput.
        # The point is to stay under a per-minute request quota, which retries
        # alone can't do - they only react after the quota is already blown.
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def generate(
        self, prompt: str, *, language: AppLanguage, response_schema: type[BaseModel]
    ) -> BaseModel:
        async with self._semaphore:
            response = await self._generate_with_retry(prompt, response_schema)

        parsed = response.parsed
        if parsed is None:
            finish_reason = (
                response.candidates[0].finish_reason if response.candidates else "no candidates"
            )
            raise RuntimeError(
                f"Gemini returned no parsed structured output (finish reason: {finish_reason})"
            )
        if not isinstance(parsed, response_schema):
            # The SDK returns a list when the schema is a list type; every schema
            # here is a single object model, so anything else is a contract break.
            raise RuntimeError(
                f"Gemini returned {type(parsed).__name__}, expected {response_schema.__name__}"
            )
        return parsed

    async def _generate_with_retry(
        self, prompt: str, response_schema: type[BaseModel]
    ) -> types.GenerateContentResponse:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        for attempt in range(_MAX_ATTEMPTS):
            try:
                return await self._client.aio.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
            except genai_errors.APIError as exc:
                if exc.code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    if exc.code == 429:
                        raise RuntimeError(
                            "RATE_LIMIT_DAILY" if _is_daily_limit(exc) else "RATE_LIMIT_MINUTE"
                        ) from exc
                    raise
                delay = _suggested_delay(exc) or min(
                    _BASE_BACKOFF_SECONDS * (2**attempt), _MAX_BACKOFF_SECONDS
                )
                logger.warning(
                    "Gemini %s returned %s; retrying in %.1fs (attempt %d/%d)",
                    self._model,
                    exc.code,
                    delay,
                    attempt + 1,
                    _MAX_ATTEMPTS,
                )
                await asyncio.sleep(delay)
        raise RuntimeError("unreachable: retry loop exhausted")
