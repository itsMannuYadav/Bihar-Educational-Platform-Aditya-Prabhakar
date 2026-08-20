import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import AppLanguage, ResourceType, db_enum


class ResourceCache(Base):
    __tablename__ = "resource_cache"
    __table_args__ = (
        Index(
            "idx_cache_lookup", "class_id", "subject_id", "chapter_id", "language", "resource_type"
        ),
        Index(
            "idx_cache_embedding",
            "query_embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": "100"},
            postgresql_ops={"query_embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cache_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    chapter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    language: Mapped[AppLanguage] = mapped_column(
        db_enum(AppLanguage, "app_language"), nullable=False
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        db_enum(ResourceType, "resource_type"), nullable=False
    )
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    canonical_resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False
    )
    query_embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
