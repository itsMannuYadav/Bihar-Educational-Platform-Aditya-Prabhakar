from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.analytics import AnalyticsEvent
from app.db.models.enums import AnalyticsEventType
from app.db.models.resource_cache import ResourceCache
from app.db.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ResourceCacheStats(BaseModel):
    resource_type: str
    cache_entries: int
    total_hits: int
    avg_hit_count: float
    event_hits: int
    event_misses: int


class CacheStatsResponse(BaseModel):
    stats: list[ResourceCacheStats]
    overall_hit_rate_pct: float | None


@router.get("/cache-stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CacheStatsResponse:
    """Hit-rate view by resource type — reads resource_cache (hit_count) and
    analytics_events (live event stream). Accessible to any logged-in user
    for teacher/team transparency; no super_admin gate at MVP scale.

    Uses Python-side aggregation of analytics_events so the JSON extraction
    stays DB-agnostic (SQLite in tests, Postgres in production).
    """
    # ── resource_cache aggregate (single SQL query) ───────────────────────────
    cache_rows = (
        await db.execute(
            select(
                ResourceCache.resource_type,
                func.count(ResourceCache.id).label("cache_entries"),
                func.sum(ResourceCache.hit_count).label("total_hits"),
                func.avg(ResourceCache.hit_count).label("avg_hit_count"),
            ).group_by(ResourceCache.resource_type)
        )
    ).all()

    # ── analytics_events — Python-side aggregation ────────────────────────────
    # Fetch only cache_hit / cache_miss rows — small set at MVP scale.
    event_rows = (
        await db.execute(
            select(AnalyticsEvent.event_type, AnalyticsEvent.event_metadata).where(
                AnalyticsEvent.event_type.in_(
                    [AnalyticsEventType.cache_hit, AnalyticsEventType.cache_miss]
                )
            )
        )
    ).all()

    # {resource_type: [hits, misses]}
    ev_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for ev_type, metadata in event_rows:
        rt = (metadata or {}).get("resource_type")
        if not rt:
            continue
        if ev_type == AnalyticsEventType.cache_hit:
            ev_counts[rt][0] += 1
        else:
            ev_counts[rt][1] += 1

    # ── merge and build response ──────────────────────────────────────────────
    stats: list[ResourceCacheStats] = []
    total_event_hits = 0
    total_event_reqs = 0

    for row in cache_rows:
        rt = str(row.resource_type)
        ev_hits, ev_misses = ev_counts.get(rt, [0, 0])
        total_event_hits += ev_hits
        total_event_reqs += ev_hits + ev_misses
        stats.append(
            ResourceCacheStats(
                resource_type=rt,
                cache_entries=int(row.cache_entries),
                total_hits=int(row.total_hits or 0),
                avg_hit_count=round(float(row.avg_hit_count or 1.0), 2),
                event_hits=ev_hits,
                event_misses=ev_misses,
            )
        )

    stats.sort(key=lambda s: s.total_hits, reverse=True)

    overall = (
        round(total_event_hits / total_event_reqs * 100, 1)
        if total_event_reqs > 0
        else None
    )

    return CacheStatsResponse(stats=stats, overall_hit_rate_pct=overall)
