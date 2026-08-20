import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.core import security
from app.core.config import Settings
from app.core.security import decode_supabase_jwt

TEST_SECRET = "test-secret"
TEST_SUB = "22222222-2222-2222-2222-222222222222"
ES256_KID = "test-kid"


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


class _FakeJWKClient:
    """Stands in for `jwt.PyJWKClient` so ES256 tests never touch the network.

    Every current Supabase project signs with ES256 against a per-project
    JWKS endpoint — confirmed by decoding a real access token from a live
    login, not assumed from docs (see the module docstring in security.py).
    A prior version of `decode_supabase_jwt` only ever checked HS256, which
    rejected every one of these with 401, i.e. rejected every real login.
    These two tests are what would have caught that before it shipped.
    """

    def __init__(self, public_key: ec.EllipticCurvePublicKey) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> ec.EllipticCurvePublicKey:
        return self._public_key


def make_es256_token(**overrides: object) -> tuple[str, ec.EllipticCurvePublicKey]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": TEST_SUB,
        "email": "teacher@example.com",
        "phone": "+919000000000",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        **overrides,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": ES256_KID})
    return token, private_key.public_key()


def test_decodes_valid_es256_token(monkeypatch: pytest.MonkeyPatch) -> None:
    token, public_key = make_es256_token()
    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKClient(public_key))

    claims = decode_supabase_jwt(token)

    assert claims.supabase_auth_id == uuid.UUID(TEST_SUB)
    assert claims.email == "teacher@example.com"


def test_rejects_es256_token_signed_by_a_different_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token, _real_public_key = make_es256_token()
    wrong_public_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKClient(wrong_public_key))

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
