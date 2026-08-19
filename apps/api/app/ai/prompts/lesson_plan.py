from pydantic import BaseModel

from app.db.models.enums import AppLanguage

# Bilingual generation is a first-class parameter, not a translation
# post-process (docs/01-architecture.md §5) — each language gets its own
# register instruction rather than "write in English then translate."
_LANGUAGE_INSTRUCTIONS: dict[AppLanguage, str] = {
    AppLanguage.en: "Write entirely in clear, simple English suitable for a government-school classroom.",
    AppLanguage.hi: "पूरी सामग्री शुद्ध, सरल हिंदी में लिखें, जैसा एक सरकारी स्कूल का शिक्षक बोलता है।",
    AppLanguage.hinglish: (
        "Write in Hinglish — natural code-mixed Hindi-English in Roman script, the way "
        "Bihar teachers actually speak in class. This is not a translation of English; "
        "write directly in this register."
    ),
}


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
        f"{_LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "Produce a practical, classroom-ready lesson plan — not a textbook summary. Include: "
        "learning objectives, a short introduction/hook, the core concepts to cover, "
        "classroom discussion questions to keep students engaged, an assessment approach, "
        "and homework."
    )
