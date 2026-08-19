import uuid
from datetime import datetime

from pydantic import Field

from app.db.models.enums import (
    MVP_RESOURCE_TYPES,
    AppLanguage,
    DurationOption,
    KitStatus,
    ResourceType,
    TeachingMode,
)
from app.schemas.base import CamelReadModel, CamelRequestModel


class GenerateTeachingKitRequest(CamelRequestModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    chapter_id: uuid.UUID
    language: AppLanguage
    duration: DurationOption
    teaching_mode: TeachingMode = TeachingMode.concept
    raw_query: str | None = None
    resource_types: list[ResourceType] = Field(default_factory=lambda: list(MVP_RESOURCE_TYPES))


class TeachingKitRequestSummary(CamelReadModel):
    request_id: uuid.UUID
    status: KitStatus
    stream_url: str


class GeneratedResourceRead(CamelReadModel):
    id: uuid.UUID
    resource_type: ResourceType
    content: dict
    file_url: str | None
    language: AppLanguage
    cache_hit: bool
    created_at: datetime


class TeachingKitStateRead(CamelReadModel):
    request_id: uuid.UUID
    status: KitStatus
    resources: list[GeneratedResourceRead]


class ResourceReadyEvent(CamelReadModel):
    resource_type: ResourceType
    resource_id: uuid.UUID
    cache_hit: bool


class KitCompleteEvent(CamelReadModel):
    request_id: uuid.UUID
    status: KitStatus
    duration_ms: int
