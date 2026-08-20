import sqlite3
import uuid
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.v1.deps import get_current_claims, get_db, get_session_factory
from app.core.security import SupabaseClaims
from app.db import models  # noqa: F401  (registers every model on Base.metadata for create_all)
from app.db.base import Base
from app.main import app

FAKE_AUTH_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def db_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine]:
    """A per-test SQLite *file*, not `:memory:` + StaticPool.

    An in-memory SQLite database only exists for as long as its one connection,
    which forces every session in the test to share a single connection. The
    generation graph fans out concurrently (docs/01-architecture.md §3) with
    each branch owning its own session, so sharing one connection made
    concurrent branches commit on top of each other's open cursors
    ("cannot commit transaction - SQL statements in progress"). A file DB gives
    each session a real connection, matching how this behaves on Postgres.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_connection: sqlite3.Connection, _record: object) -> None:
        cursor = dbapi_connection.cursor()
        # WAL keeps a reader from blocking the concurrent writers; busy_timeout
        # makes a second writer wait its turn instead of raising immediately.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

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
