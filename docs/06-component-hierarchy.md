# Component Hierarchy

## 1. Dashboard (`app/(dashboard)/dashboard/page.tsx`)

```
<AppShell>                                   # common/AppShell.tsx — top nav + language switcher + user menu
  <TopNav items={[Search, Library, MyResources, SavedLessons, Worksheets, Analytics*, Settings]} />
  <DashboardPage>
    <HeroSearch>                             # dashboard/HeroSearch.tsx
      <SearchInput placeholder={localizedPlaceholder} />
      <VoiceInputButton onTranscript={...} /># dashboard/VoiceInputButton.tsx → useVoiceInput hook
    </HeroSearch>
    <ClassSubjectChapterPicker               # dashboard/ClassSubjectChapterPicker.tsx
      onResolve={(class, subject, chapter) => ...} />
    <GenerationOptionsBar>                   # language, duration, teaching-mode selectors
      <LanguageSwitcher compact />
      <DurationSelect options={[30,40,60]} />
      <TeachingModeSelect options={[story, activity, exam, concept, quick_revision]} />
    </GenerationOptionsBar>
    <GenerateButton size="lg" />             # primary CTA, disabled until class/subject/chapter resolved
    <RecentKitsGrid>                         # dashboard/RecentKitsGrid.tsx — last N requests, React Query
      <KitCard *N />
    </RecentKitsGrid>
  </DashboardPage>
</AppShell>
```
`*` Analytics nav item conditionally rendered only for `school_admin`/`super_admin` roles.

## 2. Generation → Teaching-Kit result (`app/teaching-kit/[requestId]/page.tsx`)

```
<AppShell>
  <TeachingKitHeader>                        # chapter/class/subject breadcrumb, language + mode badges
    <SaveToLibraryButton />
    <ShareOrPrintButton />
  </TeachingKitHeader>

  <GenerationProgress                        # teaching-kit/GenerationProgress.tsx
    visible={status !== 'complete'}
    stream={useTeachingKitStream(requestId)} # hook wraps EventSource, exposes per-resource state
  />

  <ResourceTabs>                             # teaching-kit/ResourceTabs.tsx (shadcn Tabs)
    <Tab id="lesson_plan"><LessonPlanView /></Tab>
    <Tab id="teaching_script"><ScriptView /></Tab>          # includes "Blackboard Mode" toggle
    <Tab id="questions"><QuestionBankView difficultyFilter /></Tab>
    <Tab id="worksheet"><WorksheetViewer exportPdf /></Tab>
    <Tab id="presentation"><PptViewer versionTabs={[5,10,15]} exportPptx exportPdf /></Tab>
    <Tab id="mind_map"><MindMapCanvas zoomable printable downloadable /></Tab>
    <Tab id="audio"><AudioPlayer durationTabs={[1,3,5]} /></Tab>
    <Tab id="local_context" disabled={!enabled}>Coming in full release</Tab>
    <Tab id="video" disabled>
      <ComingSoonPanel feature="Video Generation" />          # video/ComingSoonPanel.tsx — UI stub, always disabled
    </Tab>
  </ResourceTabs>
</AppShell>
```

Each `*View`/`*Viewer` component:
- Renders from `generated_resources.content` (already-fetched via `GET /resources/{id}` or streamed in).
- Owns its own "Regenerate" affordance calling `POST /resources/{id}/regenerate` with type-specific param controls (e.g. `QuestionBankView` has a difficulty re-roll; `WorksheetViewer` has a section-type checklist).
- Is independently offline-cacheable (`useOfflineResource` hook) — a teacher can mark just the worksheet or just the audio for offline use without saving the whole kit.

## 3. Shared/common components

```
common/
  AppShell.tsx
  TopNav.tsx
  LanguageSwitcher.tsx        # en / hi / hinglish, persists to user.preferred_language + zustand uiStore
  EmptyState.tsx
  LoadingSkeletons.tsx        # resource-card shimmer, matches each resource type's real layout (no generic spinner)
  ErrorBoundaryCard.tsx       # per-resource-card error isolation — one failed generation never blanks the whole kit
```

## 4. Admin components (`app/admin/*`)

```
admin/
  TeacherTable.tsx            # roster + invite/deactivate actions
  SchoolForm.tsx               # super_admin only
  AnalyticsCharts.tsx          # top topics, engagement — recharts or visx, wraps dataviz-skill conventions
```

## 5. State ownership summary

| Concern | Owner |
|---|---|
| Auth session | Supabase client SDK + `proxy.ts` (Next.js 16's renamed `middleware.ts`) |
| Server data (catalog, kits, resources, library, analytics) | React Query |
| Active language, active teaching mode, generation-form draft | Zustand `uiStore` / `draftFormStore` |
| Voice recording state (recording/transcribing/error) | Zustand `voiceStore` (or local component state — small enough either way) |
| SSE stream state for an in-progress generation | `useTeachingKitStream` hook, feeds React Query cache updates (not a separate store) |
| Offline-saved resource IDs | IndexedDB via `useOfflineResource`, not duplicated into Zustand |
