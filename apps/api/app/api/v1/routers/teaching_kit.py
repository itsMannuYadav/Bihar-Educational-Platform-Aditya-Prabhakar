import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.orchestrator import InProcessOrchestrator
from app.ai.providers.llm.base import LLMProvider
from app.api.v1.deps import get_current_user, get_db, get_llm_provider, get_session_factory
from app.db.models.enums import KitStatus
from app.db.models.teaching_kit import TeachingKitRequest
from app.db.models.user import User
from app.db.repositories.teaching_kit_repository import (
    create_request,
    get_request,
    list_resources_for_request,
    update_request_status,
)
from app.schemas.teaching_kit import (
    GeneratedResourceRead,
    GenerateTeachingKitRequest,
    KitCompleteEvent,
    TeachingKitRequestSummary,
    TeachingKitStateRead,
)

router = APIRouter(prefix="/teaching-kit", tags=["teaching-kit"])


async def _get_owned_request(
    db: AsyncSession, request_id: uuid.UUID, user_id: uuid.UUID
) -> TeachingKitRequest:
    request = await get_request(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="teaching_kit_request_not_found"
        )
    if request.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_request_owner")
    return request


def _sse_frame(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream_events(
    request_id: uuid.UUID,
    llm_provider: LLMProvider,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[str]:
    # A StreamingResponse's generator runs after the request-scoped `Depends(get_db)`
    # session has already been closed, so this opens its own session rather than
    # reusing the one from the route function (which only did the ownership check).
    started_at = time.monotonic()
    async with session_factory() as db:
        try:
            orchestrator = InProcessOrchestrator(db, llm_provider)
            async for event in orchestrator.run(request_id):
                yield _sse_frame("resource_ready", event.model_dump(by_alias=True, mode="json"))
        except Exception as exc:
            await update_request_status(db, request_id, KitStatus.failed)
            yield _sse_frame("error", {"detail": str(exc)})
            return

        duration_ms = int((time.monotonic() - started_at) * 1000)
        complete = KitCompleteEvent(
            request_id=request_id, status=KitStatus.complete, duration_ms=duration_ms
        )
        yield _sse_frame("kit_complete", complete.model_dump(by_alias=True, mode="json"))


@router.post(
    "/generate", response_model=TeachingKitRequestSummary, status_code=status.HTTP_202_ACCEPTED
)
async def generate_teaching_kit(
    payload: GenerateTeachingKitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingKitRequestSummary:
    request = await create_request(db, user_id=user.id, payload=payload)
    return TeachingKitRequestSummary(
        request_id=request.id,
        status=request.status,
        stream_url=f"/api/v1/teaching-kit/{request.id}/stream",
    )


@router.get("/{request_id}", response_model=TeachingKitStateRead)
async def get_teaching_kit(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeachingKitStateRead:
    request = await _get_owned_request(db, request_id, user.id)
    resources = await list_resources_for_request(db, request_id)
    return TeachingKitStateRead(
        request_id=request.id,
        status=request.status,
        resources=[
            GeneratedResourceRead(
                id=r.id,
                resource_type=r.resource_type,
                content=r.content,
                file_url=r.file_url,
                language=r.language,
                cache_hit=r.cache_id is not None,
                created_at=r.created_at,
            )
            for r in resources
        ],
    )


@router.get("/{request_id}/stream")
async def stream_teaching_kit(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    await _get_owned_request(db, request_id, user.id)
    return StreamingResponse(
        _stream_events(request_id, llm_provider, session_factory), media_type="text/event-stream"
    )
