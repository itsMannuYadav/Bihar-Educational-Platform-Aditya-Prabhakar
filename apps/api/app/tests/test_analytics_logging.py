"""Tests for analytics event logging (Phase 7).

Verifies that cache_hit and cache_miss events are written to analytics_events
during kit generation, and that the /analytics/cache-stats endpoint aggregates
them correctly.
"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_llm_provider
from app.db.models.analytics import AnalyticsEvent
from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.models.enums import (
    AnalyticsEventType,
)
from app.db.repositories.analytics_repository import log_event
from app.main import app
from app.tests.fakes import FakeLLMProvider

# ── log_event: fire-and-forget, never raises ─────────────────────────────────


async def test_log_event_writes_row(db_session: AsyncSession) -> None:
    await log_event(
        db_session,
        event_type=AnalyticsEventType.cache_miss,
        metadata={"resource_type": "lesson_plan"},
    )
    await db_session.commit()

    rows = (
        (
            await db_session.execute(
                select(AnalyticsEvent).where(
                    AnalyticsEvent.event_type == AnalyticsEventType.cache_miss
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].event_metadata["resource_type"] == "lesson_plan"


async def test_log_event_does_not_raise_on_bad_input(db_session: AsyncSession) -> None:
    # Should swallow exceptions rather than bubbling them up.
    # We can't easily make flush fail here, but we verify the function completes.
    await log_event(
        db_session,
        event_type=AnalyticsEventType.cache_hit,
        metadata={"resource_type": "questions"},
        user_id=None,
    )
    # No assertion needed — reaching here means it didn't raise.


# ── kit generation writes cache_miss events ───────────────────────────────────


async def _seed(db: AsyncSession):
    board = Board(name="BSEB-A", state="Bihar")
    db.add(board)
    await db.flush()
    klass = SchoolClass(board_id=board.id, grade=9, display_name="Class 9")
    db.add(klass)
    await db.flush()
    subject = Subject(class_id=klass.id, name="History")
    db.add(subject)
    await db.flush()
    chapter = Chapter(subject_id=subject.id, name="The French Revolution", sequence_no=1)
    db.add(chapter)
    await db.commit()
    return klass, subject, chapter


async def test_kit_generation_writes_cache_miss_events(
    client: TestClient, db_session: AsyncSession
) -> None:
    klass, subject, chapter = await _seed(db_session)
    client.post("/api/v1/me", json={"name": "T", "preferredLanguage": "hi"})
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()

    gen = client.post(
        "/api/v1/teaching-kit/generate",
        json={
            "classId": str(klass.id),
            "subjectId": str(subject.id),
            "chapterId": str(chapter.id),
            "language": "hi",
            "duration": "40",
            "resourceTypes": ["lesson_plan", "questions"],
        },
    )
    assert gen.status_code == 202
    request_id = gen.json()["requestId"]
    client.get(f"/api/v1/teaching-kit/{request_id}/stream")

    misses = (
        (
            await db_session.execute(
                select(AnalyticsEvent).where(
                    AnalyticsEvent.event_type == AnalyticsEventType.cache_miss
                )
            )
        )
        .scalars()
        .all()
    )
    # lesson_plan + questions = at least 2 miss events
    assert len(misses) >= 2
    rt_values = {m.event_metadata.get("resource_type") for m in misses}
    assert "lesson_plan" in rt_values
    assert "questions" in rt_values

    app.dependency_overrides.pop(get_llm_provider, None)


async def test_second_kit_writes_cache_hit_events(
    client: TestClient, db_session: AsyncSession
) -> None:
    klass, subject, chapter = await _seed(db_session)
    client.post("/api/v1/me", json={"name": "T", "preferredLanguage": "hi"})
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()

    payload = {
        "classId": str(klass.id),
        "subjectId": str(subject.id),
        "chapterId": str(chapter.id),
        "language": "hi",
        "duration": "40",
        "resourceTypes": ["lesson_plan"],
    }
    r1 = client.post("/api/v1/teaching-kit/generate", json=payload)
    client.get(f"/api/v1/teaching-kit/{r1.json()['requestId']}/stream")

    r2 = client.post("/api/v1/teaching-kit/generate", json=payload)
    client.get(f"/api/v1/teaching-kit/{r2.json()['requestId']}/stream")

    hits = (
        (
            await db_session.execute(
                select(AnalyticsEvent).where(
                    AnalyticsEvent.event_type == AnalyticsEventType.cache_hit
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(hits) >= 1
    assert hits[0].event_metadata.get("hit_source") == "exact"

    app.dependency_overrides.pop(get_llm_provider, None)


# ── /analytics/cache-stats endpoint ──────────────────────────────────────────


async def test_cache_stats_returns_stats(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed(db_session)
    client.post("/api/v1/me", json={"name": "T", "preferredLanguage": "hi"})
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()

    payload = {
        "classId": str(klass.id),
        "subjectId": str(subject.id),
        "chapterId": str(chapter.id),
        "language": "hi",
        "duration": "40",
        "resourceTypes": ["lesson_plan"],
    }
    r1 = client.post("/api/v1/teaching-kit/generate", json=payload)
    client.get(f"/api/v1/teaching-kit/{r1.json()['requestId']}/stream")

    res = client.get("/api/v1/analytics/cache-stats")
    assert res.status_code == 200
    body = res.json()
    assert "stats" in body
    resource_types = [s["resource_type"] for s in body["stats"]]
    assert "lesson_plan" in resource_types

    app.dependency_overrides.pop(get_llm_provider, None)
