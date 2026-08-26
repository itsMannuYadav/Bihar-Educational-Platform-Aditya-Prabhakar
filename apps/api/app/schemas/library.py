import uuid
from datetime import datetime

from app.db.models.enums import AppLanguage, DurationOption, TeachingMode
from app.schemas.base import CamelReadModel, CamelRequestModel


class SaveLessonRequest(CamelRequestModel):
    request_id: uuid.UUID
    note: str | None = None


class SavedLessonRead(CamelReadModel):
    id: uuid.UUID
    request_id: uuid.UUID
    note: str | None
    saved_at: datetime
    class_display_name: str
    subject_name: str
    chapter_name: str
    language: AppLanguage
    duration: DurationOption
    teaching_mode: TeachingMode


class SavedLessonsPage(CamelReadModel):
    items: list[SavedLessonRead]
    next_cursor: str | None
