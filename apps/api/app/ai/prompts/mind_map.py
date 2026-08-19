from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class MindMapNode(BaseModel):
    id: str
    label: str
    children: list["MindMapNode"] = []


# `MindMapNode` is itself the response_schema (and, once dumped, exactly the
# `mind_maps.structure` jsonb shape from docs/02-database-schema.md §5 — a
# single root object, not a wrapper) — self-referencing Pydantic v2 models
# resolve their own forward ref automatically, no explicit model_rebuild()
# needed for a same-module reference like this.


def build_mind_map_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
) -> str:
    return (
        f"Build a mind map for Class {class_grade} {subject_name}, chapter '{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "The root node's label should be the chapter name. Break it into the main sub-topics "
        "as children, and break those into key facts/terms one level further where it helps. "
        "Keep it to about 2-3 levels deep — this is a mind map for a classroom wall, not an "
        "exhaustive outline. Give every node a short, unique id."
    )
