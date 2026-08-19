from typing import Literal

from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class FillBlankItem(BaseModel):
    text: str  # sentence with the blank marked as ____
    answer: str


class TrueFalseItem(BaseModel):
    statement: str
    is_true: bool


class MatchItem(BaseModel):
    left: str
    right: str


class WorksheetSection(BaseModel):
    type: Literal["fill_blank", "true_false", "match"]
    # Only the list matching `type` should be populated; the schema is a flat
    # discriminated shape (not `items: list[dict]`) so it stays strict-mode
    # compatible for OpenAI structured output.
    fill_blank_items: list[FillBlankItem] = []
    true_false_items: list[TrueFalseItem] = []
    match_items: list[MatchItem] = []


class WorksheetContent(BaseModel):
    sections: list[WorksheetSection]


def build_worksheet_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
) -> str:
    return (
        f"Write a printable worksheet for Class {class_grade} {subject_name}, chapter "
        f"'{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "Produce three sections, one of each type: a fill-in-the-blanks section (5 items), "
        "a true/false section (5 statements), and a match-the-following section (5 pairs). "
        "For each section, populate only the item list matching its type and leave the other "
        "two empty."
    )
