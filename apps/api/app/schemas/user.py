import uuid
from datetime import datetime

from app.db.models.enums import AppLanguage, UserRole
from app.schemas.base import CamelReadModel, CamelRequestModel


class UserRead(CamelReadModel):
    id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    role: UserRole
    school_id: uuid.UUID | None
    preferred_language: AppLanguage
    created_at: datetime


class UserCreate(CamelRequestModel):
    name: str
    school_id: uuid.UUID | None = None
    preferred_language: AppLanguage = AppLanguage.hi
