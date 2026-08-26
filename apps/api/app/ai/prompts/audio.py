from pydantic import BaseModel

from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class AudioScripts(BaseModel):
    """Three audio narration scripts grounded in the lesson plan.

    Word-count targets that map to the named durations at ~150 wpm:
      one_minute  → ~150 words  (hook + single key concept)
      three_minutes → ~450 words  (all core concepts, one example each)
      five_minutes  → ~750 words  (full narrative + discussion + wrap-up)
    """

    one_minute: str
    three_minutes: str
    five_minutes: str


def build_audio_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
    extra_instructions: str = "",
) -> str:
    lang_note = LANGUAGE_INSTRUCTIONS[language]
    objectives = lesson_plan_content.get("objectives", [])
    core_concepts = lesson_plan_content.get("core_concepts", [])
    intro = lesson_plan_content.get("introduction", "")

    objectives_text = "\n".join(f"- {o}" for o in objectives)
    concepts_text = "\n".join(f"- {c}" for c in core_concepts)

    return (  # noqa: E501
        f'You are writing audio narration scripts for a Class {class_grade} {subject_name} lesson on "{chapter_name}".\n'  # noqa: E501
        "\n"
        "These scripts will be read aloud (text-to-speech) to students. Write them in a warm, teacher-to-student voice — engaging, clear, never textbook-stiff.\n"  # noqa: E501
        "\n"
        f"Lesson context:\nIntroduction: {intro}\nObjectives:\n{objectives_text}\nCore concepts:\n{concepts_text}\n"  # noqa: E501
        "\n"
        f"{lang_note}\n"
        "\n"
        "Produce THREE narration scripts:\n"
        "\n"
        "one_minute (~150 words):\n"
        "  Open with a compelling hook or real-world example. Introduce ONE key concept clearly. End with a curiosity-sparking question.\n"  # noqa: E501
        "\n"
        "three_minutes (~450 words):\n"
        "  Cover ALL core concepts above, one at a time. Use a simple analogy or example per concept. Keep energy high throughout.\n"  # noqa: E501
        "\n"
        "five_minutes (~750 words):\n"
        '  Full narrative: warm opening, all core concepts explained in depth with examples, a short discussion moment ("Think about this…"), and a clear close summarising what was learned.\n'  # noqa: E501
        "\n"
        f"{extra_instructions}\n"
        "\n"
        "Return ONLY the three scripts. No headings, no labels, no extra commentary in the scripts themselves — just the spoken words as they would sound to students.\n"  # noqa: E501
    )
