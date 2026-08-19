from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.providers.llm.base import LLMProvider
from app.ai.providers.llm.openai_provider import OpenAIProvider
from app.core.config import get_settings
from app.core.security import SupabaseClaims, get_current_claims
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.repositories.user_repository import get_by_supabase_auth_id
from app.db.session import async_session_factory, get_db

__all__ = [
    "get_db",
    "get_current_claims",
    "get_current_user",
    "get_llm_provider",
    "get_session_factory",
    "require_role",
]


async def get_current_user(
    claims: SupabaseClaims = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_by_supabase_auth_id(db, claims.supabase_auth_id)
    if user is None:
        # Valid Supabase session, no app profile yet — the frontend sends these
        # teachers to /onboarding rather than treating this as an auth failure.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
    return user


def require_role(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_role")
        return user

    return dependency


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    raise NotImplementedError(f"LLM provider {settings.llm_provider!r} is not implemented yet")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """For endpoints (SSE) that must open their own DB session outside the
    normal per-request dependency lifecycle — see teaching_kit.py's
    `_stream_events`. Overridden in tests so it points at the same in-memory
    SQLite engine as `get_db`, instead of the real configured DATABASE_URL.
    """
    return async_session_factory
