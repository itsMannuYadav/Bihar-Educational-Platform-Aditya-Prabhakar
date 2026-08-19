from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School


async def _add_schools(db: AsyncSession) -> None:
    db.add_all(
        [
            School(name="Gram Panchayat Middle School, Nalanda", state="Bihar", district="Nalanda"),
            School(name="Rajkiya Madhya Vidyalaya, Patna", state="Bihar", district="Patna"),
        ]
    )
    await db.commit()


async def test_search_schools_filters_by_name(client: TestClient, db_session: AsyncSession) -> None:
    await _add_schools(db_session)

    response = client.get("/api/v1/schools", params={"q": "patna"})

    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert names == ["Rajkiya Madhya Vidyalaya, Patna"]


async def test_search_schools_without_query_returns_all(
    client: TestClient, db_session: AsyncSession
) -> None:
    await _add_schools(db_session)

    response = client.get("/api/v1/schools")

    assert response.status_code == 200
    assert len(response.json()) == 2
