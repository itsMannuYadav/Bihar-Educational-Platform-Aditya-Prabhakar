import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import AppLanguage, KitStatus, ResourceType
from app.db.models.teaching_kit import GeneratedResource, TeachingKitRequest
from app.schemas.teaching_kit import GenerateTeachingKitRequest


async def create_request(
    db: AsyncSession, *, user_id: uuid.UUID, payload: GenerateTeachingKitRequest
) -> TeachingKitRequest:
    request = TeachingKitRequest(
        user_id=user_id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        language=payload.language,
        duration=payload.duration,
        teaching_mode=payload.teaching_mode,
        raw_query=payload.raw_query,
        status=KitStatus.pending,
        resource_types=[rt.value for rt in payload.resource_types],
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def get_request(db: AsyncSession, request_id: uuid.UUID) -> TeachingKitRequest | None:
    result = await db.execute(select(TeachingKitRequest).where(TeachingKitRequest.id == request_id))
    return result.scalar_one_or_none()


async def update_request_status(db: AsyncSession, request_id: uuid.UUID, status: KitStatus) -> None:
    request = await get_request(db, request_id)
    if request is not None:
        request.status = status
        await db.commit()


async def list_resources_for_request(
    db: AsyncSession, request_id: uuid.UUID
) -> list[GeneratedResource]:
    result = await db.execute(
        select(GeneratedResource)
        .where(GeneratedResource.request_id == request_id)
        .order_by(GeneratedResource.created_at)
    )
    return list(result.scalars().all())


async def get_generated_resource(
    db: AsyncSession, resource_id: uuid.UUID
) -> GeneratedResource | None:
    result = await db.execute(select(GeneratedResource).where(GeneratedResource.id == resource_id))
    return result.scalar_one_or_none()


async def create_generated_resource(
    db: AsyncSession,
    *,
    request_id: uuid.UUID,
    resource_type: ResourceType,
    content: dict,
    language: AppLanguage,
    cache_id: uuid.UUID | None = None,
    file_url: str | None = None,
    params: dict | None = None,
) -> GeneratedResource:
    resource = GeneratedResource(
        request_id=request_id,
        resource_type=resource_type,
        content=content,
        language=language,
        cache_id=cache_id,
        file_url=file_url,
        params=params or {},
    )
    db.add(resource)
    await db.flush()
    return resource


async def get_resource_by_type(
    db: AsyncSession, request_id: uuid.UUID, resource_type: ResourceType
) -> GeneratedResource | None:
    """Most recent resource of one type in a kit — how a regenerate finds the
    lesson plan it has to stay consistent with, and how the UI resolves the
    newest copy after a re-roll replaced an earlier one.
    """
    result = await db.execute(
        select(GeneratedResource)
        .where(
            GeneratedResource.request_id == request_id,
            GeneratedResource.resource_type == resource_type,
        )
        .order_by(GeneratedResource.created_at.desc())
    )
    return result.scalars().first()
