import uuid

from app.schemas.base import CamelReadModel


class SchoolRead(CamelReadModel):
    id: uuid.UUID
    name: str
    state: str
    district: str | None
    block: str | None
