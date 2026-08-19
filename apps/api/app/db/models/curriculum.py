import uuid

from sqlalchemy import JSON, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, default="Bihar")


class SchoolClass(Base):
    """A grade level, e.g. "Class 7". Named `SchoolClass` to avoid colliding
    with the `class` keyword; maps to the `classes` table from the schema doc.
    """

    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("boards.id"), nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    sequence_no: Mapped[int | None] = mapped_column(SmallInteger)
    # Doc sketch says `text[]`; stored as JSON here so the in-memory SQLite
    # test DB (no portable ARRAY DDL compiler) can create this table too.
    syllabus_topics: Mapped[list[str] | None] = mapped_column(JSON)
