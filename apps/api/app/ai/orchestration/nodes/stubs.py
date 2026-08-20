import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.state import ResourceResult
from app.db.models.enums import AppLanguage, ResourceType
from app.db.repositories.teaching_kit_repository import create_generated_resource

# Resource types the API and schema already model but no node generates yet.
# Everything in docs/07-roadmap.md's MVP set except these is a real node as of
# Phase 4b; these keep the kit's tab list and SSE stream complete meanwhile.
# No cache bookkeeping — there's nothing worth caching about a placeholder.
PLACEHOLDER_CONTENT: dict[ResourceType, dict] = {
    ResourceType.audio: {
        "placeholder": True,
        "note": "Audio generation lands in Phase 5.",
    },
    ResourceType.animation: {
        "placeholder": True,
        "note": "Animation generation is deferred post-MVP.",
    },
}


async def generate_placeholder_resource(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    request_id: uuid.UUID,
    resource_type: ResourceType,
    language: AppLanguage,
) -> ResourceResult:
    content = PLACEHOLDER_CONTENT.get(
        resource_type,
        {"placeholder": True, "note": f"{resource_type.value} generation not implemented yet."},
    )
    async with session_factory() as db:
        resource = await create_generated_resource(
            db,
            request_id=request_id,
            resource_type=resource_type,
            content=content,
            language=language,
        )
        await db.commit()
    return ResourceResult(
        resource_type=resource_type.value, resource_id=resource.id, cache_hit=False
    )
