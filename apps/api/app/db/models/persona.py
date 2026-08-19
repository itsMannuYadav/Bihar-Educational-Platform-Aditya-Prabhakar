import uuid

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TeachingPersona(Base):
    __tablename__ = "teaching_personas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    characteristics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    prompt_fragment: Mapped[str] = mapped_column(String, nullable=False)
