from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class ScriptSection(BaseModel):
    heading: str
    script: str
    discussion_prompt: str


class TeachingScriptContent(BaseModel):
    opening: str
    sections: list[ScriptSection]
    closing: str


def build_teaching_script_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
    extra_instructions: str = "",
) -> str:
    return (
        f"Write an actual teaching script a Bihar government-school teacher can read from "
        f"in front of the class for Class {class_grade} {subject_name}, chapter "
        f"'{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "This is a script, not a textbook explanation: use simple, spoken language, build in "
        "natural pauses, and include questions the teacher asks the class to keep them engaged. "
        "Structure it as an opening hook, a few sections (each with its own script text and a "
        "discussion question to ask students), and a closing wrap-up."
        + (f"\n\n{extra_instructions}" if extra_instructions else "")
    )
