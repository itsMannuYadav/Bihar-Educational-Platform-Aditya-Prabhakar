"""Tests for role-based access control (Phase 8).

Verifies that `require_role` in `app.api.v1.deps` correctly allows or denies
access based on the authenticated user's role.  The tests use a minimal FastAPI
router mounted only for the duration of the test, so they don't couple to any
particular production endpoint.
"""

import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db, require_role
from app.core.security import SupabaseClaims, get_current_claims
from app.db.models.enums import UserRole
from app.db.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUTH_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_user(role: UserRole) -> User:
    user = User(
        supabase_auth_id=_AUTH_ID,
        email="user@example.com",
        role=role,
        preferred_language="en",
    )
    user.name = "Test User"
    return user


def _client_for_role(role: UserRole, db_session: AsyncSession) -> TestClient:
    """Build a TestClient whose auth is fixed to `role`.

    Mounts a one-route FastAPI app so we can test `require_role` without
    depending on a real production endpoint having the right gate.
    """
    test_app = FastAPI()

    @test_app.get("/admin-only")
    async def admin_only(
        _: User = Depends(require_role(UserRole.school_admin, UserRole.super_admin)),  # noqa: B008
    ) -> dict:
        return {"ok": True}

    @test_app.get("/teacher-only")
    async def teacher_only(
        _: User = Depends(require_role(UserRole.teacher)),  # noqa: B008
    ) -> dict:
        return {"ok": True}

    @test_app.get("/any-role")
    async def any_role(
        _: User = Depends(get_current_user),
    ) -> dict:
        return {"ok": True}

    async def override_get_db():  # type: ignore[return]
        yield db_session

    def override_get_claims() -> SupabaseClaims:
        return SupabaseClaims(supabase_auth_id=_AUTH_ID, email="user@example.com", phone=None)

    async def override_get_user() -> User:
        return _make_user(role)

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_claims] = override_get_claims
    test_app.dependency_overrides[get_current_user] = override_get_user

    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "role,expected_status",
    [
        (UserRole.teacher, 403),
        (UserRole.school_admin, 200),
        (UserRole.super_admin, 200),
    ],
)
async def test_admin_only_endpoint(
    role: UserRole, expected_status: int, db_session: AsyncSession
) -> None:
    client = _client_for_role(role, db_session)
    res = client.get("/admin-only")
    assert res.status_code == expected_status


@pytest.mark.parametrize(
    "role,expected_status",
    [
        (UserRole.teacher, 200),
        (UserRole.school_admin, 403),
        (UserRole.super_admin, 403),
    ],
)
async def test_teacher_only_endpoint(
    role: UserRole, expected_status: int, db_session: AsyncSession
) -> None:
    client = _client_for_role(role, db_session)
    res = client.get("/teacher-only")
    assert res.status_code == expected_status


@pytest.mark.parametrize("role", [UserRole.teacher, UserRole.school_admin, UserRole.super_admin])
async def test_any_authenticated_user_can_access(role: UserRole, db_session: AsyncSession) -> None:
    client = _client_for_role(role, db_session)
    res = client.get("/any-role")
    assert res.status_code == 200


async def test_require_role_returns_403_with_detail(db_session: AsyncSession) -> None:
    """The 403 body must carry `detail: insufficient_role` for API clients to
    distinguish a role gate from other 4xx errors."""
    client = _client_for_role(UserRole.teacher, db_session)
    res = client.get("/admin-only")
    assert res.status_code == 403
    assert res.json()["detail"] == "insufficient_role"
