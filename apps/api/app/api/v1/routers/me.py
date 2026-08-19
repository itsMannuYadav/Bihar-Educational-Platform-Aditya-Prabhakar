from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_claims, get_current_user, get_db
from app.core.security import SupabaseClaims
from app.db.models.user import User
from app.db.repositories.user_repository import create_user, get_by_supabase_auth_id
from app.schemas.user import UserCreate, UserRead

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/me", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_me(
    payload: UserCreate,
    claims: SupabaseClaims = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
) -> User:
    existing = await get_by_supabase_auth_id(db, claims.supabase_auth_id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="profile_already_exists")

    return await create_user(
        db,
        supabase_auth_id=claims.supabase_auth_id,
        email=claims.email,
        phone=claims.phone,
        payload=payload,
    )
