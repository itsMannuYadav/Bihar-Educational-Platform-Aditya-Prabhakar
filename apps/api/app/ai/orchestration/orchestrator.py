import time
import uuid
from collections.abc import AsyncIterator
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestration.graph import build_graph
from app.ai.providers.llm.base import LLMProvider
from app.db.models.enums import KitStatus
from app.db.repositories.teaching_kit_repository import get_request, update_request_status
from app.schemas.teaching_kit import KitCompleteEvent, ResourceReadyEvent


class OrchestratorClient(Protocol):
    async def run(self, request_id: uuid.UUID) -> AsyncIterator[ResourceReadyEvent]: ...


class InProcessOrchestrator:
    """Runs the LangGraph teaching-kit graph in-process and streams each
    resource as it completes — matches docs/03-api-design.md §10's "invoked
    in-process for MVP scale" note.

    No reconnect/resume if the caller disconnects mid-stream: generation is
    tied to this async generator's lifetime. Robust background-worker +
    pub/sub delivery is a Phase 7+ hardening concern, not this skeleton.
    """

    def __init__(self, db: AsyncSession, llm_provider: LLMProvider) -> None:
        self._db = db
        self._llm_provider = llm_provider
        self._graph = build_graph()

    async def run(self, request_id: uuid.UUID) -> AsyncIterator[ResourceReadyEvent]:
        request = await get_request(self._db, request_id)
        if request is None:
            raise ValueError(f"teaching_kit_requests {request_id} not found")

        started_at = time.monotonic()
        await update_request_status(self._db, request_id, KitStatus.generating)

        initial_state = {
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
        }
        config = {"configurable": {"db": self._db, "llm_provider": self._llm_provider}}

        async for update in self._graph.astream(initial_state, config=config, stream_mode="updates"):
            for node_output in update.values():
                for result in node_output.get("resources", []):
                    yield ResourceReadyEvent(
                        resource_type=result["resource_type"],
                        resource_id=result["resource_id"],
                        cache_hit=result["cache_hit"],
                    )

        await update_request_status(self._db, request_id, KitStatus.complete)
        self.duration_ms = int((time.monotonic() - started_at) * 1000)

    def kit_complete_event(self, request_id: uuid.UUID) -> KitCompleteEvent:
        return KitCompleteEvent(
            request_id=request_id, status=KitStatus.complete, duration_ms=self.duration_ms
        )
