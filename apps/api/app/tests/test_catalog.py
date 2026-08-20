from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject


async def _seed_curriculum(db: AsyncSession) -> tuple[SchoolClass, SchoolClass, Subject, Subject]:
    board = Board(name="BSEB", state="Bihar")
    db.add(board)
    await db.flush()

    class_7 = SchoolClass(board_id=board.id, grade=7, display_name="Class 7")
    class_8 = SchoolClass(board_id=board.id, grade=8, display_name="Class 8")
    db.add_all([class_7, class_8])
    await db.flush()

    science_7 = Subject(class_id=class_7.id, name="Science")
    hindi_7 = Subject(class_id=class_7.id, name="Hindi")
    science_8 = Subject(class_id=class_8.id, name="Science")
    db.add_all([science_7, hindi_7, science_8])
    await db.flush()

    db.add_all(
        [
            Chapter(subject_id=science_7.id, name="Nutrition in Plants", sequence_no=1),
            Chapter(subject_id=science_7.id, name="Heat", sequence_no=4),
            Chapter(subject_id=science_8.id, name="Crop Production and Management", sequence_no=1),
        ]
    )
    await db.commit()
    return class_7, class_8, science_7, hindi_7


async def test_get_classes_filters_by_board(client: TestClient, db_session: AsyncSession) -> None:
    class_7, class_8, _, _ = await _seed_curriculum(db_session)

    response = client.get("/api/v1/catalog/classes", params={"board_id": str(class_7.board_id)})

    assert response.status_code == 200
    grades = [c["grade"] for c in response.json()]
    assert grades == [7, 8]


async def test_get_subjects_filters_by_class(client: TestClient, db_session: AsyncSession) -> None:
    class_7, _, _, _ = await _seed_curriculum(db_session)

    response = client.get("/api/v1/catalog/subjects", params={"class_id": str(class_7.id)})

    assert response.status_code == 200
    names = sorted(s["name"] for s in response.json())
    assert names == ["Hindi", "Science"]


async def test_get_chapters_filters_by_subject_and_orders_by_sequence(
    client: TestClient, db_session: AsyncSession
) -> None:
    _, _, science_7, _ = await _seed_curriculum(db_session)

    response = client.get("/api/v1/catalog/chapters", params={"subject_id": str(science_7.id)})

    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert names == ["Nutrition in Plants", "Heat"]


async def test_create_chapter_adds_one_for_a_subject_with_none_seeded(
    client: TestClient, db_session: AsyncSession
) -> None:
    _, _, _, hindi_7 = await _seed_curriculum(db_session)

    response = client.post(
        "/api/v1/catalog/chapters",
        json={"subjectId": str(hindi_7.id), "name": "Bachpan"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Bachpan"
    assert body["subjectId"] == str(hindi_7.id)

    # Immediately visible to the picker that prompted adding it in the first
    # place — the whole point is a teacher isn't blocked by empty content.
    listed = client.get("/api/v1/catalog/chapters", params={"subject_id": str(hindi_7.id)})
    assert [c["name"] for c in listed.json()] == ["Bachpan"]


async def test_create_chapter_is_case_insensitive_get_or_create(
    client: TestClient, db_session: AsyncSession
) -> None:
    _, _, _, hindi_7 = await _seed_curriculum(db_session)

    first = client.post(
        "/api/v1/catalog/chapters", json={"subjectId": str(hindi_7.id), "name": "Bachpan"}
    )
    second = client.post(
        "/api/v1/catalog/chapters", json={"subjectId": str(hindi_7.id), "name": "  bachpan  "}
    )

    assert first.status_code == 201
    assert second.status_code == 201
    # Same chapter both times — two teachers typing the same chapter name
    # (different case, incidental whitespace) must not fork the catalog.
    assert first.json()["id"] == second.json()["id"]

    listed = client.get("/api/v1/catalog/chapters", params={"subject_id": str(hindi_7.id)})
    assert len(listed.json()) == 1


async def test_create_chapter_rejects_a_blank_name(
    client: TestClient, db_session: AsyncSession
) -> None:
    _, _, _, hindi_7 = await _seed_curriculum(db_session)

    response = client.post(
        "/api/v1/catalog/chapters", json={"subjectId": str(hindi_7.id), "name": "   "}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "chapter_name_empty"
