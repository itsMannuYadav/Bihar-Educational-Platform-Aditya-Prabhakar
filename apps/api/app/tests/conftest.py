import uuid
from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.v1.deps import get_current_claims, get_db, get_session_factory
from app.core.security import SupabaseClaims
from app.db import models  # noqa: F401  (registers every model on Base.metadata for create_all)
from app.db.base import Base
from app.main import app

FAKE_AUTH_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Bound to the same in-memory engine as `db_session` — used to override
    `get_session_factory` for endpoints (SSE) that open their own session
    outside the normal per-request dependency lifecycle.
    """
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with db_session_factory() as session:
        yield session


@pytest.fixture
def client(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> Iterator[TestClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    def override_get_claims() -> SupabaseClaims:
        return SupabaseClaims(
            supabase_auth_id=FAKE_AUTH_ID, email="teacher@example.com", phone=None
        )

    def override_get_session_factory() -> async_sessionmaker[AsyncSession]:
        return db_session_factory

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_claims] = override_get_claims
    app.dependency_overrides[get_session_factory] = override_get_session_factory
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
