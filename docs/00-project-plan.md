# AI Teaching Companion for Government Schools — Master Plan

**Prototype scope:** Bihar. **Architecture scope:** state-agnostic from day one.

## 1. Product thesis

Government-school teachers are the bottleneck resource in Indian public education, not students. Most "edtech" targets students directly and assumes a device-per-child, high-engagement context that doesn't exist in most government schools. This product instead treats the **teacher** as the primary user and optimizes a single metric:

> Time from "I need to teach photosynthesis to Class 7 tomorrow" to "I have a usable, printable, board-ready teaching kit in my hand" — target **under 10 minutes**, one search box, zero configuration beyond class/subject/chapter/duration.

Everything else (analytics, admin, personas, offline support) is in service of that loop staying fast, trustworthy, and cheap to run at scale (hence aggressive caching — Bihar has ~70,000+ government schools; the topic space per class/subject/chapter is finite and highly repeated).

## 2. Non-goals (explicitly out of scope for v1)

- Student-facing learning app / student accounts.
- AI video generation (UI stub only, "Coming Soon").
- Imitating named individual educators (only extracted, generic teaching *characteristics*).
- Tight coupling to one LLM vendor or one presentation vendor (OpenAI/Gemini and Canva must both sit behind abstraction layers).
- Multi-state curriculum mapping (architecture supports it; content/data for v1 is Bihar-only, NCERT/BSEB aligned).

## 3. Document index

| Doc | Contents |
|---|---|
| [01-architecture.md](01-architecture.md) | System architecture, service boundaries, provider abstractions, caching strategy, offline/PWA approach |
| [02-database-schema.md](02-database-schema.md) | Full Postgres schema + DDL sketch, caching table design, pgvector usage |
| [03-api-design.md](03-api-design.md) | FastAPI REST/SSE surface, request/response shapes, generation pipeline contract |
| [04-folder-structure.md](04-folder-structure.md) | Monorepo layout for `apps/web` (Next.js) and `apps/api` (FastAPI) |
| [05-user-flows.md](05-user-flows.md) | End-to-end flows: onboarding, kit generation (cache hit/miss), voice input, admin |
| [06-component-hierarchy.md](06-component-hierarchy.md) | React component tree for dashboard + teaching-kit result screens |
| [07-roadmap.md](07-roadmap.md) | Phase 1–9 delivery plan mapped to MVP scope |

A visual wireframe of the core screens (hero search, generation flow, teaching-kit results, worksheet/PPT viewers) is delivered separately as an interactive mockup — see the artifact linked in chat.

## 4. MVP cut (Phase 1 ships exactly this, nothing more)

- Topic search (text, bilingual placeholder, Hindi/English/Hinglish)
- Class → Subject → Chapter → Language → Duration selector
- "Generate Teaching Kit" → produces: Lesson Plan, Teaching Script, Quiz (MCQ/short/long), Worksheet (PDF export), PPT (5/10/15-slide, PPTX+PDF export), Mind Map (interactive, print/export), Audio (1/3/5-min, play/pause/download)
- Voice input (STT) into the search box, Hindi/English/Hinglish
- Result caching keyed on (class, subject, chapter, language, duration, mode) — cache hit skips all AI calls
- Auth via Supabase (mobile OTP, email OTP, Google)

Everything else in the spec (Blackboard Mode as a distinct rendering, Local Context Generator, Activity Generator, PYQ bank, Canva export, animations, flowcharts/diagrams beyond mind maps, teaching personas, analytics dashboard, offline PWA caching, school/super-admin consoles) is **designed in the schema/API now** so nothing has to be re-architected later, but is feature-flagged off until Phase 4+. See [07-roadmap.md](07-roadmap.md).

## 5. Key architectural bets

1. **One generation request → one LangGraph run → N resources**, not N independent LLM calls the user triggers one-by-one. The teacher clicks one button; the graph fans out to produce every kit resource, streaming each one back as it finishes (SSE), so the UI never shows a single 60-second blank spinner.
2. **Cache-first, not cache-aside as an afterthought.** The cache key is checked *before* the graph runs, per-resource-type — so if 8 of 9 resource types are cached but "worksheet" isn't (e.g. someone requested a new difficulty mix), only that one resource triggers an LLM call. See [02-database-schema.md](02-database-schema.md#resource_cache).
3. **Provider abstraction on every external creative-AI dependency**: `LLMProvider`, `TTSProvider`, `PresentationExportProvider` (Canva is a future implementation of this interface, not a special case), `STTProvider`. Swapping OpenAI ↔ Gemini, or adding Canva export, touches one adapter file, not the graph or the API layer.
4. **Bilingual is a first-class content dimension, not a UI-only i18n concern.** Language is part of the cache key and part of every generation prompt; UI chrome translation (buttons, nav) uses standard next-intl, but *generated content* language is a generation parameter.
