from langchain_core.runnables import RunnableConfig

from app.ai.orchestration.state import ResourceResult, TeachingKitState
from app.ai.prompts.lesson_plan import LessonPlanContent, build_lesson_plan_prompt
from app.ai.providers.llm.base import LLMProvider
from app.cache.keys import compute_cache_key
from app.cache.service import get_cached, record_cache_hit, write_cache
from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode
from app.db.repositories.curriculum_repository import (
    get_chapter_by_id,
    get_class_by_id,
    get_subject_by_id,
)
from app.db.repositories.teaching_kit_repository import (
    create_generated_resource,
    get_generated_resource,
)


async def generate_lesson_plan_node(state: TeachingKitState, config: RunnableConfig) -> dict:
    configurable = config["configurable"]
    db = configurable["db"]
    llm_provider: LLMProvider = configurable["llm_provider"]

    language = AppLanguage(state["language"])
    duration = DurationOption(state["duration"])
    teaching_mode = TeachingMode(state["teaching_mode"])

    cache_key = compute_cache_key(
        class_id=state["class_id"],
        subject_id=state["subject_id"],
        chapter_id=state["chapter_id"],
        language=language,
        duration=duration,
        teaching_mode=teaching_mode,
        resource_type=ResourceType.lesson_plan,
        params={},
    )

    cached = await get_cached(db, cache_key)
    if cached is not None:
        canonical = await get_generated_resource(db, cached.canonical_resource_id)
        if canonical is None:
            raise RuntimeError(f"resource_cache {cached.id} points at a missing generated_resource")
        resource = await create_generated_resource(
            db,
            request_id=state["request_id"],
            resource_type=ResourceType.lesson_plan,
            content=canonical.content,
            language=language,
            cache_id=cached.id,
            file_url=canonical.file_url,
        )
        await record_cache_hit(db, cached)
        return {
            "resources": [
                ResourceResult(
                    resource_type=ResourceType.lesson_plan.value,
                    resource_id=resource.id,
                    cache_hit=True,
                )
            ]
        }

    chapter = await get_chapter_by_id(db, state["chapter_id"])
    subject = await get_subject_by_id(db, state["subject_id"])
    school_class = await get_class_by_id(db, state["class_id"])
    if chapter is None or subject is None or school_class is None:
        raise ValueError("teaching-kit request references a curriculum entity that no longer exists")

    prompt = build_lesson_plan_prompt(
        chapter_name=chapter.name,
        subject_name=subject.name,
        class_grade=school_class.grade,
        language=language,
        duration_minutes=duration.value,
        teaching_mode=teaching_mode.value,
    )
    content = await llm_provider.generate(prompt, language=language, response_schema=LessonPlanContent)

    resource = await create_generated_resource(
        db,
        request_id=state["request_id"],
        resource_type=ResourceType.lesson_plan,
        content=content.model_dump(),
        language=language,
    )
    await write_cache(
        db,
        cache_key=cache_key,
        class_id=state["class_id"],
        subject_id=state["subject_id"],
        chapter_id=state["chapter_id"],
        language=language,
        resource_type=ResourceType.lesson_plan,
        params={},
        canonical_resource_id=resource.id,
    )
    return {
        "resources": [
            ResourceResult(
                resource_type=ResourceType.lesson_plan.value, resource_id=resource.id, cache_hit=False
            )
        ]
    }
