import uuid
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    # Supabase projects created after the JWT signing-keys rollout sign
    # tokens with an asymmetric key (ES256 here) rather than the legacy
    # HS256 shared secret, so verification has to go through the project's
    # JWKS rather than SUPABASE_JWT_SECRET. PyJWKClient caches keys by kid
    # and refetches on an unrecognized one, so this survives key rotation.
    settings = get_settings()
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


@dataclass(frozen=True)
class SupabaseClaims:
    """The decoded, verified identity of the caller — not yet an app user.

    A first-time caller has valid claims but no `users` row; routers decide
    what that means (see /me's onboarding-required 404 in routers/me.py).
    """

    supabase_auth_id: uuid.UUID
    email: str | None
    phone: str | None


def decode_supabase_jwt(token: str) -> SupabaseClaims:
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_expired_token",
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_claims")

    return SupabaseClaims(
        supabase_auth_id=uuid.UUID(sub),
        email=payload.get("email"),
        phone=payload.get("phone") or None,
    )


def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token: str | None = Query(default=None),
) -> SupabaseClaims:
    # `token` query-param fallback exists only for the SSE stream endpoint:
    # native EventSource can't send an Authorization header. Every other
    # route keeps using the bearer header as normal.
    raw_token = credentials.credentials if credentials is not None else token
    if raw_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    return decode_supabase_jwt(raw_token)
