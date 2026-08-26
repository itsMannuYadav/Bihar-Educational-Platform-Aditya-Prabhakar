import uuid
from collections.abc import AsyncIterator
from typing import Protocol

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.graph import build_graph
from app.ai.orchestration.state import TeachingKitState
from app.ai.providers.embedding.base import EmbeddingProvider
from app.ai.providers.llm.base import LLMProvider
from app.db.models.enums import KitStatus
from app.db.repositories.teaching_kit_repository import get_request, update_request_status
from app.schemas.teaching_kit import ResourceReadyEvent


class OrchestratorClient(Protocol):
    async def run(self, request_id: uuid.UUID) -> AsyncIterator[ResourceReadyEvent]: ...


class InProcessOrchestrator:
    """Runs the LangGraph teaching-kit graph in-process and streams each
    resource as it completes — matches docs/03-api-design.md §10's "invoked
    in-process for MVP scale" note.

    Nodes fan out *concurrently* (LangGraph's Send API — docs/01-architecture.md
    §3's "fans out in parallel"), so every node opens its own short-lived DB
    session via `session_factory` rather than sharing one `AsyncSession`
    instance — a single session isn't safe for concurrent use from multiple
    tasks (confirmed the hard way: sharing one session here corrupted
    mid-flush and raised `PendingRollbackError` under concurrent fan-out).

    No reconnect/resume if the caller disconnects mid-stream: generation is
    tied to this async generator's lifetime. Robust background-worker +
    pub/sub delivery is a Phase 7+ hardening concern, not this skeleton.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        llm_provider: LLMProvider,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._llm_provider = llm_provider
        self._embedding_provider = embedding_provider
        self._graph = build_graph()

    async def run(self, request_id: uuid.UUID) -> AsyncIterator[ResourceReadyEvent]:
        async with self._session_factory() as db:
            request = await get_request(db, request_id)
            if request is None:
                raise ValueError(f"teaching_kit_requests {request_id} not found")
            await update_request_status(db, request_id, KitStatus.generating)

            initial_state: TeachingKitState = {
                "request_id": request.id,
                "class_id": request.class_id,
                "subject_id": request.subject_id,
                "chapter_id": request.chapter_id,
                "language": request.language.value,
                "duration": request.duration.value,
                "teaching_mode": request.teaching_mode.value,
                "resource_types": request.resource_types,
                "current_resource_type": "",
                "resources": [],
                "lesson_plan_content": {},
                "raw_query": request.raw_query,
            }

        config: RunnableConfig = {
            "configurable": {
                "session_factory": self._session_factory,
                "llm_provider": self._llm_provider,
                "embedding_provider": self._embedding_provider,
            }
        }
        async for update in self._graph.astream(
            initial_state, config=config, stream_mode="updates"
        ):
            for node_output in update.values():
                for result in node_output.get("resources", []):
                    yield ResourceReadyEvent(
                        resource_type=result["resource_type"],
                        resource_id=result["resource_id"],
                        cache_hit=result["cache_hit"],
                    )

        async with self._session_factory() as db:
            await update_request_status(db, request_id, KitStatus.complete)
