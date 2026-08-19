import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_llm_provider
from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.models.enums import AppLanguage, DurationOption, KitStatus, TeachingMode
from app.db.models.teaching_kit import TeachingKitRequest
from app.main import app
from app.tests.fakes import FakeLLMProvider

MVP_RESOURCE_TYPE_COUNT = 7  # lesson_plan, teaching_script, questions, worksheet, presentation, mind_map, audio


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


def _create_profile(client: TestClient) -> None:
    res = client.post("/api/v1/me", json={"name": "Anita Kumari", "preferredLanguage": "hi"})
    assert res.status_code == 201


def _use_fake_llm_provider() -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()


async def test_generate_then_stream_returns_every_mvp_resource(
    client: TestClient, db_session: AsyncSession
) -> None:
    school_class, subject, chapter = await _seed_curriculum(db_session)
    _create_profile(client)
    _use_fake_llm_provider()

    generate_res = client.post(
        "/api/v1/teaching-kit/generate",
        json={
            "classId": str(school_class.id),
            "subjectId": str(subject.id),
            "chapterId": str(chapter.id),
            "language": "hi",
            "duration": "40",
        },
    )
    assert generate_res.status_code == 202
    body = generate_res.json()
    assert body["status"] == "pending"
    request_id = body["requestId"]

    stream_res = client.get(f"/api/v1/teaching-kit/{request_id}/stream")
    assert stream_res.status_code == 200
    assert stream_res.text.count("event: resource_ready") == MVP_RESOURCE_TYPE_COUNT
    assert "event: kit_complete" in stream_res.text
    assert "event: error" not in stream_res.text

    poll_res = client.get(f"/api/v1/teaching-kit/{request_id}")
    assert poll_res.status_code == 200
    poll_body = poll_res.json()
    assert poll_body["status"] == "complete"
    assert len(poll_body["resources"]) == MVP_RESOURCE_TYPE_COUNT
    lesson_plan = next(r for r in poll_body["resources"] if r["resourceType"] == "lesson_plan")
    assert lesson_plan["cacheHit"] is False
    assert lesson_plan["content"]["objectives"]


async def test_poll_rejects_a_request_owned_by_someone_else(
    client: TestClient, db_session: AsyncSession
) -> None:
    school_class, subject, chapter = await _seed_curriculum(db_session)
    _create_profile(client)

    someone_elses_request = TeachingKitRequest(
        user_id=uuid.uuid4(),
        class_id=school_class.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        status=KitStatus.pending,
        resource_types=["lesson_plan"],
    )
    db_session.add(someone_elses_request)
    await db_session.commit()

    res = client.get(f"/api/v1/teaching-kit/{someone_elses_request.id}")
    assert res.status_code == 403


async def test_generate_requires_a_profile(client: TestClient, db_session: AsyncSession) -> None:
    school_class, subject, chapter = await _seed_curriculum(db_session)

    res = client.post(
        "/api/v1/teaching-kit/generate",
        json={
            "classId": str(school_class.id),
            "subjectId": str(subject.id),
            "chapterId": str(chapter.id),
            "language": "hi",
            "duration": "40",
        },
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "profile_not_found"
