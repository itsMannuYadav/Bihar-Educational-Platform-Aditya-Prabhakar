import hashlib
import json
import uuid

from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode


def compute_cache_key(
    *,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    chapter_id: uuid.UUID,
    language: AppLanguage,
    duration: DurationOption,
    teaching_mode: TeachingMode,
    resource_type: ResourceType,
    params: dict,
) -> str:
    """sha256(class_id|subject_id|chapter_id|language|duration|teaching_mode|resource_type|sorted(params))
    per docs/02-database-schema.md §4. Must match apps/web/lib/cache-keys.ts exactly
    once that lands (frontend/backend cache-key parity is the point).
    """
    raw = "|".join(
        [
            str(class_id),
            str(subject_id),
            str(chapter_id),
            language.value,
            duration.value,
            teaching_mode.value,
            resource_type.value,
            json.dumps(params, sort_keys=True, separators=(",", ":")),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
