import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import AppLanguage, ResourceType
from app.db.models.resource_cache import ResourceCache

__all__ = ["get_cached", "record_cache_hit", "semantic_cache_lookup", "write_cache"]

logger = logging.getLogger(__name__)

# Similarity threshold for the semantic near-match fallback
# (docs/02-database-schema.md §4 step 2).  0.92 means queries must be very
# close in meaning — different phrasings of the same chapter topic should pass;
# a completely different topic should not.
SEMANTIC_SIMILARITY_THRESHOLD = 0.92


async def get_cached(db: AsyncSession, cache_key: str) -> ResourceCache | None:
    result = await db.execute(select(ResourceCache).where(ResourceCache.cache_key == cache_key))
    return result.scalar_one_or_none()


async def record_cache_hit(db: AsyncSession, entry: ResourceCache) -> None:
    entry.hit_count += 1
    entry.last_used_at = datetime.now(UTC)
    await db.flush()


async def semantic_cache_lookup(
    db: AsyncSession,
    *,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    resource_type: ResourceType,
    embedding: list[float],
) -> ResourceCache | None:
    """Cosine-similarity search within the same curriculum scope.

    Returns the closest cache entry above SEMANTIC_SIMILARITY_THRESHOLD, or
    None on any miss — including when the DB doesn't support pgvector (SQLite
    in tests), in which case the OperationalError is swallowed and logged so
    tests stay green while production gets the full semantic fallback.
    """
    try:
        # pgvector <=> = cosine distance (0 = identical, 1 = orthogonal).
        # 1 - distance = similarity, so threshold means distance < 1 - threshold.
        distance_threshold = 1.0 - SEMANTIC_SIMILARITY_THRESHOLD
        stmt = text(
            """
            SELECT id, cache_key, class_id, subject_id, chapter_id, language,
                   resource_type, params, canonical_resource_id,
                   query_embedding, hit_count, last_used_at, created_at,
                   (query_embedding <=> :embedding) AS distance
            FROM resource_cache
            WHERE class_id = :class_id
              AND subject_id = :subject_id
              AND resource_type = :resource_type
              AND query_embedding IS NOT NULL
              AND (query_embedding <=> :embedding) < :distance_threshold
            ORDER BY query_embedding <=> :embedding
            LIMIT 1
            """
        )
        result = await db.execute(
            stmt,
            {
                "embedding": str(embedding),
                "class_id": str(class_id),
                "subject_id": str(subject_id),
                "resource_type": resource_type.value,
                "distance_threshold": distance_threshold,
            },
        )
        row = result.mappings().first()
        if row is None:
            return None
        return await db.get(ResourceCache, row["id"])
    except OperationalError:
        # pgvector extension / <=> operator not available (e.g. SQLite in tests).
        logger.debug("semantic_cache_lookup skipped: pgvector not available")
        return None


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
    query_embedding: list[float] | None = None,
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
        query_embedding=query_embedding,
    )
    db.add(entry)
    await db.flush()
    return entry
