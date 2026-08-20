from pydantic import BaseModel

from app.ai.prompts.context import lesson_plan_summary
from app.ai.prompts.language import LANGUAGE_INSTRUCTIONS
from app.db.models.enums import AppLanguage


class MindMapNode(BaseModel):
    """The stored shape: `mind_maps.structure` jsonb from
    docs/02-database-schema.md section 5 — a single root object, arbitrarily
    nested. This is what readers (API, frontend canvas) consume.
    """

    id: str
    label: str
    children: list["MindMapNode"] = []


# What we actually *ask the model for* is the flattened three-level form below,
# not MindMapNode. A self-referencing schema is legal Pydantic and legal JSON
# Schema, but Gemini handles the recursive $ref badly in structured-output mode:
# asked for a 3-level map it returned a 3-node tree with two duplicate labels
# and no grandchildren at all. Naming each level explicitly gets a properly
# grouped map, and `to_mind_map_node` folds it back into the recursive shape so
# nothing downstream knows the difference.


class MindMapLeaf(BaseModel):
    id: str
    label: str


class MindMapBranch(BaseModel):
    id: str
    label: str
    key_points: list[MindMapLeaf]


class MindMapOutline(BaseModel):
    id: str
    label: str
    sub_topics: list[MindMapBranch]


def to_mind_map_node(outline: MindMapOutline) -> MindMapNode:
    return MindMapNode(
        id=outline.id,
        label=outline.label,
        children=[
            MindMapNode(
                id=branch.id,
                label=branch.label,
                children=[MindMapNode(id=leaf.id, label=leaf.label) for leaf in branch.key_points],
            )
            for branch in outline.sub_topics
        ],
    )


def build_mind_map_prompt(
    *,
    chapter_name: str,
    subject_name: str,
    class_grade: int,
    language: AppLanguage,
    lesson_plan_content: dict,
    extra_instructions: str = "",
) -> str:
    return (
        f"Build a mind map for Class {class_grade} {subject_name}, chapter '{chapter_name}'.\n\n"
        f"{lesson_plan_summary(lesson_plan_content)}\n\n"
        f"{LANGUAGE_INSTRUCTIONS[language]}\n\n"
        "The root label is the chapter name. Give it 4 to 6 sub-topics, and give each sub-topic "
        "2 to 4 key points of its own — the grouping into sub-topics is what makes this "
        "readable on a classroom wall, so never leave a sub-topic with no key points, and never "
        "repeat a label. Keep every label to a few words, and give every node a short, unique id."
        + (f"\n\n{extra_instructions}" if extra_instructions else "")
    )
