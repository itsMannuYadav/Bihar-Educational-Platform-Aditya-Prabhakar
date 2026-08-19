import uuid

from sqlalchemy import JSON, Boolean, CheckConstraint, Enum, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import Difficulty, QuestionType


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False, index=True
    )
    type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), nullable=False
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    options: Mapped[list | None] = mapped_column(JSON)
    answer: Mapped[str | None] = mapped_column(String)
    explanation: Mapped[str | None] = mapped_column(String)
    is_previous_year: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Presentation(Base):
    __tablename__ = "presentations"
    __table_args__ = (
        CheckConstraint("slide_count in (5, 10, 15)", name="ck_presentations_slide_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False
    )
    slide_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    slides: Mapped[dict] = mapped_column(JSON, nullable=False)
    pptx_url: Mapped[str | None] = mapped_column(String)
    pdf_url: Mapped[str | None] = mapped_column(String)
    canva_export_ref: Mapped[str | None] = mapped_column(String)


class AudioResource(Base):
    __tablename__ = "audio_resources"
    __table_args__ = (
        CheckConstraint(
            "duration_variant in (1, 3, 5)", name="ck_audio_resources_duration_variant"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False
    )
    duration_variant: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    audio_url: Mapped[str] = mapped_column(String, nullable=False)
    transcript: Mapped[str] = mapped_column(String, nullable=False)
    tts_provider: Mapped[str] = mapped_column(String, nullable=False)


class MindMap(Base):
    __tablename__ = "mind_maps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False
    )
    structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    svg_url: Mapped[str | None] = mapped_column(String)
    png_url: Mapped[str | None] = mapped_column(String)


class Worksheet(Base):
    __tablename__ = "worksheets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generated_resources.id"), nullable=False
    )
    sections: Mapped[list] = mapped_column(JSON, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String)
