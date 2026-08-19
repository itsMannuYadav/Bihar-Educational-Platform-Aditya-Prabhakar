import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_claims, get_db
from app.db.repositories.curriculum_repository import list_chapters, list_classes, list_subjects
from app.schemas.curriculum import ChapterRead, ClassRead, SubjectRead

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
