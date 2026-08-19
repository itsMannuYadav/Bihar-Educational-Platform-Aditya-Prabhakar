# Development Roadmap

Each phase produces something runnable/demoable — no phase is "infrastructure only" with nothing to show.

## Phase 1 — Project setup

- Monorepo scaffold per [04-folder-structure.md](04-folder-structure.md): `apps/web` (Next.js + TS + Tailwind + shadcn init), `apps/api` (FastAPI + Poetry/uv, Dockerfile).
- Lint/format: ESLint+Prettier (web), ruff+black (api). CI skeleton (lint + typecheck on push).
- `packages/shared-types` seeded with the generation-params type (class/subject/chapter/language/duration/mode).
- **Demo**: empty app shell deployed to a Vercel preview + FastAPI `/health` on Railway.

## Phase 2 — Authentication

- Supabase project provisioned; Mobile OTP, Email OTP, Google sign-in wired on the frontend.
- `apps/api/app/core/security.py`: JWT verification dependency.
- `users` table + `/me` GET/POST (profile creation on first login).
- Onboarding flow (school search/select, preferred language) per [05-user-flows.md §1](05-user-flows.md#1-onboarding--login).
- Role-based route guards (`proxy.ts` — Next.js 16's renamed `middleware.ts` — plus the backend's `require_role` dependency) even though only `teacher` role has real UI yet.
- **Demo**: full login → onboarding → empty dashboard, three auth methods working.

## Phase 3 — Database

- Full schema from [02-database-schema.md](02-database-schema.md) via Alembic migrations: identity/org, curriculum catalog, requests/resources, `resource_cache` (pgvector extension enabled), resource-detail tables, personas, saved_lessons, analytics_events.
- Seed script: Bihar Class 6–10, core subjects (Science, Social Science, Math, Hindi, English), chapter list for at least one subject end-to-end (enough to demo Phase 4) — full curriculum seeding is ongoing content work, not a blocking Phase 3 task.
- Repository layer (`db/repositories/`) — no raw queries in routers.
- **Demo**: `GET /catalog/classes` → `/subjects` → `/chapters` returns real seeded Bihar curriculum data.

## Phase 4 — Teaching-kit generation (the core of the product)

Sub-phased because this is the largest phase:

**4a — Orchestration skeleton**
- LangGraph graph wired with `check_cache` fan-out + one real node (`generate_lesson_plan`) and stubs for the rest returning placeholder content.
- `LLMProvider` abstraction + `OpenAIProvider` implementation (Gemini adapter can follow same interface later, not blocking).
- `/teaching-kit/generate` + SSE `/stream` endpoint, `GenerationProgress` UI component consuming it.

**4b — MVP resource nodes**
- `generate_teaching_script`, `generate_questions`, `generate_worksheet` (+ PDF export worker), `generate_mind_map` (+ interactive render), `generate_ppt_outline` + `render_ppt` (native PPTX, 5/10/15 versions, PDF export).
- Cache write-through on every node; cache-key derivation shared between frontend `lib/cache-keys.ts` and backend `cache/keys.py`.
- Result view: `ResourceTabs` + all MVP `*View`/`*Viewer` components per [06-component-hierarchy.md §2](06-component-hierarchy.md#2-generation--teaching-kit-result-appteaching-kitrequestidpagetsx).
- **Demo**: full core loop — search → confirm → generate → all MVP resources appear, cache hit is visibly instant on a repeat request.

**4c — Voice input**
- `STTProvider` abstraction + implementation, `/voice/transcribe`, `VoiceInputButton`.
- **Demo**: spoken Hinglish query → transcribed → generates correct kit.

**4d — Library**
- Save/list/search saved lessons.
- **Demo**: save a kit, find it again from Saved Lessons.

## Phase 5 — Audio generation

- `TTSProvider` abstraction + implementation.
- 1/3/5-minute script variants generated per lesson plan core concepts, rendered to audio, stored in Supabase Storage.
- `AudioPlayer` component (play/pause/download), offline-cacheable.
- **Demo**: generate a kit, play all three audio lengths, download one.

*(Explicitly not built here: animation generator, video generation. Animation generator is designed in the resource_type enum and API contract but implemented only if time allows post-MVP; video stays a `501`-stubbed "Coming Soon" per [01-architecture.md §4](01-architecture.md#4-ai-provider-abstraction-layer).)*

## Phase 6 — PPT generation (hardening pass)

- Design-quality pass on the native PPTX templates (large fonts, teacher-friendly layouts per the design system).
- `PresentationExportProvider` abstraction confirmed clean enough that a `CanvaExportProvider` stub can be added without touching the graph (build the stub, not full Canva integration — that's a post-MVP milestone gated on Canva partnership/API access).
- **Demo**: 5/10/15-slide decks for the same chapter, PPTX + PDF download both work.

## Phase 7 — Caching (hardening + observability pass)

- pgvector semantic near-match fallback (flow described in [02-database-schema.md §4](02-database-schema.md#4-cache-layer--the-mandatory-piece)) implemented and tuned (similarity threshold).
- Cache-hit/miss logging to `analytics_events`; basic internal ops view of hit rate by resource type.
- Load-test the cache-key derivation for collisions/consistency between frontend and backend.
- **Demo**: two differently-phrased queries for the same chapter resolve to the same cached kit; hit-rate dashboard shows real numbers.

## Phase 8 — Testing

- Backend: pytest — provider adapters mocked, cache-key determinism tests, graph node contract tests, RBAC tests per role.
- Frontend: component tests (Vitest/RTL) for `HeroSearch`, `ResourceTabs`, `GenerationProgress` (SSE handling incl. partial/failed states); Playwright e2e for the full core loop (login → generate → view → save → export) on a mobile viewport.
- Accessibility pass: keyboard navigation through the full core loop, screen-reader labels on all icon-only buttons (mic, export, save), contrast check against the orange/white/soft-gray palette.
- **Demo**: CI green, e2e recording of the core loop on a simulated low-end Android viewport.

## Phase 9 — Deployment

- Production Vercel project (web) + Railway/Azure production service (api) + Supabase production project.
- Env/secrets management, DB migration runbook, background worker process sizing.
- Basic uptime/error monitoring (Sentry or equivalent) on both frontend and backend.
- Soft-launch with a small set of pilot schools; analytics dashboard becomes the feedback loop for what to build next (Blackboard Mode polish, Local Context Generator, Activity Generator, PYQ bank, school/super-admin consoles, offline PWA hardening, animations, Canva integration — all already schema/API-ready per earlier docs).

## Post-MVP backlog (designed now, built later)

| Feature | Status after Phase 9 |
|---|---|
| Blackboard Mode (distinct board-optimized rendering, not just a script view) | Schema/content model ready; needs dedicated UI |
| Local Context Generator (Bihar-specific examples) | Prompt-template hook exists in every generation node; needs curated local-context data source |
| Activity Generator | `resource_type` enum entry exists; node not registered |
| Previous-Year Questions | `questions.is_previous_year` flag exists; needs PYQ source dataset |
| Flowcharts / standalone diagrams (beyond mind maps) | `resource_type` entries exist; needs SVG generation node |
| Animation generator | Explicitly deferred, see Phase 5 note |
| Video generation | Stub only, `VideoGenerationProvider` unimplemented by design |
| Canva export | `PresentationExportProvider` interface ready; needs partnership/API access |
| Teaching personas UI (mode picker beyond the 5 MVP modes) | `teaching_personas` table + prompt-fragment mechanism ready; needs UI + content |
| Offline PWA (full) | Phase 4–8 builds resource-level offline caching; full app-shell offline hardening is a dedicated pass |
| School/Super-admin consoles | API routes ([03-api-design.md §9](03-api-design.md#9-admin)) exist; UI is a dedicated phase |
