from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_claims, get_db
from app.db.repositories.school_repository import search_schools
from app.schemas.school import SchoolRead

router = APIRouter(tags=["schools"])


@router.get("/schools", response_model=list[SchoolRead])
async def list_schools(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    _claims=Depends(get_current_claims),
) -> list[SchoolRead]:
    schools = await search_schools(db, query=q)
    return [SchoolRead.model_validate(s) for s in schools]
