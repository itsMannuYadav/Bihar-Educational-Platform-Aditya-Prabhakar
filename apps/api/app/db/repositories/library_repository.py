import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, or_, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Chapter, SchoolClass, Subject
from app.db.models.saved_lesson import SavedLesson
from app.db.models.teaching_kit import TeachingKitRequest
from app.schemas.library import SavedLessonRead

# ---------------------------------------------------------------------------
# Base join shared across all list / search queries
# ---------------------------------------------------------------------------

_SAVED_COLS = (
    select(
        SavedLesson.id,
        SavedLesson.request_id,
        SavedLesson.note,
        SavedLesson.saved_at,
        TeachingKitRequest.language,
        TeachingKitRequest.duration,
        TeachingKitRequest.teaching_mode,
        Chapter.name.label("chapter_name"),
        Subject.name.label("subject_name"),
        SchoolClass.display_name.label("class_display_name"),
    )
    .join(TeachingKitRequest, SavedLesson.request_id == TeachingKitRequest.id)
    .join(Chapter, TeachingKitRequest.chapter_id == Chapter.id)
    .join(Subject, TeachingKitRequest.subject_id == Subject.id)
    .join(SchoolClass, TeachingKitRequest.class_id == SchoolClass.id)
)


def _to_schema(row: Row) -> SavedLessonRead:  # type: ignore[type-arg]
    return SavedLessonRead.model_validate(dict(row._mapping))


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


async def save_lesson(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    request_id: uuid.UUID,
    note: str | None,
) -> SavedLessonRead:
    # Re-activate a soft-deleted record rather than forking the unique index.
    existing_result = await db.execute(
        select(SavedLesson).where(
            SavedLesson.user_id == user_id,
            SavedLesson.request_id == request_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        existing.deleted_at = None
        existing.note = note
        existing.saved_at = func.now()  # type: ignore[assignment]
        await db.commit()
        await db.refresh(existing)
    else:
        existing = SavedLesson(user_id=user_id, request_id=request_id, note=note)
        db.add(existing)
        await db.commit()
        await db.refresh(existing)

    row = await db.execute(
        _SAVED_COLS.where(
            SavedLesson.id == existing.id,
            SavedLesson.deleted_at.is_(None),
        )
    )
    result = row.one()
    return _to_schema(result)


async def unsave_lesson(
    db: AsyncSession,
    *,
    saved_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        select(SavedLesson).where(
            SavedLesson.id == saved_id,
            SavedLesson.user_id == user_id,
            SavedLesson.deleted_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    row.deleted_at = datetime.now(tz=UTC)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


async def list_saved_lessons(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    cursor: datetime | None,
    limit: int,
) -> tuple[list[SavedLessonRead], datetime | None]:
    stmt = _SAVED_COLS.where(
        SavedLesson.user_id == user_id,
        SavedLesson.deleted_at.is_(None),
    ).order_by(desc(SavedLesson.saved_at))
    if cursor is not None:
        stmt = stmt.where(SavedLesson.saved_at < cursor)
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = result.all()

    has_more = len(rows) > limit
    items = [_to_schema(r) for r in rows[:limit]]
    next_cursor = items[-1].saved_at if has_more else None
    return items, next_cursor


async def get_saved_by_request(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    request_id: uuid.UUID,
) -> SavedLessonRead | None:
    result = await db.execute(
        _SAVED_COLS.where(
            SavedLesson.user_id == user_id,
            SavedLesson.request_id == request_id,
            SavedLesson.deleted_at.is_(None),
        )
    )
    row = result.one_or_none()
    return _to_schema(row) if row is not None else None


async def search_saved_lessons(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    q: str,
    class_id: uuid.UUID | None,
    subject_id: uuid.UUID | None,
    limit: int,
) -> list[SavedLessonRead]:
    stmt = _SAVED_COLS.where(
        SavedLesson.user_id == user_id,
        SavedLesson.deleted_at.is_(None),
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Chapter.name.ilike(pattern),
                Subject.name.ilike(pattern),
            )
        )
    if class_id is not None:
        stmt = stmt.where(SchoolClass.id == class_id)
    if subject_id is not None:
        stmt = stmt.where(Subject.id == subject_id)

    stmt = stmt.order_by(desc(SavedLesson.saved_at)).limit(limit)
    result = await db.execute(stmt)
    return [_to_schema(r) for r in result.all()]
