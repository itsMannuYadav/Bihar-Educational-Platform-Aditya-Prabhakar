import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import AppLanguage, ResourceType
from app.db.models.resource_cache import ResourceCache

__all__ = ["get_cached", "record_cache_hit", "write_cache"]


async def get_cached(db: AsyncSession, cache_key: str) -> ResourceCache | None:
    result = await db.execute(select(ResourceCache).where(ResourceCache.cache_key == cache_key))
    return result.scalar_one_or_none()


async def record_cache_hit(db: AsyncSession, entry: ResourceCache) -> None:
    entry.hit_count += 1
    entry.last_used_at = datetime.now(UTC)
    await db.flush()


async def write_cache(
    db: AsyncSession,
    *,
    cache_key: str,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    chapter_id: uuid.UUID,
    language: AppLanguage,
    resource_type: ResourceType,
    params: dict,
    canonical_resource_id: uuid.UUID,
) -> ResourceCache:
    entry = ResourceCache(
        cache_key=cache_key,
        class_id=class_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        language=language,
        resource_type=resource_type,
        params=params,
        canonical_resource_id=canonical_resource_id,
    )
    db.add(entry)
    await db.flush()
    return entry
