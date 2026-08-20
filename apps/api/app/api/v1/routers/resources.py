import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.nodes.base import run_resource_node
from app.ai.orchestration.nodes.registry import PRESENTATION_VERSIONS, RESOURCE_SPECS
from app.ai.providers.llm.base import LLMProvider
from app.ai.providers.presentation_export import NativePptxProvider
from app.api.v1.deps import get_current_user, get_db, get_llm_provider, get_session_factory
from app.db.models.enums import ResourceType
from app.db.models.teaching_kit import GeneratedResource
from app.db.models.user import User
from app.db.repositories.curriculum_repository import get_chapter_by_id
from app.db.repositories.teaching_kit_repository import (
    get_generated_resource,
    get_request,
    get_resource_by_type,
)
from app.schemas.teaching_kit import GeneratedResourceRead, RegenerateResourceRequest

router = APIRouter(prefix="/resources", tags=["resources"])


def _to_read_model(resource: GeneratedResource) -> GeneratedResourceRead:
    return GeneratedResourceRead(
        id=resource.id,
        resource_type=resource.resource_type,
        content=resource.content,
        file_url=resource.file_url,
        language=resource.language,
        cache_hit=resource.cache_id is not None,
        created_at=resource.created_at,
    )


async def _get_owned_resource(
    db: AsyncSession, resource_id: uuid.UUID, user_id: uuid.UUID
) -> GeneratedResource:
    resource = await get_generated_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resource_not_found")
    request = await get_request(db, resource.request_id)
    # Ownership lives on the request, not the resource — a resource is only
    # ever reachable through the kit that produced it.
    if request is None or request.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_resource_owner")
    return resource


@router.get("/{resource_id}", response_model=GeneratedResourceRead)
async def read_resource(
    resource_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GeneratedResourceRead:
    return _to_read_model(await _get_owned_resource(db, resource_id, user.id))


@router.post("/{resource_id}/regenerate", response_model=GeneratedResourceRead)
async def regenerate_resource(
    resource_id: uuid.UUID,
    payload: RegenerateResourceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> GeneratedResourceRead:
    """Re-runs one node with new params, leaving the rest of the kit alone.

    Runs inline rather than through the graph: regeneration is a single node
    with no fan-out, so there is nothing for LangGraph to orchestrate.
    """
    resource = await _get_owned_resource(db, resource_id, user.id)
    spec = RESOURCE_SPECS.get(resource.resource_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"no_generator_for_{resource.resource_type.value}",
        )

    request = await get_request(db, resource.request_id)
    assert request is not None  # _get_owned_resource already proved it exists

    lesson_plan_content: dict = {}
    if resource.resource_type is not ResourceType.lesson_plan:
        lesson_plan = await get_resource_by_type(db, request.id, ResourceType.lesson_plan)
        if lesson_plan is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="lesson_plan_missing",
            )
        lesson_plan_content = lesson_plan.content

    generation = await run_resource_node(
        spec=spec,
        session_factory=session_factory,
        llm_provider=llm_provider,
        request_id=request.id,
        class_id=request.class_id,
        subject_id=request.subject_id,
        chapter_id=request.chapter_id,
        language=request.language,
        duration=request.duration,
        teaching_mode=request.teaching_mode,
        lesson_plan_content=lesson_plan_content,
        params=payload.params,
    )

    regenerated = await get_generated_resource(db, generation.resource_id)
    assert regenerated is not None  # just written by run_resource_node
    return _to_read_model(regenerated)


def _safe_filename(stem: str, extension: str) -> str:
    """Chapter names carry Devanagari, spaces and punctuation, and a
    Content-Disposition filename has to survive that. ASCII slug here; the real
    name stays in the UI.
    """
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower()
    return f"{slug or 'resource'}.{extension}"


@router.get("/{resource_id}/export")
async def export_resource(
    resource_id: uuid.UUID,
    export_format: str = Query("pptx", alias="format"),
    version: int = Query(15),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Renders a resource to a downloadable file.

    Deviates from docs/03-api-design.md section 5's enqueue-then-poll job
    contract: a deck renders in well under a second, so a job table plus a
    polling round trip would add latency and moving parts for no benefit at MVP
    scale. That async shape becomes right once video/audio rendering lands.

    PDF is deliberately not offered here. ReportLab and its peers have no Indic
    shaping engine, so a server-rendered Hindi worksheet comes out with its
    matras in the wrong order - visibly broken. The frontend prints to PDF
    through the browser instead, which shapes Devanagari correctly and needs no
    bundled fonts. PPTX has no such problem: it stores text as text and lets
    PowerPoint do the shaping.
    """
    if export_format != "pptx":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported_format",
        )

    resource = await _get_owned_resource(db, resource_id, user.id)
    if resource.resource_type is not ResourceType.presentation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"not_exportable_{resource.resource_type.value}",
        )
    if version not in PRESENTATION_VERSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_version")

    slides = resource.content.get("versions", {}).get(str(version))
    if not slides:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version_not_stored")

    request = await get_request(db, resource.request_id)
    assert request is not None
    chapter = await get_chapter_by_id(db, request.chapter_id)
    title = chapter.name if chapter else "Teaching Kit"

    provider = NativePptxProvider()
    data = provider.render(title=title, slides=slides)
    filename = _safe_filename(f"{title}-{version}-slides", provider.extension)
    return Response(
        content=data,
        media_type=provider.media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
