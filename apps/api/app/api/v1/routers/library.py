import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.repositories import library_repository as repo
from app.schemas.library import SavedLessonRead, SavedLessonsPage, SaveLessonRequest

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/saved")
async def list_saved(
    cursor: str | None = Query(None, description="ISO-format saved_at of last seen item"),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedLessonsPage:
    cursor_dt: datetime | None = None
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid cursor — must be an ISO-format timestamp",
            ) from exc

    items, next_dt = await repo.list_saved_lessons(
        db, user_id=user.id, cursor=cursor_dt, limit=limit
    )
    return SavedLessonsPage(
        items=items,
        next_cursor=next_dt.isoformat() if next_dt else None,
    )


@router.post("/saved", status_code=status.HTTP_201_CREATED)
async def save_lesson(
    body: SaveLessonRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedLessonRead:
    try:
        return await repo.save_lesson(
            db, user_id=user.id, request_id=body.request_id, note=body.note
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not save lesson — request_id may not exist",
        ) from exc


@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_lesson(
    saved_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    removed = await repo.unsave_lesson(db, saved_id=saved_id, user_id=user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved lesson not found"
        )


@router.get("/saved/by-request/{request_id}")
async def get_saved_by_request(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedLessonRead:
    saved = await repo.get_saved_by_request(db, user_id=user.id, request_id=request_id)
    if saved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not saved")
    return saved


@router.get("/search")
async def search_library(
    q: str = Query("", description="Search text — matches chapter and subject names"),
    class_id: uuid.UUID | None = Query(None),
    subject_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedLessonRead]:
    return await repo.search_saved_lessons(
        db,
        user_id=user.id,
        q=q.strip(),
        class_id=class_id,
        subject_id=subject_id,
        limit=limit,
    )
