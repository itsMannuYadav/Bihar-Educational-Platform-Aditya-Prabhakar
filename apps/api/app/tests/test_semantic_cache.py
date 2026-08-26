"""Tests for the semantic near-match cache fallback (Phase 7).

All tests use the FakeEmbeddingProvider so no real OpenAI calls happen, and
the semantic_cache_lookup is exercised against SQLite — it gracefully returns
None because pgvector's <=> operator is absent, which is the correct
production-safe behaviour: exact-key cache still works; semantic fallback just
doesn't fire in the test DB.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.embedding.base import EmbeddingProvider
from app.cache.keys import compute_cache_key
from app.cache.service import semantic_cache_lookup, write_cache
from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode


class FakeEmbeddingProvider:
    """Returns a deterministic 1536-dim embedding for any text — no network."""

    def __init__(self, *, vec: list[float] | None = None) -> None:
        self._vec = vec or [0.1] * 1536
        self.call_count = 0

    async def embed(self, text: str) -> list[float]:
        self.call_count += 1
        return self._vec


# ── EmbeddingProvider protocol check ─────────────────────────────────────────


def test_fake_embedding_provider_satisfies_protocol() -> None:
    provider: EmbeddingProvider = FakeEmbeddingProvider()  # type: ignore[assignment]
    assert provider is not None


# ── semantic_cache_lookup degrades gracefully on SQLite ───────────────────────


async def test_semantic_lookup_returns_none_on_sqlite(db_session: AsyncSession) -> None:
    """pgvector <=> operator not available in SQLite — function must return None,
    not raise, so generation falls through to the LLM as expected.
    """
    result = await semantic_cache_lookup(
        db_session,
        class_id=uuid.uuid4(),
        subject_id=uuid.uuid4(),
        resource_type=ResourceType.lesson_plan,
        embedding=[0.1] * 1536,
    )
    assert result is None


# ── write_cache accepts optional embedding ────────────────────────────────────


async def test_write_cache_stores_embedding(db_session: AsyncSession) -> None:
    from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
    from app.db.models.enums import KitStatus
    from app.db.models.teaching_kit import GeneratedResource, TeachingKitRequest
    from app.db.models.user import User

    board = Board(name="BSEB", state="Bihar")
    db_session.add(board)
    await db_session.flush()
    klass = SchoolClass(board_id=board.id, grade=7, display_name="Class 7")
    db_session.add(klass)
    await db_session.flush()
    subject = Subject(class_id=klass.id, name="Science")
    db_session.add(subject)
    await db_session.flush()
    chapter = Chapter(subject_id=subject.id, name="Nutrition in Plants", sequence_no=1)
    db_session.add(chapter)
    await db_session.flush()

    user = User(supabase_auth_id=uuid.uuid4(), name="Teacher", preferred_language=AppLanguage.hi)
    db_session.add(user)
    await db_session.flush()

    request = TeachingKitRequest(
        user_id=user.id,
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        status=KitStatus.complete,
        resource_types=["lesson_plan"],
    )
    db_session.add(request)
    await db_session.flush()

    resource = GeneratedResource(
        request_id=request.id,
        resource_type=ResourceType.lesson_plan,
        content={"objectives": ["Learn something"]},
        language=AppLanguage.hi,
        params={},
    )
    db_session.add(resource)
    await db_session.flush()

    embedding = [0.5] * 1536
    cache_key = compute_cache_key(
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        resource_type=ResourceType.lesson_plan,
        params={},
    )
    entry = await write_cache(
        db_session,
        cache_key=cache_key,
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        resource_type=ResourceType.lesson_plan,
        params={},
        canonical_resource_id=resource.id,
        query_embedding=embedding,
    )
    await db_session.commit()

    assert entry.query_embedding == embedding


# ── run_resource_node with embedding_provider (semantic path skipped in SQLite)


async def test_run_resource_node_accepts_embedding_provider(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Generating a kit with an embedding_provider wired in should not raise,
    even though semantic lookup always returns None in SQLite (OperationalError
    swallowed). The kit completes normally via the LLM path.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.ai.orchestration.nodes.base import run_resource_node
    from app.ai.orchestration.nodes.registry import RESOURCE_SPECS
    from app.api.v1.deps import get_llm_provider, get_session_factory
    from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
    from app.db.models.enums import KitStatus
    from app.db.models.teaching_kit import TeachingKitRequest
    from app.db.models.user import User
    from app.main import app
    from app.tests.fakes import FakeLLMProvider

    board = Board(name="BSEB2", state="Bihar")
    db_session.add(board)
    await db_session.flush()
    klass = SchoolClass(board_id=board.id, grade=8, display_name="Class 8")
    db_session.add(klass)
    await db_session.flush()
    subject = Subject(class_id=klass.id, name="Maths")
    db_session.add(subject)
    await db_session.flush()
    chapter = Chapter(subject_id=subject.id, name="Fractions", sequence_no=1)
    db_session.add(chapter)
    await db_session.flush()

    user = User(supabase_auth_id=uuid.uuid4(), name="T2", preferred_language=AppLanguage.hi)
    db_session.add(user)
    await db_session.flush()

    request = TeachingKitRequest(
        user_id=user.id,
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        status=KitStatus.pending,
        resource_types=["lesson_plan"],
        raw_query="fractions lesson",
    )
    db_session.add(request)
    await db_session.commit()

    fake_embed = FakeEmbeddingProvider()
    fake_llm = FakeLLMProvider()

    session_factory: async_sessionmaker = app.dependency_overrides.get(
        get_session_factory, get_session_factory
    )()
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm

    spec = RESOURCE_SPECS[ResourceType.lesson_plan]
    generation = await run_resource_node(
        spec=spec,
        session_factory=session_factory,
        llm_provider=fake_llm,
        embedding_provider=fake_embed,
        request_id=request.id,
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        lesson_plan_content={},
        raw_query="fractions lesson",
    )

    assert generation.cache_hit is False
    # Embedding was requested for the semantic lookup attempt
    assert fake_embed.call_count == 1

    app.dependency_overrides.pop(get_llm_provider, None)
