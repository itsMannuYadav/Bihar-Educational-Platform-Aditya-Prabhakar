import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.orchestration.state import ResourceResult
from app.ai.providers.embedding.base import EmbeddingProvider
from app.ai.providers.llm.base import LLMProvider
from app.cache.keys import compute_cache_key
from app.cache.service import (
    get_cached,
    record_cache_hit,
    semantic_cache_lookup,
    write_cache,
)
from app.db.models.enums import (
    AnalyticsEventType,
    AppLanguage,
    DurationOption,
    ResourceType,
    TeachingMode,
)
from app.db.repositories.analytics_repository import log_event
from app.db.repositories.curriculum_repository import (
    get_chapter_by_id,
    get_class_by_id,
    get_subject_by_id,
)
from app.db.repositories.teaching_kit_repository import (
    create_generated_resource,
    get_generated_resource,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromptContext:
    """Everything any prompt builder might need, so `ResourceSpec.build_prompt`
    has one signature across all resource types — the lesson plan wants
    duration/teaching_mode, the rest want the lesson plan itself. Each registry
    entry adapts this onto its own builder's keyword arguments.
    """

    chapter_name: str
    subject_name: str
    class_grade: int
    language: AppLanguage
    duration: DurationOption
    teaching_mode: TeachingMode
    lesson_plan_content: dict
    extra_instructions: str


PromptBuilder = Callable[[PromptContext], str]
PersistDetails = Callable[[AsyncSession, uuid.UUID, dict], Awaitable[None]]


@dataclass(frozen=True)
class ResourceSpec:
    """Everything that differs between one generation node and the next.

    The cache-check → prompt → structured-generate → persist → cache-write
    sequence is identical for every resource type, so it lives once in
    `run_resource_node` and each type contributes only this spec. Adding a
    resource type (activities, blackboard_notes, flowchart…) means adding a
    prompt module and one entry to the registry — not another near-identical
    node module.
    """

    resource_type: ResourceType
    response_schema: type[BaseModel]
    build_prompt: PromptBuilder
    #: Maps the parsed LLM model onto the `generated_resources.content` jsonb.
    to_content: Callable[[BaseModel], dict]
    #: Writes the type-specific normalized rows (questions, worksheets, …).
    #: Runs on cache hits too: detail rows are keyed by `resource_id`, and a
    #: cache hit still mints a fresh generated_resources row.
    persist_details: PersistDetails | None = None
    #: Renders regenerate-time params into an extra prompt paragraph.
    describe_params: Callable[[dict], str] = lambda params: ""


@dataclass(frozen=True)
class ResourceGeneration:
    resource_id: uuid.UUID
    content: dict
    cache_hit: bool

    def as_result(self, resource_type: ResourceType) -> ResourceResult:
        return ResourceResult(
            resource_type=resource_type.value,
            resource_id=self.resource_id,
            cache_hit=self.cache_hit,
        )


async def _use_cached_entry(
    db: AsyncSession,
    *,
    cached,
    spec: ResourceSpec,
    request_id: uuid.UUID,
    language: AppLanguage,
    params: dict,
    hit_source: str,  # "exact" or "semantic"
) -> ResourceGeneration:
    """Materialise a cache hit: create a lightweight generated_resources row,
    write the detail rows, bump hit_count, and log the analytics event.
    """
    canonical = await get_generated_resource(db, cached.canonical_resource_id)
    if canonical is None:
        raise RuntimeError(
            f"resource_cache {cached.id} points at a missing generated_resource"
        )
    content = dict(canonical.content)
    resource = await create_generated_resource(
        db,
        request_id=request_id,
        resource_type=spec.resource_type,
        content=content,
        language=language,
        cache_id=cached.id,
        file_url=canonical.file_url,
        params=params,
    )
    if spec.persist_details is not None:
        await spec.persist_details(db, resource.id, content)
    await record_cache_hit(db, cached)
    await log_event(
        db,
        event_type=AnalyticsEventType.cache_hit,
        metadata={
            "resource_type": spec.resource_type.value,
            "hit_source": hit_source,
            "cache_id": str(cached.id),
        },
    )
    await db.commit()
    return ResourceGeneration(resource_id=resource.id, content=content, cache_hit=True)


async def run_resource_node(
    *,
    spec: ResourceSpec,
    session_factory: async_sessionmaker[AsyncSession],
    llm_provider: LLMProvider,
    request_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    chapter_id: uuid.UUID,
    language: AppLanguage,
    duration: DurationOption,
    teaching_mode: TeachingMode,
    lesson_plan_content: dict,
    params: dict | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    raw_query: str | None = None,
) -> ResourceGeneration:
    """Cache-checked generation of one resource. Callable both from a graph
    node and directly from `POST /resources/{id}/regenerate`, which is why it
    takes plain arguments rather than a `TeachingKitState`.

    Cache lookup order (docs/02-database-schema.md §4):
      1. Exact key match — zero AI cost, zero embedding cost.
      2. Semantic near-match (only when raw_query + embedding_provider present)
         — embed the query, cosine-search within same curriculum scope,
         threshold ≥ 0.92 → treat as hit.
      3. Miss — generate fresh; store embedding in cache if raw_query present.
    """
    params = params or {}
    cache_key = compute_cache_key(
        class_id=class_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        language=language,
        duration=duration,
        teaching_mode=teaching_mode,
        resource_type=spec.resource_type,
        params=params,
    )

    # Each Send-dispatched branch runs concurrently (docs/01-architecture.md §3),
    # so this owns its sessions rather than sharing one — see the
    # InProcessOrchestrator docstring for what sharing one broke.
    async with session_factory() as db:
        # ── Step 1: exact cache hit ──────────────────────────────────────────
        cached = await get_cached(db, cache_key)
        if cached is not None:
            return await _use_cached_entry(
                db,
                cached=cached,
                spec=spec,
                request_id=request_id,
                language=language,
                params=params,
                hit_source="exact",
            )

        # ── Step 2: semantic near-match ───────────────────────────────────────
        query_embedding: list[float] | None = None
        if raw_query and embedding_provider is not None:
            try:
                query_embedding = await embedding_provider.embed(raw_query)
                semantic = await semantic_cache_lookup(
                    db,
                    class_id=class_id,
                    subject_id=subject_id,
                    resource_type=spec.resource_type,
                    embedding=query_embedding,
                )
                if semantic is not None:
                    logger.info(
                        "semantic cache hit for %s (raw_query=%r)",
                        spec.resource_type.value,
                        raw_query,
                    )
                    return await _use_cached_entry(
                        db,
                        cached=semantic,
                        spec=spec,
                        request_id=request_id,
                        language=language,
                        params=params,
                        hit_source="semantic",
                    )
            except Exception:
                logger.warning(
                    "embedding/semantic lookup failed for %s (non-fatal)",
                    spec.resource_type.value,
                    exc_info=True,
                )
                query_embedding = None

        # ── Step 3: full miss — fetch prompt context ──────────────────────────
        chapter = await get_chapter_by_id(db, chapter_id)
        subject = await get_subject_by_id(db, subject_id)
        school_class = await get_class_by_id(db, class_id)
        if chapter is None or subject is None or school_class is None:
            raise ValueError(
                "teaching-kit request references a curriculum entity that no longer exists"
            )
        prompt = spec.build_prompt(
            PromptContext(
                chapter_name=chapter.name,
                subject_name=subject.name,
                class_grade=school_class.grade,
                language=language,
                duration=duration,
                teaching_mode=teaching_mode,
                lesson_plan_content=lesson_plan_content,
                extra_instructions=spec.describe_params(params),
            )
        )

    # Deliberately outside any `async with session_factory()`: a generation call
    # takes ~10s, and a kit fans out many at once. Holding a pooled DB
    # connection for that whole window would exhaust the pool for no reason.
    parsed = await llm_provider.generate(
        prompt, language=language, response_schema=spec.response_schema
    )
    content = spec.to_content(parsed)

    async with session_factory() as db:
        resource = await create_generated_resource(
            db,
            request_id=request_id,
            resource_type=spec.resource_type,
            content=content,
            language=language,
            params=params,
        )
        if spec.persist_details is not None:
            await spec.persist_details(db, resource.id, content)
        await log_event(
            db,
            event_type=AnalyticsEventType.cache_miss,
            metadata={"resource_type": spec.resource_type.value},
        )
        await db.commit()
        resource_id = resource.id

    # Cache write lives in its own transaction, after the resource is durable.
    # Two concurrent kits for the same chapter race to claim the same
    # cache_key; the loser keeps its own generated_resources row and simply
    # doesn't become the canonical entry. Isolating it this way means the
    # unique violation can't roll back the resource we just generated — and
    # avoids SAVEPOINT, which pysqlite's implicit-BEGIN handling breaks.
    async with session_factory() as db:
        try:
            await write_cache(
                db,
                cache_key=cache_key,
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=chapter_id,
                language=language,
                resource_type=spec.resource_type,
                params=params,
                canonical_resource_id=resource_id,
                query_embedding=query_embedding,
            )
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.info(
                "cache_key for %s was claimed concurrently; keeping this copy uncached",
                spec.resource_type.value,
            )

    return ResourceGeneration(resource_id=resource_id, content=content, cache_hit=False)
