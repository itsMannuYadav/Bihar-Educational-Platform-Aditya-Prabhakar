# Folder Structure

Monorepo (npm/pnpm workspaces for the JS side, standalone Python package for the API — no forced single-tool monorepo framework, keeps FastAPI deployable as a plain Docker image independent of the JS toolchain).

```
bihar-teaching-companion/
├── apps/
│   ├── web/                             # Next.js (Vercel)
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── onboarding/page.tsx  # first-login: name, school, preferred language
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx           # top nav: Search, Library, My Resources, Saved, Worksheets, Analytics, Settings
│   │   │   │   ├── dashboard/page.tsx   # hero search + recent kits
│   │   │   │   ├── library/page.tsx
│   │   │   │   ├── my-resources/page.tsx
│   │   │   │   ├── saved-lessons/page.tsx
│   │   │   │   ├── worksheets/page.tsx
│   │   │   │   ├── analytics/page.tsx   # school_admin/super_admin only, route-guarded
│   │   │   │   └── settings/page.tsx
│   │   │   ├── teaching-kit/
│   │   │   │   └── [requestId]/
│   │   │   │       ├── page.tsx         # result shell: tabs across resource types
│   │   │   │       ├── lesson-plan/page.tsx
│   │   │   │       ├── script/page.tsx
│   │   │   │       ├── worksheet/page.tsx
│   │   │   │       ├── presentation/page.tsx
│   │   │   │       ├── mind-map/page.tsx
│   │   │   │       └── audio/page.tsx
│   │   │   ├── admin/
│   │   │   │   ├── schools/page.tsx     # super_admin
│   │   │   │   └── teachers/page.tsx    # school_admin + super_admin
│   │   │   └── layout.tsx               # root: providers, PWA manifest link, font
│   │   ├── components/
│   │   │   ├── ui/                      # shadcn primitives (button, card, tabs, dialog, ...)
│   │   │   ├── dashboard/               # HeroSearch, VoiceInputButton, ClassSubjectChapterPicker, RecentKitsGrid
│   │   │   ├── teaching-kit/            # ResourceTabs, LessonPlanView, ScriptView, WorksheetViewer, PptViewer, MindMapCanvas, AudioPlayer, GenerationProgress
│   │   │   ├── admin/                   # TeacherTable, SchoolForm, AnalyticsCharts
│   │   │   └── common/                  # LanguageSwitcher, AppShell, EmptyState, LoadingSkeletons
│   │   ├── lib/
│   │   │   ├── api-client.ts            # typed fetch wrapper, SSE helper
│   │   │   ├── supabase.ts
│   │   │   └── cache-keys.ts            # mirrors backend cache_key derivation for React Query keys
│   │   ├── hooks/
│   │   │   ├── useTeachingKitStream.ts  # SSE subscription hook
│   │   │   ├── useVoiceInput.ts
│   │   │   └── useOfflineResource.ts
│   │   ├── stores/                      # zustand: uiStore (language, active mode), voiceStore, draftFormStore
│   │   ├── messages/                    # en.json, hi.json, hinglish.json (UI chrome i18n)
│   │   ├── public/
│   │   │   ├── manifest.json
│   │   │   └── icons/
│   │   ├── service-worker.ts            # or next-pwa config
│   │   ├── proxy.ts                     # auth guard, role-based route protection (Next.js 16 renamed `middleware.ts` → `proxy.ts`, `export function proxy()`)
│   │   └── package.json
│   │
│   └── api/                             # FastAPI (Railway/Azure)
│       ├── app/
│       │   ├── main.py                  # app factory, router registration, CORS, middleware
│       │   ├── api/v1/
│       │   │   ├── routers/
│       │   │   │   ├── catalog.py
│       │   │   │   ├── teaching_kit.py
│       │   │   │   ├── resources.py     # lesson_plan/script/worksheet/presentation/audio/mind_map sub-routes
│       │   │   │   ├── voice.py
│       │   │   │   ├── library.py
│       │   │   │   ├── analytics.py
│       │   │   │   └── admin.py
│       │   │   └── deps.py              # get_current_user, require_role, get_db
│       │   ├── core/
│       │   │   ├── config.py            # pydantic-settings, env vars
│       │   │   ├── security.py          # Supabase JWT verification
│       │   │   └── logging.py
│       │   ├── ai/
│       │   │   ├── providers/
│       │   │   │   ├── llm/{base.py, openai_provider.py, gemini_provider.py}
│       │   │   │   ├── tts/{base.py, <provider>.py}
│       │   │   │   ├── stt/{base.py, <provider>.py}
│       │   │   │   └── presentation_export/{base.py, native_pptx.py, canva.py}  # canva.py stub only initially
│       │   │   ├── orchestration/
│       │   │   │   ├── graph.py         # LangGraph definition
│       │   │   │   └── nodes/           # one module per resource-generation node
│       │   │   └── prompts/             # per-resource, per-language prompt templates
│       │   ├── cache/
│       │   │   ├── service.py           # check_cache / write_cache, embedding similarity search
│       │   │   └── keys.py              # cache_key derivation (shared logic, single source of truth)
│       │   ├── db/
│       │   │   ├── models/              # SQLAlchemy models mirroring 02-database-schema.md
│       │   │   ├── repositories/
│       │   │   └── migrations/          # Alembic
│       │   ├── schemas/                 # Pydantic request/response models
│       │   ├── workers/                 # background jobs: render_pptx, render_pdf, finalize_audio
│       │   └── tests/
│       ├── alembic.ini
│       ├── pyproject.toml
│       └── Dockerfile
│
├── packages/
│   └── shared-types/                    # hand-kept TS types mirroring Pydantic schemas for the generation-params contract
│
├── infra/
│   ├── docker/
│   ├── railway.json
│   └── azure/
│
└── docs/                                # this folder
```

**Why not a fully unified TS monorepo tool (Turborepo/Nx) at MVP stage:** the two apps deploy to entirely different platforms (Vercel vs Railway/Azure) with different toolchains (Node vs Python); a shared workspace tool buys little beyond the `shared-types` package, which is small enough to hand-sync at this stage. Revisit if a third JS app (e.g. a native wrapper) gets added.
