# User Flows

## 1. Onboarding & login

```mermaid
sequenceDiagram
    actor T as Teacher
    participant W as Web App
    participant SB as Supabase Auth
    participant API as FastAPI

    T->>W: Open app
    W->>T: Login screen (Mobile OTP / Email OTP / Google)
    T->>SB: Submit phone or email or Google
    SB-->>T: OTP challenge (if OTP path)
    T->>SB: Enter OTP
    SB-->>W: JWT session
    W->>API: GET /me (Bearer JWT)
    alt first login
        API-->>W: 404 user not found
        W->>T: Onboarding form (name, school search/select, preferred language)
        T->>W: Submit
        W->>API: POST /me (create profile)
    else returning user
        API-->>W: user profile
    end
    W->>T: Dashboard (hero search)
```

Design note: school selection is a searchable, pre-seeded list (from `schools`, UDISE-coded) — never a free-text field, so downstream admin/analytics scoping stays clean. If a teacher's school isn't found, they can flag it for `super_admin` review rather than self-creating a school record.

## 2. Core loop — generate a teaching kit (the product's central flow)

```mermaid
flowchart TD
    A["Teacher opens Dashboard"] --> B{"Type or speak a query?"}
    B -- types --> C["Hero search box\n'How should I teach photosynthesis?'"]
    B -- speaks --> D["Mic button → STT →\ntext fills search box"]
    D --> C
    C --> E["System resolves query →\nsuggests Class/Subject/Chapter\n(editable dropdowns)"]
    E --> F["Teacher confirms/adjusts:\nClass, Subject, Chapter, Language, Duration, Mode"]
    F --> G["Tap 'Generate Teaching Kit'"]
    G --> H["POST /teaching-kit/generate\n→ request_id, SSE stream opens"]
    H --> I["GenerationProgress UI:\nresource cards appear as each streams in"]
    I --> J{"Cached?"}
    J -- "yes, per resource" --> K["Resource appears near-instantly\n(no spinner, subtle 'from library' tag)"]
    J -- "no" --> L["LLM/TTS/export call runs\n(worker for PPT/PDF/audio render)"]
    L --> K
    K --> M["All resources streamed →\nkit_complete event"]
    M --> N["Teacher lands on Teaching-Kit result view:\ntabs per resource, all interactive"]
    N --> O{"Teacher action"}
    O -- "Save" --> P["POST /library/saved → appears in Saved Lessons"]
    O -- "Export" --> Q["POST /resources/{id}/export →\nPDF/PPTX/PNG download"]
    O -- "Regenerate one resource" --> R["POST /resources/{id}/regenerate\n(e.g. different worksheet mix)"]
    O -- "Nothing, just teach" --> S["Kit remains accessible offline\nif previously opened (service worker cache)"]
```

Key UX commitment: the teacher never sees a single blank "generating..." screen for the full pipeline duration. Each resource card individually resolves (cache hit = instant, cache miss = short generation state scoped to that one card), so perceived latency is the slowest *individual* resource, not the sum of all of them.

## 3. Cache hit vs miss — what the teacher actually experiences

| | Cache hit | Cache miss |
|---|---|---|
| Lesson plan card | Appears in <1s, "Ready" badge | Appears after LLM call (~3–6s), no badge |
| Worksheet card | Appears in <1s | Appears after generation + PDF render (~5–10s) |
| Audio card | Instant playback available | Progress bar while TTS renders, then playable |
| PPT card | Instant thumbnail preview | Outline generates, then thumbnails render progressively per slide |

No cache-hit/miss distinction is exposed as jargon to the teacher — only a subtle "Ready" vs. brief loading shimmer. Internally every event is logged to `analytics_events` (`cache_hit`/`cache_miss`) for the ops-facing effectiveness dashboard.

## 4. Voice input flow

```mermaid
sequenceDiagram
    actor T as Teacher
    participant W as Web App
    participant API as FastAPI

    T->>W: Tap mic icon
    W->>T: Recording indicator (pulse animation), listening in preferred language
    T->>W: Speaks query
    W->>API: POST /voice/transcribe (audio blob, language_hint)
    API-->>W: {text, detected_language}
    W->>T: Search box fills with transcribed text, editable before submit
    T->>W: Confirms / edits / taps search
    Note over W: Continues into Core Loop (flow 2)
```

If transcription confidence is low or `detected_language` disagrees with `preferred_language`, the UI shows the text with a "did we get this right?" affordance rather than silently proceeding — misheard chapter names are the single highest-cost error in this flow (wrong topic generated).

## 5. School admin flow

```mermaid
flowchart LR
    A["School Admin logs in"] --> B["Admin dashboard:\nteacher roster + usage summary"]
    B --> C{"Action"}
    C -- "Invite teacher" --> D["POST /admin/schools/{id}/teachers\n→ SMS/email invite"]
    C -- "View analytics" --> E["GET /analytics/overview?school_id=\nMost-used subjects, active teacher count, kits/week"]
    C -- "Deactivate teacher" --> F["PATCH /admin/teachers/{id}"]
```

## 6. Super admin flow

Same shape as school admin, scoped platform-wide plus `admin/schools` CRUD and cross-school analytics — no separate flow diagram needed; it's flow 5 with `school_id` omitted and an additional Schools management screen.
