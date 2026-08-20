import uuid

from sqlalchemy import func, select
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


async def get_or_create_chapter(db: AsyncSession, *, subject_id: uuid.UUID, name: str) -> Chapter:
    """Backs a teacher typing a chapter name the seeded catalog doesn't have.

    Case-insensitive match first, so "Heat" and "heat" from two different
    teachers land on the same chapter (and the same cache) instead of
    quietly forking the catalog. `sequence_no` is left null rather than
    guessed, since there's no syllabus position to put it at — verified
    directly rather than assumed: Postgres sorts null last for ascending
    order, so on the real database a teacher-added chapter takes its place
    after the reviewed, numbered ones. SQLite (the test database) sorts
    null *first* for the same query — a real platform difference, not a bug
    — so tests here don't assert ordering relative to numbered chapters.
    """
    name = name.strip()
    existing = await db.execute(
        select(Chapter).where(
            Chapter.subject_id == subject_id, func.lower(Chapter.name) == name.lower()
        )
    )
    chapter = existing.scalar_one_or_none()
    if chapter is not None:
        return chapter

    chapter = Chapter(subject_id=subject_id, name=name)
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter
