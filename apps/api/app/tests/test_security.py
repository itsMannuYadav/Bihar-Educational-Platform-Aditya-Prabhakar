import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.core.security import decode_supabase_jwt

TEST_SUB = "22222222-2222-2222-2222-222222222222"

# Mirrors production: Supabase signs with an asymmetric key (ES256) resolved
# via JWKS, not a shared HS256 secret — see app/core/security.py.
_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
_OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(
    *, signing_key: ec.EllipticCurvePrivateKey = _SIGNING_KEY, **overrides: object
) -> str:
    payload = {
        "sub": TEST_SUB,
        "email": "teacher@example.com",
        "phone": "+919000000000",
        "aud": "authenticated",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        **overrides,
    }
    return jwt.encode(payload, signing_key, algorithm="ES256")


class _StubSigningKey:
    def __init__(self, key: ec.EllipticCurvePublicKey) -> None:
        self.key = key


class _StubJWKClient:
    def get_signing_key_from_jwt(self, token: str) -> _StubSigningKey:
        return _StubSigningKey(_SIGNING_KEY.public_key())


@pytest.fixture(autouse=True)
def _patch_jwks_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.security._jwks_client", lambda: _StubJWKClient())


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
    token = make_token(signing_key=_OTHER_KEY)

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
        _SIGNING_KEY,
        algorithm="ES256",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_token_claims"
