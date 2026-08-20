# Shiksha Sathi

AI teaching companion for Bihar classrooms. Architecture in
[`docs/01-architecture.md`](docs/01-architecture.md), schema in
[`docs/02-database-schema.md`](docs/02-database-schema.md), endpoints in
[`docs/03-api-design.md`](docs/03-api-design.md).

The app is two services you run separately: a FastAPI backend (`apps/api`)
and a Next.js frontend (`apps/web`).

## Quick start (demo / already-configured machine)

If `.env` files already exist under `apps/api` and `apps/web` (i.e. this
isn't a fresh clone), just boot both servers.

**Terminal 1 — backend**

```bash
cd apps/api
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Serves the API at `http://localhost:8000`.

**Terminal 2 — frontend**

```bash
cd apps/web
npm run dev
```

Serves the app at `http://localhost:3000` — this is the URL to demo.

## First-time setup

**Backend** — see [`apps/api/README.md`](apps/api/README.md) for full
details (Postgres/pgvector requirement, LLM provider config, etc.):

```bash
cd apps/api
uv sync --dev
cp .env.example .env   # then fill in the blanks
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Seed curriculum data so there's something to generate against:

```bash
uv run python -m app.db.seed_curriculum
```

**Frontend**:

```bash
cd apps/web
npm install
cp .env.example .env   # fill in NEXT_PUBLIC_API_URL / Supabase keys
npm run dev
```

## Notes for demos

- `alembic upgrade head` is safe to re-run even with no pending migrations —
  run it before every demo as a habit.
- Gemini free tier is ~5 requests/minute and a full 7-resource teaching kit
  takes ~100s to generate (`LLM_MAX_CONCURRENCY` bounds the fan-out) — either
  budget for that pause live, or generate a kit ahead of time as a backup.
