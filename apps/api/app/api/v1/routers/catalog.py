import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_claims, get_db
from app.db.repositories.curriculum_repository import (
    get_or_create_chapter,
    list_chapters,
    list_classes,
    list_subjects,
)
from app.schemas.curriculum import ChapterRead, ClassRead, CreateChapterRequest, SubjectRead

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/classes", response_model=list[ClassRead])
async def get_classes(
    board_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _claims=Depends(get_current_claims),
) -> list[ClassRead]:
    classes = await list_classes(db, board_id=board_id)
    return [ClassRead.model_validate(c) for c in classes]


@router.get("/subjects", response_model=list[SubjectRead])
async def get_subjects(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _claims=Depends(get_current_claims),
) -> list[SubjectRead]:
    subjects = await list_subjects(db, class_id=class_id)
    return [SubjectRead.model_validate(s) for s in subjects]


@router.get("/chapters", response_model=list[ChapterRead])
async def get_chapters(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _claims=Depends(get_current_claims),
) -> list[ChapterRead]:
    chapters = await list_chapters(db, subject_id=subject_id)
    return [ChapterRead.model_validate(c) for c in chapters]


@router.post("/chapters", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    payload: CreateChapterRequest,
    db: AsyncSession = Depends(get_db),
    _claims=Depends(get_current_claims),
) -> ChapterRead:
    """Lets a teacher add a chapter the seeded catalog doesn't have yet,
    rather than blocking generation on content work catching up to every
    class/subject combination. Get-or-create: a name that already exists for
    this subject returns the existing chapter instead of forking it, so two
    teachers typing "Heat" land on the same catalog entry and the same
    cache.
    """
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chapter_name_empty")
    chapter = await get_or_create_chapter(db, subject_id=payload.subject_id, name=name)
    return ChapterRead.model_validate(chapter)
