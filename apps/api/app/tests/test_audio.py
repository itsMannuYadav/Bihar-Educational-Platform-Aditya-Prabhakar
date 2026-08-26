from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_llm_provider, get_tts_provider
from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.main import app
from app.tests.fakes import FakeLLMProvider, FakeTTSProvider


async def _seed(db: AsyncSession) -> tuple[SchoolClass, Subject, Chapter]:
    board = Board(name="BSEB", state="Bihar")
    db.add(board)
    await db.flush()
    klass = SchoolClass(board_id=board.id, grade=7, display_name="Class 7")
    db.add(klass)
    await db.flush()
    subject = Subject(class_id=klass.id, name="Science")
    db.add(subject)
    await db.flush()
    chapter = Chapter(subject_id=subject.id, name="Nutrition in Plants", sequence_no=1)
    db.add(chapter)
    await db.commit()
    return klass, subject, chapter


def _setup(client: TestClient) -> None:
    client.post("/api/v1/me", json={"name": "Test Teacher", "preferredLanguage": "hi"})
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()


async def _generate_kit_with_audio(client: TestClient, db: AsyncSession) -> tuple[str, str]:
    """Returns (request_id, audio_resource_id)."""
    klass, subject, chapter = await _seed(db)
    _setup(client)

    gen = client.post(
        "/api/v1/teaching-kit/generate",
        json={
            "classId": str(klass.id),
            "subjectId": str(subject.id),
            "chapterId": str(chapter.id),
            "language": "hi",
            "duration": "40",
            "resourceTypes": ["lesson_plan", "audio"],
        },
    )
    assert gen.status_code == 202
    request_id = gen.json()["requestId"]

    stream = client.get(f"/api/v1/teaching-kit/{request_id}/stream")
    assert stream.status_code == 200

    kit = client.get(f"/api/v1/teaching-kit/{request_id}")
    resources = kit.json()["resources"]
    audio = next(r for r in resources if r["resourceType"] == "audio")
    return request_id, audio["id"]


async def test_audio_resource_has_three_variants(
    client: TestClient, db_session: AsyncSession
) -> None:
    _, audio_id = await _generate_kit_with_audio(client, db_session)
    res = client.get(f"/api/v1/resources/{audio_id}")
    assert res.status_code == 200
    content = res.json()["content"]
    variants = content["variants"]
    assert set(variants.keys()) == {"1", "3", "5"}
    assert all(isinstance(v, str) and len(v) > 10 for v in variants.values())


async def test_audio_stream_returns_mp3(client: TestClient, db_session: AsyncSession) -> None:
    fake_tts = FakeTTSProvider()
    app.dependency_overrides[get_tts_provider] = lambda: fake_tts

    _, audio_id = await _generate_kit_with_audio(client, db_session)

    for duration in ["1", "3", "5"]:
        res = client.get(f"/api/v1/resources/{audio_id}/audio/stream?duration={duration}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 0

    assert fake_tts.call_count == 3

    app.dependency_overrides.pop(get_tts_provider, None)


async def test_audio_stream_rejects_wrong_resource_type(
    client: TestClient, db_session: AsyncSession
) -> None:
    fake_tts = FakeTTSProvider()
    app.dependency_overrides[get_tts_provider] = lambda: fake_tts

    klass, subject, chapter = await _seed(db_session)
    _setup(client)

    gen = client.post(
        "/api/v1/teaching-kit/generate",
        json={
            "classId": str(klass.id),
            "subjectId": str(subject.id),
            "chapterId": str(chapter.id),
            "language": "hi",
            "duration": "40",
            "resourceTypes": ["lesson_plan"],
        },
    )
    request_id = gen.json()["requestId"]
    client.get(f"/api/v1/teaching-kit/{request_id}/stream")
    kit = client.get(f"/api/v1/teaching-kit/{request_id}")
    lesson_plan_id = next(
        r["id"] for r in kit.json()["resources"] if r["resourceType"] == "lesson_plan"
    )

    res = client.get(f"/api/v1/resources/{lesson_plan_id}/audio/stream")
    assert res.status_code == 400

    app.dependency_overrides.pop(get_tts_provider, None)
