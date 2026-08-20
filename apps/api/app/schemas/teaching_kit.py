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
    # Denormalized for the result page's breadcrumb and badges. Returned here
    # rather than left to the client, which would otherwise need three extra
    # catalog round trips just to title the page it is already loading.
    class_display_name: str
    subject_name: str
    chapter_name: str
    language: AppLanguage
    duration: DurationOption
    teaching_mode: TeachingMode
    requested_resource_types: list[ResourceType]
    resources: list[GeneratedResourceRead]


class ResourceReadyEvent(CamelReadModel):
    resource_type: ResourceType
    resource_id: uuid.UUID
    cache_hit: bool


class KitCompleteEvent(CamelReadModel):
    request_id: uuid.UUID
    status: KitStatus
    duration_ms: int


class RegenerateResourceRequest(CamelRequestModel):
    """Type-specific re-roll knobs (docs/03-api-design.md §5) — e.g. questions
    take `{difficulty, count, types}`, worksheets take `{sections}`. Kept as a
    free-form dict rather than a union: it also feeds the cache key, so a
    re-roll with different params is a distinct cacheable resource.
    """

    params: dict = Field(default_factory=dict)
