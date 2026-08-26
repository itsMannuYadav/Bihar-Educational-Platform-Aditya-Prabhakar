import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import (
    AppLanguage,
    DurationOption,
    KitStatus,
    ResourceType,
    TeachingMode,
    db_enum,
)


class TeachingKitRequest(Base):
    __tablename__ = "teaching_kit_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    chapter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    language: Mapped[AppLanguage] = mapped_column(
        db_enum(AppLanguage, "app_language"), nullable=False
    )
    duration: Mapped[DurationOption] = mapped_column(
        db_enum(DurationOption, "duration_option"), nullable=False
    )
    teaching_mode: Mapped[TeachingMode] = mapped_column(
        db_enum(TeachingMode, "teaching_mode"), nullable=False, default=TeachingMode.concept
    )
    raw_query: Mapped[str | None] = mapped_column(String)
    status: Mapped[KitStatus] = mapped_column(
        db_enum(KitStatus, "kit_status"), nullable=False, default=KitStatus.pending
    )
    # Not in the original schema doc sketch: /teaching-kit/generate hands off
    # to /stream, which only gets request_id — the requested resource types
    # have to be persisted somewhere for /stream to know what to generate.
    resource_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GeneratedResource(Base):
    __tablename__ = "generated_resources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teaching_kit_requests.id"), nullable=False, index=True
    )
    # No FK yet — resource_cache is created in a later migration; the
    # constraint is added there via ALTER TABLE (see docs/02-database-schema.md
    # §4, resource_cache.canonical_resource_id references this table right back).
    cache_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resource_cache.id", use_alter=True, name="fk_generated_resources_cache_id")
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        db_enum(ResourceType, "resource_type"), nullable=False, index=True
    )
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    file_url: Mapped[str | None] = mapped_column(String)
    language: Mapped[AppLanguage] = mapped_column(
        db_enum(AppLanguage, "app_language"), nullable=False
    )
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
