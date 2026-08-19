from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School


async def search_schools(db: AsyncSession, *, query: str | None, limit: int = 20) -> list[School]:
    stmt = select(School).where(School.deleted_at.is_(None))
    if query:
        stmt = stmt.where(School.name.ilike(f"%{query}%"))
    stmt = stmt.order_by(School.name).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
