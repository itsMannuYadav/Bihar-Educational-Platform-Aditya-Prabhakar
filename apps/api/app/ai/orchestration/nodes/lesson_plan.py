from langchain_core.runnables import RunnableConfig

from app.ai.orchestration.nodes.base import run_resource_node
from app.ai.orchestration.nodes.registry import RESOURCE_SPECS
from app.ai.orchestration.state import TeachingKitState
from app.ai.providers.llm.base import LLMProvider
from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode


async def generate_lesson_plan_node(state: TeachingKitState, config: RunnableConfig) -> dict:
    """Runs first and alone: every other node grounds itself in this output
    (docs/01-architecture.md §3), so its content goes back into state for the
    fan-out branches to read.
    """
    configurable = config["configurable"]
    llm_provider: LLMProvider = configurable["llm_provider"]

    generation = await run_resource_node(
        spec=RESOURCE_SPECS[ResourceType.lesson_plan],
        session_factory=configurable["session_factory"],
        llm_provider=llm_provider,
        request_id=state["request_id"],
        class_id=state["class_id"],
        subject_id=state["subject_id"],
        chapter_id=state["chapter_id"],
        language=AppLanguage(state["language"]),
        duration=DurationOption(state["duration"]),
        teaching_mode=TeachingMode(state["teaching_mode"]),
        lesson_plan_content={},
    )
    return {
        "resources": [generation.as_result(ResourceType.lesson_plan)],
        "lesson_plan_content": generation.content,
    }
