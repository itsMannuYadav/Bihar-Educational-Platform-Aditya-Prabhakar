import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestration.nodes.base import PromptContext, ResourceSpec
from app.ai.prompts.audio import AudioScripts, build_audio_prompt
from app.ai.prompts.lesson_plan import LessonPlanContent, build_lesson_plan_prompt
from app.ai.prompts.mind_map import MindMapOutline, build_mind_map_prompt, to_mind_map_node
from app.ai.prompts.presentation import PresentationOutline, build_presentation_prompt
from app.ai.prompts.questions import QuestionSetContent, build_questions_prompt
from app.ai.prompts.teaching_script import TeachingScriptContent, build_teaching_script_prompt
from app.ai.prompts.worksheet import WorksheetContent, build_worksheet_prompt
from app.db.models.enums import ResourceType
from app.db.repositories.resource_detail_repository import (
    create_mind_map,
    create_presentation,
    create_questions,
    create_worksheet,
)

#: `presentations.slide_count` is constrained to exactly these (schema §5).
PRESENTATION_VERSIONS = (5, 10, 15)


def _grounded(builder):
    """Adapter for every builder that grounds itself in the lesson plan."""

    def build(ctx: PromptContext) -> str:
        return builder(
            chapter_name=ctx.chapter_name,
            subject_name=ctx.subject_name,
            class_grade=ctx.class_grade,
            language=ctx.language,
            lesson_plan_content=ctx.lesson_plan_content,
            extra_instructions=ctx.extra_instructions,
        )

    return build


def _build_lesson_plan(ctx: PromptContext) -> str:
    # The lesson plan is the one resource with nothing to ground itself in —
    # it takes the period length and teaching mode instead.
    return build_lesson_plan_prompt(
        chapter_name=ctx.chapter_name,
        subject_name=ctx.subject_name,
        class_grade=ctx.class_grade,
        language=ctx.language,
        duration_minutes=ctx.duration.value,
        teaching_mode=ctx.teaching_mode.value,
    )


def trim_slides(slides: list[dict], target: int) -> list[dict]:
    """Derives the 5- and 10-slide decks from the generated 15.

    The prompt asks for a deck whose essential content sits in the opening and
    closing slides, so a shorter version drops from the middle rather than
    truncating the ending — a 5-slide deck that stops mid-chapter would be
    useless to a teacher.
    """
    if len(slides) <= target:
        return slides
    head = (target + 1) // 2
    tail = target - head
    return slides[:head] + slides[-tail:]


def _mind_map_content(parsed: BaseModel) -> dict:
    assert isinstance(parsed, MindMapOutline)
    return to_mind_map_node(parsed).model_dump()


def _presentation_content(parsed: BaseModel) -> dict:
    assert isinstance(parsed, PresentationOutline)
    slides = [slide.model_dump() for slide in parsed.slides]
    return {
        "versions": {str(n): trim_slides(slides, n) for n in PRESENTATION_VERSIONS},
    }


async def _persist_questions(db: AsyncSession, resource_id: uuid.UUID, content: dict) -> None:
    await create_questions(db, resource_id=resource_id, questions=content["questions"])


async def _persist_worksheet(db: AsyncSession, resource_id: uuid.UUID, content: dict) -> None:
    await create_worksheet(db, resource_id=resource_id, sections=content["sections"])


async def _persist_mind_map(db: AsyncSession, resource_id: uuid.UUID, content: dict) -> None:
    await create_mind_map(db, resource_id=resource_id, structure=content)


async def _persist_presentation(db: AsyncSession, resource_id: uuid.UUID, content: dict) -> None:
    for n in PRESENTATION_VERSIONS:
        await create_presentation(
            db,
            resource_id=resource_id,
            slide_count=n,
            slides={"slides": content["versions"][str(n)]},
        )


def _describe_question_params(params: dict) -> str:
    """`POST /resources/{id}/regenerate` params → a prompt paragraph
    (docs/03-api-design.md §5: `{difficulty, count, types}`).
    """
    parts: list[str] = []
    if count := params.get("count"):
        parts.append(f"Produce exactly {count} questions.")
    if difficulty := params.get("difficulty"):
        parts.append(f"Every question must be {difficulty} difficulty.")
    if types := params.get("types"):
        parts.append(f"Use only these question types: {', '.join(types)}.")
    return " ".join(parts)


def _describe_worksheet_params(params: dict) -> str:
    if sections := params.get("sections"):
        return f"Produce only these section types, one each: {', '.join(sections)}."
    return ""


def _audio_content(parsed: BaseModel) -> dict:
    assert isinstance(parsed, AudioScripts)
    return {
        "variants": {
            "1": parsed.one_minute,
            "3": parsed.three_minutes,
            "5": parsed.five_minutes,
        }
    }


def _build_audio(ctx: PromptContext) -> str:
    return build_audio_prompt(
        chapter_name=ctx.chapter_name,
        subject_name=ctx.subject_name,
        class_grade=ctx.class_grade,
        language=ctx.language,
        lesson_plan_content=ctx.lesson_plan_content,
        extra_instructions=ctx.extra_instructions,
    )


RESOURCE_SPECS: dict[ResourceType, ResourceSpec] = {
    ResourceType.lesson_plan: ResourceSpec(
        resource_type=ResourceType.lesson_plan,
        response_schema=LessonPlanContent,
        build_prompt=_build_lesson_plan,
        to_content=lambda parsed: parsed.model_dump(),
    ),
    ResourceType.teaching_script: ResourceSpec(
        resource_type=ResourceType.teaching_script,
        response_schema=TeachingScriptContent,
        build_prompt=_grounded(build_teaching_script_prompt),
        to_content=lambda parsed: parsed.model_dump(),
    ),
    ResourceType.questions: ResourceSpec(
        resource_type=ResourceType.questions,
        response_schema=QuestionSetContent,
        build_prompt=_grounded(build_questions_prompt),
        to_content=lambda parsed: parsed.model_dump(),
        persist_details=_persist_questions,
        describe_params=_describe_question_params,
    ),
    ResourceType.worksheet: ResourceSpec(
        resource_type=ResourceType.worksheet,
        response_schema=WorksheetContent,
        build_prompt=_grounded(build_worksheet_prompt),
        to_content=lambda parsed: parsed.model_dump(),
        persist_details=_persist_worksheet,
        describe_params=_describe_worksheet_params,
    ),
    ResourceType.mind_map: ResourceSpec(
        resource_type=ResourceType.mind_map,
        response_schema=MindMapOutline,
        build_prompt=_grounded(build_mind_map_prompt),
        # Folds the flat three-level generation shape back into the recursive
        # `mind_maps.structure` jsonb — see mind_map.py for why they differ.
        to_content=_mind_map_content,
        persist_details=_persist_mind_map,
    ),
    ResourceType.presentation: ResourceSpec(
        resource_type=ResourceType.presentation,
        response_schema=PresentationOutline,
        build_prompt=_grounded(build_presentation_prompt),
        to_content=_presentation_content,
        persist_details=_persist_presentation,
    ),
    ResourceType.audio: ResourceSpec(
        resource_type=ResourceType.audio,
        response_schema=AudioScripts,
        build_prompt=_build_audio,
        to_content=_audio_content,
        # Audio scripts ground themselves in the lesson plan, same as the other
        # resource types, but the node also needs lesson_plan_content in context
        # — that's already wired in run_resource_node for non-lesson-plan types.
    ),
}
