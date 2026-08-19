import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import decode_supabase_jwt

TEST_SECRET = "test-secret"
TEST_SUB = "22222222-2222-2222-2222-222222222222"


def make_token(**overrides: object) -> str:
    payload = {
        "sub": TEST_SUB,
        "email": "teacher@example.com",
        "phone": "+919000000000",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        **overrides,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: Settings(supabase_jwt_secret=TEST_SECRET),
    )


def test_decodes_valid_token() -> None:
    claims = decode_supabase_jwt(make_token())

    assert claims.supabase_auth_id == uuid.UUID(TEST_SUB)
    assert claims.email == "teacher@example.com"
    assert claims.phone == "+919000000000"


def test_rejects_expired_token() -> None:
    token = make_token(exp=datetime.now(UTC) - timedelta(minutes=1))

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_or_expired_token"


def test_rejects_tampered_signature() -> None:
    token = jwt.encode(
        {"sub": TEST_SUB, "aud": "authenticated", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "a-completely-different-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_rejects_wrong_audience() -> None:
    token = make_token(aud="some-other-app")

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_rejects_missing_sub_claim() -> None:
    token = jwt.encode(
        {"aud": "authenticated", "exp": datetime.now(UTC) + timedelta(hours=1)},
        TEST_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_token_claims"
