import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.schemas.user import UserCreate


async def get_by_supabase_auth_id(db: AsyncSession, supabase_auth_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.supabase_auth_id == supabase_auth_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    supabase_auth_id: uuid.UUID,
    email: str | None,
    phone: str | None,
    payload: UserCreate,
) -> User:
    user = User(
        supabase_auth_id=supabase_auth_id,
        email=email,
        phone=phone,
        name=payload.name,
        school_id=payload.school_id,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
