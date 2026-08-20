import uuid
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

# Every Supabase project issues both flavours of token depending on age and
# migration state, so both have to be supported at once, not chosen once:
#
# - ES256, asymmetric, verified against the project's public JWKS
#   (`{supabase_url}/auth/v1/.well-known/jwks.json`) — what a *current*
#   Supabase project issues, confirmed by decoding a real access token from a
#   live signInWithOtp() call: `{"alg": "ES256", "kid": "5370...42cca"}`. A
#   version of this file that only checked HS256 against SUPABASE_JWT_SECRET
#   rejected every one of these with 401 `invalid_or_expired_token` — i.e. it
#   would have rejected every real login, always, silently, in production.
# - HS256, symmetric, verified against SUPABASE_JWT_SECRET — the legacy
#   shared-secret scheme, kept for projects still on it and for tests, which
#   sign fixtures with a plain shared secret rather than standing up a JWKS
#   server.
#
# The token's own header names which one it used, so branch on that instead
# of guessing or trying both.


@dataclass(frozen=True)
class SupabaseClaims:
    """The decoded, verified identity of the caller — not yet an app user.

    A first-time caller has valid claims but no `users` row; routers decide
    what that means (see /me's onboarding-required 404 in routers/me.py).
    """

    supabase_auth_id: uuid.UUID
    email: str | None
    phone: str | None


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    # Module-level cache so the JWKS document (and its own internal 5-minute
    # key cache) is fetched once per process rather than once per request.
    settings = get_settings()
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def decode_supabase_jwt(token: str) -> SupabaseClaims:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg", "").startswith("ES") or header.get("alg", "").startswith("RS"):
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key, algorithms=[header["alg"]], audience="authenticated"
            )
        else:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except jwt.PyJWTError as exc:
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
