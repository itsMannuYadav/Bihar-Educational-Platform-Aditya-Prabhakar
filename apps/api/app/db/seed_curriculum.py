"""Seed the Bihar curriculum catalog (board, classes 6-10, core subjects) so
the `/catalog` endpoints have real data to serve. Chapters are seeded in full
for Class 7 Science only — enough to demo Phase 4 end-to-end; the rest of the
chapter catalog is ongoing content work, not a blocking Phase 3 task (see
docs/07-roadmap.md Phase 3).

Run with: uv run python -m app.db.seed_curriculum
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.session import async_session_factory

CORE_SUBJECTS = ["Science", "Social Science", "Math", "Hindi", "English"]

# Real NCERT Class 7 Science chapter list (BSEB is NCERT-aligned).
CLASS_7_SCIENCE_CHAPTERS = [
    "Nutrition in Plants",
    "Nutrition in Animals",
    "Fibre to Fabric",
    "Heat",
    "Acids, Bases and Salts",
    "Physical and Chemical Changes",
    "Weather, Climate and Adaptations of Animals to Climate",
    "Winds, Storms and Cyclones",
    "Soil",
    "Respiration in Organisms",
    "Transportation in Animals and Plants",
    "Reproduction in Plants",
    "Motion and Time",
    "Electric Current and its Effects",
    "Light",
    "Water: A Precious Resource",
    "Forests: Our Lifeline",
    "Wastewater Story",
]


async def _get_or_create_board(db: AsyncSession) -> Board:
    board = (await db.execute(select(Board).where(Board.name == "BSEB"))).scalar_one_or_none()
    if board is None:
        board = Board(name="BSEB", state="Bihar")
        db.add(board)
        await db.flush()
    return board


async def seed_curriculum() -> None:
    async with async_session_factory() as db:
        board = await _get_or_create_board(db)

        existing_classes = {
            c.grade: c
            for c in (await db.execute(select(SchoolClass).where(SchoolClass.board_id == board.id)))
            .scalars()
            .all()
        }

        classes_by_grade = dict(existing_classes)
        for grade in range(6, 11):
            if grade not in classes_by_grade:
                school_class = SchoolClass(
                    board_id=board.id, grade=grade, display_name=f"Class {grade}"
                )
                db.add(school_class)
                classes_by_grade[grade] = school_class
        await db.flush()

        existing_subjects = {
            (s.class_id, s.name)
            for s in (
                await db.execute(
                    select(Subject).where(
                        Subject.class_id.in_(c.id for c in classes_by_grade.values())
                    )
                )
            )
            .scalars()
            .all()
        }

        subjects_by_key: dict[tuple[int, str], Subject] = {}
        for grade, school_class in classes_by_grade.items():
            for subject_name in CORE_SUBJECTS:
                if (school_class.id, subject_name) not in existing_subjects:
                    subject = Subject(class_id=school_class.id, name=subject_name)
                    db.add(subject)
                    subjects_by_key[(grade, subject_name)] = subject
        await db.flush()

        class_7_science = (
            subjects_by_key.get((7, "Science"))
            or (
                await db.execute(
                    select(Subject).where(
                        Subject.class_id == classes_by_grade[7].id, Subject.name == "Science"
                    )
                )
            ).scalar_one()
        )

        existing_chapter_names = {
            name
            for (name,) in (
                await db.execute(
                    select(Chapter.name).where(Chapter.subject_id == class_7_science.id)
                )
            ).all()
        }
        for sequence_no, chapter_name in enumerate(CLASS_7_SCIENCE_CHAPTERS, start=1):
            if chapter_name not in existing_chapter_names:
                db.add(
                    Chapter(
                        subject_id=class_7_science.id,
                        name=chapter_name,
                        sequence_no=sequence_no,
                    )
                )

        await db.commit()
        print(
            f"Seeded curriculum: board={board.name}, "
            f"classes={len(classes_by_grade)}, subjects_added={len(subjects_by_key)}, "
            f"class_7_science_chapters={len(CLASS_7_SCIENCE_CHAPTERS)}"
        )


if __name__ == "__main__":
    asyncio.run(seed_curriculum())
