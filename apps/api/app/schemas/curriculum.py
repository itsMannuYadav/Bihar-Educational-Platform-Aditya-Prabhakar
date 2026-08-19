import uuid

from app.schemas.base import CamelReadModel


class BoardRead(CamelReadModel):
    id: uuid.UUID
    name: str
    state: str


class ClassRead(CamelReadModel):
    id: uuid.UUID
    board_id: uuid.UUID
    grade: int
    display_name: str


class SubjectRead(CamelReadModel):
    id: uuid.UUID
    class_id: uuid.UUID
    name: str


class ChapterRead(CamelReadModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    sequence_no: int | None
    syllabus_topics: list[str] | None
