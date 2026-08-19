# API Design (FastAPI, `/api/v1`)

## 1. Conventions

- All endpoints return `{ data, error }` envelopes; errors use RFC7807-style `{ type, title, detail, status }` in the `error` field.
- Auth: `Authorization: Bearer <supabase_jwt>` on every call except `/health`. Verified via `Depends(get_current_user)`.
- Pagination: cursor-based (`?cursor=&limit=`) on all list endpoints.
- Every generation-triggering endpoint accepts an `Idempotency-Key` header so a flaky mobile connection retry doesn't double-generate.

## 2. Authorization

```python
Role = Literal["teacher", "school_admin", "super_admin"]

def require_role(*roles: Role):
    def dep(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "insufficient_role")
        return user
    return dep
```

Applied per-router: `catalog`/`teaching_kit`/`library`/`voice` → any authenticated user; `admin/*` (school-scoped) → `school_admin, super_admin`; `admin/schools`, `admin/platform` → `super_admin` only. A `school_admin` additionally gets a row-level filter (`school_id = current_user.school_id`) applied in the repository layer, not left to the client to scope correctly.

## 3. Catalog (reference data)

```
GET  /catalog/classes?board_id=
GET  /catalog/subjects?class_id=
GET  /catalog/chapters?subject_id=
GET  /catalog/personas          # teaching-persona list for the mode/persona picker
```

## 4. Teaching-kit generation — the core flow

```
POST /teaching-kit/generate
```

Request:
```json
{
  "class_id": "uuid",
  "subject_id": "uuid",
  "chapter_id": "uuid",
  "language": "hi | en | hinglish",
  "duration": "30 | 40 | 60",
  "teaching_mode": "story | activity | exam | concept | quick_revision",
  "raw_query": "Class 7 ke students ko photosynthesis kaise padhaun",
  "resource_types": ["lesson_plan", "teaching_script", "questions", "worksheet", "presentation", "mind_map", "audio"]
}
```

Response (`202 Accepted`, generation is async):
```json
{ "data": { "request_id": "uuid", "status": "pending", "stream_url": "/teaching-kit/{request_id}/stream" } }
```

`resource_types` lets the frontend request only what the active screen needs (MVP set by default) while the schema/graph already support the full resource-type enum — this is how "everything else should be designed but not fully implemented" is expressed at the API level: the contract exists, the graph nodes for non-MVP types simply aren't registered yet.

```
GET  /teaching-kit/{request_id}                # poll: full current state
GET  /teaching-kit/{request_id}/stream          # SSE: one event per resource as it completes
```

SSE event shape:
```json
event: resource_ready
data: {"resource_type": "lesson_plan", "resource_id": "uuid", "cache_hit": true}
```
```json
event: kit_complete
data: {"request_id": "uuid", "status": "complete", "duration_ms": 4210}
```

Rationale for SSE over WebSocket: generation is one-directional (server → client) and needs to survive through typical school-network HTTP proxies more reliably than raw WS; no bidirectional need exists here.

## 5. Per-resource endpoints (view, regenerate, export)

```
GET  /resources/{resource_id}
POST /resources/{resource_id}/regenerate          # re-run just this node, e.g. teacher wants a different worksheet mix
POST /resources/{resource_id}/export {format}      # pdf | pptx | svg | png — enqueues a worker job
GET  /resources/{resource_id}/export/{job_id}      # poll export job status → file_url on completion
```

Type-specific parameter routes (thin wrappers that set `resource_type` + `params` and call the same underlying generate/regenerate path):

```
POST /resources/questions/generate        {difficulty, count, types: [mcq, short, long, hots]}
POST /resources/previous-year-questions/generate  {years_back, difficulty}
POST /resources/presentation/generate     {version: 5|10|15}
POST /resources/presentation/{id}/export  {format: pptx|pdf|canva}   # canva returns 501 until Phase 6+
POST /resources/audio/generate            {duration_variant: 1|3|5}
POST /resources/mind-map/generate
POST /resources/worksheet/generate        {sections: [fill_blank, true_false, match, label_diagram]}
POST /resources/video/generate            → 501 Not Implemented, {"detail": "coming_soon"}  # stub, matches disabled UI
```

## 6. Voice input

```
POST /voice/transcribe
```
Multipart body: audio blob + `language_hint` (optional). Returns `{ text, detected_language }`. Backend calls `STTProvider.transcribe`; frontend then feeds `text` into the same search/generation flow as typed input — voice is an input modality, not a separate feature path.

## 7. Library

```
GET    /library/saved?cursor=&limit=
POST   /library/saved            {request_id, note?}
DELETE /library/saved/{id}
GET    /library/search?q=&class_id=&subject_id=      # search across the teacher's own past requests + cache-backed global catalog
```

## 8. Analytics (admin)

```
GET /analytics/overview?school_id=&from=&to=          # totals: kits generated, active teachers, top resource types
GET /analytics/top-topics?school_id=&limit=            # from resource_cache.hit_count + analytics_events
GET /analytics/teacher-engagement?school_id=
```

`school_admin` calls are auto-scoped to their own `school_id` (see §2); `super_admin` may omit `school_id` for platform-wide numbers.

## 9. Admin

```
GET    /admin/schools
POST   /admin/schools                # super_admin only
GET    /admin/schools/{id}/teachers
POST   /admin/schools/{id}/teachers  # invite/create teacher account
PATCH  /admin/teachers/{id}          # role change, deactivate
```

## 10. Generation pipeline contract (internal, orchestrator ↔ API)

The `/teaching-kit/generate` handler does not itself call any LLM — it validates input, creates the `teaching_kit_requests` row, and hands off to the LangGraph orchestrator (invoked in-process for MVP scale; extractable to a separate queue-consumed service later without an API contract change, since the API only ever talks to it through `OrchestratorClient.run(request_id)`).

```python
class OrchestratorClient(Protocol):
    async def run(self, request_id: UUID) -> AsyncIterator[ResourceReadyEvent]: ...
```

This is the seam that keeps "one click generates everything, streamed progressively" from becoming a monolithic function — every new resource type is a new graph node plus one line registering it in the default `resource_types` set when it's ready to leave "designed but not implemented" status.
