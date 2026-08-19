import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedLesson(Base):
    __tablename__ = "saved_lessons"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teaching_kit_requests.id"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "idx_saved_unique",
            "user_id",
            "request_id",
            unique=True,
            # Postgres-only predicate; other dialects (SQLite, in tests) just
            # get a plain unique index, a stricter but harmless subset.
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
