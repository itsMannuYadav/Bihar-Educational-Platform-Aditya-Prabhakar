from pydantic import BaseModel

from app.ai.prompts.lesson_plan import LessonPlanContent
from app.db.models.enums import AppLanguage


class FakeLLMProvider:
    """Test double for LLMProvider — no network calls, tracks how many times
    it was invoked so cache-hit tests can assert the LLM wasn't called twice.
    """

    def __init__(self) -> None:
        self.call_count = 0

    async def generate(
        self, prompt: str, *, language: AppLanguage, response_schema: type[BaseModel]
    ) -> BaseModel:
        self.call_count += 1
        if response_schema is LessonPlanContent:
            return LessonPlanContent(
                objectives=["Understand the core idea of the chapter"],
                introduction="A short hook to open the class.",
                core_concepts=["Concept one", "Concept two"],
                classroom_discussion=["Why does this happen?", "Can you think of an example?"],
                assessment=["Short oral quiz on the core concepts"],
                homework="Read the chapter summary and answer question 1.",
            )
        raise NotImplementedError(f"FakeLLMProvider has no canned response for {response_schema}")
