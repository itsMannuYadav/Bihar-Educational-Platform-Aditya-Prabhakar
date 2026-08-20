from langchain_core.runnables import RunnableConfig

from app.ai.orchestration.nodes.base import run_resource_node
from app.ai.orchestration.nodes.registry import RESOURCE_SPECS
from app.ai.orchestration.nodes.stubs import generate_placeholder_resource
from app.ai.orchestration.state import TeachingKitState
from app.ai.providers.llm.base import LLMProvider
from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode


async def generate_resource_node(state: TeachingKitState, config: RunnableConfig) -> dict:
    """The fan-out branch: generates whichever resource type this `Send` carried.

    One node handles every type rather than one graph node per type, because
    the graph shape is identical for all of them and `Send` already carries the
    discriminator in `current_resource_type`.
    """
    configurable = config["configurable"]
    session_factory = configurable["session_factory"]
    llm_provider: LLMProvider = configurable["llm_provider"]

    resource_type = ResourceType(state["current_resource_type"])
    language = AppLanguage(state["language"])

    spec = RESOURCE_SPECS.get(resource_type)
    if spec is None:
        # Types that are schema/API-ready but have no generator yet (audio →
        # Phase 5, animation/video → post-MVP). Still produces a real row so
        # the kit's SSE stream and result tabs stay consistent.
        result = await generate_placeholder_resource(
            session_factory,
            request_id=state["request_id"],
            resource_type=resource_type,
            language=language,
        )
        return {"resources": [result]}

    generation = await run_resource_node(
        spec=spec,
        session_factory=session_factory,
        llm_provider=llm_provider,
        request_id=state["request_id"],
        class_id=state["class_id"],
        subject_id=state["subject_id"],
        chapter_id=state["chapter_id"],
        language=language,
        duration=DurationOption(state["duration"]),
        teaching_mode=TeachingMode(state["teaching_mode"]),
        lesson_plan_content=state["lesson_plan_content"],
    )
    return {"resources": [generation.as_result(resource_type)]}
