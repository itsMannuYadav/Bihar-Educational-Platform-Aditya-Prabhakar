from pydantic import BaseModel

from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class LessonPlanContent(BaseModel):
    objectives: list[str]
    introduction: str
    core_concepts: list[str]
    classroom_discussion: list[str]
    assessment: list[str]
    homework: str


def build_lesson_plan_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    duration_minutes: str,
    teaching_mode: str,
) -> str:
    return (
        f"You are helping a government-school teacher in Bihar prepare a lesson plan for "
        f"Class {class_grade} {subject_name}, chapter '{chapter_name}'.\n"
        f"The class period is {duration_minutes} minutes. Teaching style: {teaching_mode}.\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "Produce a practical, classroom-ready lesson plan — not a textbook summary. Include: "
        "learning objectives, a short introduction/hook, the core concepts to cover, "
        "classroom discussion questions to keep students engaged, an assessment approach, "
        "and homework."
    )
