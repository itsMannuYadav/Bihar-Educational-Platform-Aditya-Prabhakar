from typing import Literal

from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class QuestionOption(BaseModel):
    label: str
    text: str
    is_correct: bool


class QuestionItem(BaseModel):
    type: Literal["mcq", "short_answer", "long_answer", "hots"]
    difficulty: Literal["easy", "moderate", "advanced"]
    question_text: str
    options: list[QuestionOption] | None = None
    answer: str
    explanation: str | None = None


class QuestionSetContent(BaseModel):
    questions: list[QuestionItem]


def build_questions_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
) -> str:
    return (
        f"Write a set of exam-style questions for Class {class_grade} {subject_name}, chapter "
        f"'{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "Produce about 10 questions covering a mix of types (mcq, short_answer, long_answer, "
        "hots — higher-order thinking) and difficulties (easy, moderate, advanced). Every mcq "
        "needs 4 options with exactly one marked correct. Every question needs a model answer; "
        "add a short explanation where it helps a teacher grading student work."
    )
