# Shiksha Sathi API

FastAPI backend for the AI teaching companion. Architecture in
[`docs/01-architecture.md`](../../docs/01-architecture.md), schema in
[`docs/02-database-schema.md`](../../docs/02-database-schema.md), endpoints in
[`docs/03-api-design.md`](../../docs/03-api-design.md).

## Running it

```bash
uv sync --dev
cp .env.example .env   # then fill in the blanks
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Needs a Postgres with the `pgvector` extension available (`resource_cache`
carries a `vector(1536)` column). Supabase provides one out of the box; for a
local one, `pgvector/pgvector:pg17` is the least-effort image.

Seed enough curriculum to generate against:

```bash
uv run python -m app.db.seed_curriculum
```

## Checks

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q
```

## LLM provider

`LLM_PROVIDER` selects between `openai` and `gemini`; the matching key must be
set or `/teaching-kit/*` returns 503 with `llm_not_configured` rather than
failing deep inside a generation. Both providers implement the same
`LLMProvider` Protocol (`app/ai/providers/llm/base.py`) and return a parsed
Pydantic model, so nodes never branch on which one is active.

Two things worth knowing before changing the Gemini config:

- **Model ids expire.** `gemini-2.5-flash` already 404s for new keys with
  "no longer available to new users". If a call fails that way, list what the
  key can actually reach with `client.models.list()` rather than guessing a
  name.
- **The free tier allows 5 requests/minute.** A teaching kit fans out 6
  generations at once, so an unthrottled kit exhausts the quota before its
  first resource lands. `LLM_MAX_CONCURRENCY` (default 2) bounds the fan-out,
  and the provider honours the server's own suggested retry delay on 429/503.
  A full 7-resource kit takes roughly 100s on the free tier; raise the
  concurrency on a paid tier, where the parallel fan-out is the whole point.

## Generation nodes

Adding a resource type does not mean writing another node. The cache-check →
prompt → structured-generate → persist → cache-write sequence lives once in
`app/ai/orchestration/nodes/base.py`; a type contributes a prompt module plus
one `ResourceSpec` entry in `nodes/registry.py`. Types with no spec fall
through to a placeholder row so the kit's SSE stream and result tabs stay
complete (audio → Phase 5).

`app/ai/prompts/mind_map.py` is the one place where the generated shape and the
stored shape differ on purpose: Gemini handles self-referencing `$ref` schemas
badly in structured-output mode, so the model is asked for a flat three-level
outline that is then folded into the recursive `mind_maps.structure` jsonb.

## Deviations from the design docs

Both are deliberate and commented at the point of departure:

- **Export is synchronous.** [`docs/03-api-design.md` §5](../../docs/03-api-design.md)
  specifies `POST /resources/{id}/export` enqueuing a job to poll. A deck
  renders in well under a second, so `GET /resources/{id}/export?format=pptx`
  streams the file directly; the job contract becomes the right shape once
  video/audio rendering lands.
- **PDF is rendered by the browser, not the server.** ReportLab and its peers
  have no Indic shaping engine, so a server-rendered Hindi worksheet comes out
  with its matras in the wrong order. The frontend prints through the browser
  instead (print stylesheet in `apps/web/app/globals.css`), which shapes
  Devanagari correctly and needs no bundled fonts. PPTX has no such problem —
  it stores text as text and lets PowerPoint do the shaping — so that one is
  rendered server-side by `NativePptxProvider`.

## Tests

`pytest` runs against a per-test SQLite **file**, not `:memory:`. An in-memory
SQLite database only lives as long as its single connection, which forces every
session in a test to share one connection — and the generation graph fans out
concurrently with each branch owning its own session, so a shared connection
made concurrent branches commit on top of each other's open cursors. See the
`db_engine` fixture in `app/tests/conftest.py`.
