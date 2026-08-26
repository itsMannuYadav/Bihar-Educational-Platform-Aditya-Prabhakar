import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.models.enums import AppLanguage, DurationOption, KitStatus, TeachingMode
from app.db.models.teaching_kit import TeachingKitRequest

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


async def _seed_curriculum(db: AsyncSession) -> tuple[SchoolClass, Subject, Chapter]:
    board = Board(name="BSEB", state="Bihar")
    db.add(board)
    await db.flush()
    klass = SchoolClass(board_id=board.id, grade=8, display_name="Class 8")
    db.add(klass)
    await db.flush()
    subject = Subject(class_id=klass.id, name="Science")
    db.add(subject)
    await db.flush()
    chapter = Chapter(subject_id=subject.id, name="Photosynthesis", sequence_no=1)
    db.add(chapter)
    await db.commit()
    return klass, subject, chapter


async def _seed_request(
    db: AsyncSession, user_id: uuid.UUID, klass: SchoolClass, subject: Subject, chapter: Chapter
) -> TeachingKitRequest:
    req = TeachingKitRequest(
        user_id=user_id,
        class_id=klass.id,
        subject_id=subject.id,
        chapter_id=chapter.id,
        language=AppLanguage.hi,
        duration=DurationOption.forty,
        teaching_mode=TeachingMode.concept,
        status=KitStatus.complete,
        resource_types=["lesson_plan"],
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


def _profile(client: TestClient) -> None:
    r = client.post("/api/v1/me", json={"name": "Test Teacher", "preferredLanguage": "hi"})
    assert r.status_code == 201


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_save_then_list(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)

    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)

    save_res = client.post("/api/v1/library/saved", json={"requestId": str(req.id)})
    assert save_res.status_code == 201
    saved = save_res.json()
    assert saved["chapterName"] == "Photosynthesis"
    assert saved["subjectName"] == "Science"
    assert saved["classDisplayName"] == "Class 8"

    list_res = client.get("/api/v1/library/saved")
    assert list_res.status_code == 200
    body = list_res.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["requestId"] == str(req.id)
    assert body["nextCursor"] is None


async def test_save_note(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)
    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)

    res = client.post(
        "/api/v1/library/saved", json={"requestId": str(req.id), "note": "Great lesson!"}
    )
    assert res.status_code == 201
    assert res.json()["note"] == "Great lesson!"


async def test_unsave(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)
    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)

    save_res = client.post("/api/v1/library/saved", json={"requestId": str(req.id)})
    saved_id = save_res.json()["id"]

    del_res = client.delete(f"/api/v1/library/saved/{saved_id}")
    assert del_res.status_code == 204

    list_res = client.get("/api/v1/library/saved")
    assert list_res.json()["items"] == []

    # Double-delete → 404
    del2 = client.delete(f"/api/v1/library/saved/{saved_id}")
    assert del2.status_code == 404


async def test_get_by_request(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)
    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)

    # Before saving → 404
    res = client.get(f"/api/v1/library/saved/by-request/{req.id}")
    assert res.status_code == 404

    client.post("/api/v1/library/saved", json={"requestId": str(req.id)})

    # After saving → 200
    res = client.get(f"/api/v1/library/saved/by-request/{req.id}")
    assert res.status_code == 200
    assert res.json()["requestId"] == str(req.id)


async def test_search(client: TestClient, db_session: AsyncSession) -> None:
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)
    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)
    client.post("/api/v1/library/saved", json={"requestId": str(req.id)})

    # Matching search
    res = client.get("/api/v1/library/search?q=photo")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Non-matching
    res = client.get("/api/v1/library/search?q=trigonometry")
    assert res.status_code == 200
    assert res.json() == []

    # Empty q returns all saved
    res = client.get("/api/v1/library/search?q=")
    assert len(res.json()) == 1


async def test_resave_restores_record(client: TestClient, db_session: AsyncSession) -> None:
    """Saving → unsaving → saving again should restore the record, not create a duplicate."""
    klass, subject, chapter = await _seed_curriculum(db_session)
    _profile(client)
    from app.tests.conftest import FAKE_AUTH_ID

    req = await _seed_request(db_session, FAKE_AUTH_ID, klass, subject, chapter)

    save1 = client.post("/api/v1/library/saved", json={"requestId": str(req.id)})
    saved_id = save1.json()["id"]
    client.delete(f"/api/v1/library/saved/{saved_id}")
    save2 = client.post("/api/v1/library/saved", json={"requestId": str(req.id)})
    assert save2.status_code == 201

    list_res = client.get("/api/v1/library/saved")
    assert len(list_res.json()["items"]) == 1
