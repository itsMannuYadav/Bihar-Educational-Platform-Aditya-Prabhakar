import uuid

from app.schemas.base import CamelReadModel, CamelRequestModel


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


class CreateChapterRequest(CamelRequestModel):
    """A teacher typing a chapter the seeded catalog doesn't have yet — the
    seed script only covers Class 7 Science end to end (docs/07-roadmap.md
    Phase 3), so every other class/subject combination has no chapters at
    all until either content work catches up or a teacher adds one this way.
    """

    subject_id: uuid.UUID
    name: str
