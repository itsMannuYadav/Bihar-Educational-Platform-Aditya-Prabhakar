from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from app.ai.orchestration.nodes.lesson_plan import generate_lesson_plan_node
from app.ai.orchestration.nodes.stubs import generate_resource_stub_node
from app.ai.orchestration.state import TeachingKitState
from app.db.models.enums import ResourceType


def _route_after_lesson_plan(state: TeachingKitState) -> list[Send]:
    """`generate_lesson_plan` always runs first (it's the shared source of
    truth every other resource references — docs/01-architecture.md §3);
    everything else fans out in parallel via LangGraph's Send/map-reduce API.
    """
    return [
        Send("generate_resource", {**state, "current_resource_type": resource_type})
        for resource_type in state["resource_types"]
        if resource_type != ResourceType.lesson_plan.value
    ]


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(TeachingKitState)
    graph.add_node("generate_lesson_plan", generate_lesson_plan_node)
    graph.add_node("generate_resource", generate_resource_stub_node)
    graph.add_edge(START, "generate_lesson_plan")
    graph.add_conditional_edges(
        "generate_lesson_plan", _route_after_lesson_plan, ["generate_resource"]
    )
    graph.add_edge("generate_resource", END)
    return graph.compile()
