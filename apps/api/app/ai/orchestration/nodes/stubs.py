from langchain_core.runnables import RunnableConfig

from app.ai.orchestration.state import ResourceResult, TeachingKitState
from app.db.models.enums import AppLanguage, ResourceType
from app.db.repositories.teaching_kit_repository import create_generated_resource

# Placeholder content for MVP resource types that aren't real nodes yet
# (Phase 4b replaces each of these with a real, cached generation node —
# see docs/07-roadmap.md). No cache bookkeeping here: there's nothing worth
# caching about a stub.
PLACEHOLDER_CONTENT: dict[ResourceType, dict] = {
    ResourceType.teaching_script: {
        "placeholder": True,
        "note": "Teaching script generation lands in Phase 4b.",
    },
    ResourceType.questions: {
        "placeholder": True,
        "note": "Question bank generation lands in Phase 4b.",
    },
    ResourceType.worksheet: {
        "placeholder": True,
        "note": "Worksheet generation lands in Phase 4b.",
    },
    ResourceType.presentation: {
        "placeholder": True,
        "note": "Presentation generation lands in Phase 4b.",
    },
    ResourceType.mind_map: {
        "placeholder": True,
        "note": "Mind map generation lands in Phase 4b.",
    },
    ResourceType.audio: {
        "placeholder": True,
        "note": "Audio generation lands in Phase 5.",
    },
}


async def generate_resource_stub_node(state: TeachingKitState, config: RunnableConfig) -> dict:
    # See lesson_plan.py / orchestrator.py: each concurrently fanned-out
    # branch owns its own session rather than sharing one.
    session_factory = config["configurable"]["session_factory"]
    resource_type = ResourceType(state["current_resource_type"])
    language = AppLanguage(state["language"])

    content = PLACEHOLDER_CONTENT.get(
        resource_type,
        {"placeholder": True, "note": f"{resource_type.value} generation not implemented yet."},
    )

    async with session_factory() as db:
        resource = await create_generated_resource(
            db,
            request_id=state["request_id"],
            resource_type=resource_type,
            content=content,
            language=language,
        )
        await db.commit()
        return {
            "resources": [
                ResourceResult(
                    resource_type=resource_type.value, resource_id=resource.id, cache_hit=False
                )
            ]
        }
