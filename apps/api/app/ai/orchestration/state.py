import operator
import uuid
from typing import Annotated, TypedDict


class ResourceResult(TypedDict):
    resource_type: str
    resource_id: uuid.UUID
    cache_hit: bool


class TeachingKitState(TypedDict):
    request_id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    chapter_id: uuid.UUID
    language: str
    duration: str
    teaching_mode: str
    resource_types: list[str]
    # Only meaningful inside a Send-dispatched fan-out branch (see graph.py).
    current_resource_type: str
    resources: Annotated[list[ResourceResult], operator.add]
    # Set once by generate_lesson_plan_node before the fan-out runs; every
    # other node reads it for grounding (docs/01-architecture.md §3 — lesson
    # plan is "the shared source of truth every other resource references").
    # Plain overwrite, not accumulated: only one node ever sets it.
    lesson_plan_content: dict
