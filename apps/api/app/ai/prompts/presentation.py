from typing import Literal

from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class Slide(BaseModel):
    # Provider-agnostic shape from docs/01-architecture.md §4 — both the
    # native PPTX renderer (when it lands) and a future CanvaExportProvider
    # consume this same structure.
    layout: Literal["title", "bullets", "diagram", "image_caption"]
    title: str
    body: list[str] = []
    speaker_notes: str = ""


class PresentationOutline(BaseModel):
    slides: list[Slide]


def build_presentation_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
    extra_instructions: str = "",
) -> str:
    return (
        f"Design a 15-slide classroom presentation outline for Class {class_grade} "
        f"{subject_name}, chapter '{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "Slide 1 must be a title slide. Use a mix of layouts (bullets, diagram, image_caption) "
        "for the rest, ordered so the deck can be trimmed to a shorter version by dropping "
        "slides from the middle without losing the story — keep the most essential content in "
        "the first few and last couple of slides. Every slide needs short speaker notes with "
        "what the teacher should say." + (f"\n\n{extra_instructions}" if extra_instructions else "")
    )
