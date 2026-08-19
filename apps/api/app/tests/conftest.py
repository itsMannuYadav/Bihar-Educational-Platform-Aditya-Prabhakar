import uuid
from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.deps import get_current_claims, get_db
from app.core.security import SupabaseClaims
from app.db import models  # noqa: F401  (registers every model on Base.metadata for create_all)
from app.db.base import Base
from app.main import app

FAKE_AUTH_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession) -> Iterator[TestClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    def override_get_claims() -> SupabaseClaims:
        return SupabaseClaims(
            supabase_auth_id=FAKE_AUTH_ID, email="teacher@example.com", phone=None
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_claims] = override_get_claims
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
