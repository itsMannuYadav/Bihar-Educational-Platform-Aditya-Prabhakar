import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.analytics import AnalyticsEvent
from app.db.models.enums import AnalyticsEventType

logger = logging.getLogger(__name__)

__all__ = ["log_event"]


async def log_event(
    db: AsyncSession,
    *,
    event_type: AnalyticsEventType,
    metadata: dict,
    user_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
) -> None:
    """Fire-and-forget analytics write.

    Failures are logged but never re-raised — an analytics write must never
    take down a generation or a cache hit.
    """
    try:
        db.add(
            AnalyticsEvent(
                user_id=user_id,
                school_id=school_id,
                event_type=event_type,
                event_metadata=metadata,
            )
        )
        await db.flush()
    except Exception:
        logger.warning("analytics write failed (non-fatal)", exc_info=True)
