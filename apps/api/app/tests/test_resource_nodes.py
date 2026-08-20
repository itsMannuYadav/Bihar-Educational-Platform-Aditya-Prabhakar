import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.graph import build_graph
from app.ai.orchestration.nodes.registry import PRESENTATION_VERSIONS, trim_slides
from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.models.enums import (
    MVP_RESOURCE_TYPES,
    AppLanguage,
    DurationOption,
    KitStatus,
    ResourceType,
    TeachingMode,
)
from app.db.models.resource_cache import ResourceCache
from app.db.models.resource_detail import MindMap, Presentation, Question, Worksheet
from app.db.models.teaching_kit import GeneratedResource, TeachingKitRequest
from app.db.models.user import User
from app.tests.fakes import FakeLLMProvider


async def _seed_request(db: AsyncSession) -> TeachingKitRequest:
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
    user = User(supabase_auth_id=uuid.uuid4(), name="Anita", preferred_language=AppLanguage.hi)
    db.add_all([chapter, user])
    await db.flush()

    request = TeachingKitRequest(
        user_id=user.id,
        class_id=school_class.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        status=KitStatus.pending,
        resource_types=[rt.value for rt in MVP_RESOURCE_TYPES],
    )
    db.add(request)
    await db.commit()
    return request


def _initial_state(request: TeachingKitRequest) -> dict:
    return {
        "request_id": request.id,
        "class_id": request.class_id,
        "subject_id": request.subject_id,
        "chapter_id": request.chapter_id,
        "language": request.language.value,
        "duration": request.duration.value,
        "teaching_mode": request.teaching_mode.value,
        "resource_types": request.resource_types,
        "current_resource_type": "",
        "resources": [],
        "lesson_plan_content": {},
    }


async def _run_kit(
    request: TeachingKitRequest,
    session_factory: async_sessionmaker[AsyncSession],
    llm: FakeLLMProvider,
) -> dict:
    return await build_graph().ainvoke(
        _initial_state(request),
        config={"configurable": {"session_factory": session_factory, "llm_provider": llm}},
    )


async def test_every_mvp_resource_type_is_generated(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    request = await _seed_request(db_session)

    final_state = await _run_kit(request, db_session_factory, FakeLLMProvider())

    generated = {r["resource_type"] for r in final_state["resources"]}
    assert generated == {rt.value for rt in MVP_RESOURCE_TYPES}
    assert all(r["cache_hit"] is False for r in final_state["resources"])


async def test_normalized_detail_rows_are_written(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Content lands in generated_resources.content *and* the type-specific
    tables from docs/02-database-schema.md section 5 — the latter is what makes
    a question bank filterable without parsing jsonb.
    """
    request = await _seed_request(db_session)

    await _run_kit(request, db_session_factory, FakeLLMProvider())

    assert (await db_session.execute(select(func.count()).select_from(Question))).scalar_one() == 2
    assert (await db_session.execute(select(func.count()).select_from(Worksheet))).scalar_one() == 1
    assert (await db_session.execute(select(func.count()).select_from(MindMap))).scalar_one() == 1
    # One presentations row per slide-count version.
    presentations = (
        (await db_session.execute(select(Presentation).order_by(Presentation.slide_count)))
        .scalars()
        .all()
    )
    assert [p.slide_count for p in presentations] == sorted(PRESENTATION_VERSIONS)
    assert [len(p.slides["slides"]) for p in presentations] == sorted(PRESENTATION_VERSIONS)


async def test_second_kit_for_same_chapter_hits_cache_without_calling_the_llm(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    request = await _seed_request(db_session)
    first_llm = FakeLLMProvider()
    await _run_kit(request, db_session_factory, first_llm)
    assert first_llm.call_count == 6  # every MVP type except audio (still a placeholder)

    second_request = TeachingKitRequest(
        user_id=request.user_id,
        class_id=request.class_id,
        subject_id=request.subject_id,
        chapter_id=request.chapter_id,
        language=request.language,
        duration=request.duration,
        teaching_mode=request.teaching_mode,
        status=KitStatus.pending,
        resource_types=request.resource_types,
    )
    db_session.add(second_request)
    await db_session.commit()

    second_llm = FakeLLMProvider()
    final_state = await _run_kit(second_request, db_session_factory, second_llm)

    assert second_llm.call_count == 0
    cached_types = {r["resource_type"] for r in final_state["resources"] if r["cache_hit"]}
    assert cached_types == {rt.value for rt in MVP_RESOURCE_TYPES if rt is not ResourceType.audio}


async def test_cache_hit_still_writes_its_own_detail_rows(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Detail rows are keyed by resource_id, and a cache hit still mints a new
    generated_resources row — so the second kit needs its own copies or its
    question bank comes back empty.
    """
    request = await _seed_request(db_session)
    await _run_kit(request, db_session_factory, FakeLLMProvider())

    second_request = TeachingKitRequest(
        user_id=request.user_id,
        class_id=request.class_id,
        subject_id=request.subject_id,
        chapter_id=request.chapter_id,
        language=request.language,
        duration=request.duration,
        teaching_mode=request.teaching_mode,
        status=KitStatus.pending,
        resource_types=[ResourceType.lesson_plan.value, ResourceType.questions.value],
    )
    db_session.add(second_request)
    await db_session.commit()
    await _run_kit(second_request, db_session_factory, FakeLLMProvider())

    questions_resource = (
        await db_session.execute(
            select(GeneratedResource).where(
                GeneratedResource.request_id == second_request.id,
                GeneratedResource.resource_type == ResourceType.questions,
            )
        )
    ).scalar_one()
    rows = (
        (
            await db_session.execute(
                select(Question).where(Question.resource_id == questions_resource.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2


async def test_one_cache_entry_per_generated_resource_type(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    request = await _seed_request(db_session)

    await _run_kit(request, db_session_factory, FakeLLMProvider())

    entries = (await db_session.execute(select(ResourceCache))).scalars().all()
    # audio is still a placeholder node, so it writes no cache entry.
    assert {e.resource_type for e in entries} == {
        rt for rt in MVP_RESOURCE_TYPES if rt is not ResourceType.audio
    }
    assert all(e.hit_count == 1 for e in entries)


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (15, list(range(15))),
        (10, [0, 1, 2, 3, 4, 10, 11, 12, 13, 14]),
        (5, [0, 1, 2, 13, 14]),
    ],
)
def test_shorter_decks_drop_from_the_middle(target: int, expected: list[int]) -> None:
    """A 5-slide deck that simply truncated at slide 5 would stop mid-chapter;
    the trim has to keep the opening and the closing.
    """
    slides = [{"i": i} for i in range(15)]
    assert [s["i"] for s in trim_slides(slides, target)] == expected
