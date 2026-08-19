import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Chapter, SchoolClass, Subject


async def get_class_by_id(db: AsyncSession, class_id: uuid.UUID) -> SchoolClass | None:
    result = await db.execute(select(SchoolClass).where(SchoolClass.id == class_id))
    return result.scalar_one_or_none()


async def get_subject_by_id(db: AsyncSession, subject_id: uuid.UUID) -> Subject | None:
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def get_chapter_by_id(db: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    return result.scalar_one_or_none()


async def list_classes(db: AsyncSession, *, board_id: uuid.UUID | None = None) -> list[SchoolClass]:
    stmt = select(SchoolClass)
    if board_id:
        stmt = stmt.where(SchoolClass.board_id == board_id)
    stmt = stmt.order_by(SchoolClass.grade)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_subjects(db: AsyncSession, *, class_id: uuid.UUID) -> list[Subject]:
    stmt = select(Subject).where(Subject.class_id == class_id).order_by(Subject.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_chapters(db: AsyncSession, *, subject_id: uuid.UUID) -> list[Chapter]:
    stmt = (
        select(Chapter)
        .where(Chapter.subject_id == subject_id)
        .order_by(Chapter.sequence_no, Chapter.name)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
