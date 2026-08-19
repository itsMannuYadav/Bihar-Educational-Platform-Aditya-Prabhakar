import uuid

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestration.nodes.lesson_plan import generate_lesson_plan_node
from app.ai.orchestration.state import TeachingKitState
from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.models.enums import AppLanguage, DurationOption, TeachingMode
from app.tests.fakes import FakeLLMProvider


async def _seed_curriculum(db: AsyncSession) -> tuple[SchoolClass, Subject, Chapter]:
    board = Board(name="BSEB", state="Bihar")
    db.add(board)
    await db.flush()

    school_class = SchoolClass(board_id=board.id, grade=7, display_name="Class 7")
    db.add(school_class)
    await db.flush()

    subject = Subject(class_id=school_class.id, name="Science")
    db.add(subject)
    await db.flush()

    chapter = Chapter(subject_id=subject.id, name="Nutrition in Plants", sequence_no=1)
    db.add(chapter)
    await db.commit()

    return school_class, subject, chapter


def _build_state(
    school_class: SchoolClass, subject: Subject, chapter: Chapter
) -> TeachingKitState:
    return TeachingKitState(
        request_id=uuid.uuid4(),
        class_id=school_class.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi.value,
        duration=DurationOption.forty.value,
        teaching_mode=TeachingMode.concept.value,
        resource_types=["lesson_plan"],
        current_resource_type="",
        resources=[],
    )


async def test_cache_miss_calls_llm_and_marks_result_uncached(db_session: AsyncSession) -> None:
    school_class, subject, chapter = await _seed_curriculum(db_session)
    fake_llm = FakeLLMProvider()
    config: RunnableConfig = {"configurable": {"db": db_session, "llm_provider": fake_llm}}

    result = await generate_lesson_plan_node(_build_state(school_class, subject, chapter), config)

    assert fake_llm.call_count == 1
    assert result["resources"][0]["cache_hit"] is False


async def test_cache_hit_skips_the_llm_on_a_second_identical_call(
    db_session: AsyncSession,
) -> None:
    school_class, subject, chapter = await _seed_curriculum(db_session)
    fake_llm = FakeLLMProvider()
    config: RunnableConfig = {"configurable": {"db": db_session, "llm_provider": fake_llm}}

    first = await generate_lesson_plan_node(_build_state(school_class, subject, chapter), config)
    second = await generate_lesson_plan_node(_build_state(school_class, subject, chapter), config)

    assert fake_llm.call_count == 1
    assert first["resources"][0]["cache_hit"] is False
    assert second["resources"][0]["cache_hit"] is True
    # Cache hit still produces its own generated_resources row for this request.
    assert first["resources"][0]["resource_id"] != second["resources"][0]["resource_id"]
