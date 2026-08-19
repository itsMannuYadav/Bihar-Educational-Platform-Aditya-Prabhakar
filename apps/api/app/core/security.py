import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


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
    settings = get_settings()
    try:
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
) -> SupabaseClaims:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    return decode_supabase_jwt(credentials.credentials)
