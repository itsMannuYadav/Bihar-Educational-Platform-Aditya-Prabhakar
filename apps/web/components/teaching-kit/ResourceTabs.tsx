"use client";

import type {
  GeneratedResource,
  LessonPlanContent,
  MindMapNode,
  PresentationContent,
  QuestionSetContent,
  ResourceType,
  TeachingScriptContent,
  WorksheetContent,
} from "@shiksha-sathi/shared-types";
import { isPlaceholder } from "@shiksha-sathi/shared-types";
import { Loader2, RefreshCw } from "lucide-react";
import { useState } from "react";

import { ComingSoonPanel } from "@/components/teaching-kit/ComingSoonPanel";
import { LessonPlanView } from "@/components/teaching-kit/LessonPlanView";
import { MindMapCanvas } from "@/components/teaching-kit/MindMapCanvas";
import { PptViewer } from "@/components/teaching-kit/PptViewer";
import { QuestionBankView } from "@/components/teaching-kit/QuestionBankView";
import { ScriptView } from "@/components/teaching-kit/ScriptView";
import { WorksheetViewer } from "@/components/teaching-kit/WorksheetViewer";
import { regenerateResource } from "@/lib/api-client";

export const TAB_ORDER: ResourceType[] = [
  "lesson_plan",
  "teaching_script",
  "questions",
  "worksheet",
  "presentation",
  "mind_map",
  "audio",
];

export const TAB_LABEL: Partial<Record<ResourceType, string>> = {
  lesson_plan: "Lesson Plan",
  teaching_script: "Script",
  questions: "Questions",
  worksheet: "Worksheet",
  presentation: "Slides",
  mind_map: "Mind Map",
  audio: "Audio",
};

/** Resource types with no generator behind them yet, so the tab renders a
 * ComingSoonPanel and hides its Regenerate control. */
const NO_GENERATOR: Partial<Record<ResourceType, string>> = {
  audio: "Audio narration",
};

interface Props {
  resources: GeneratedResource[];
  chapterName: string;
  /** Types still streaming in — rendered as disabled tabs so the tab strip
   * doesn't reshuffle underneath the teacher as each resource lands. */
  pendingTypes: ResourceType[];
}

function ResourceBody({
  resource,
  chapterName,
}: {
  resource: GeneratedResource;
  chapterName: string;
}) {
  if (isPlaceholder(resource.content)) {
    return (
      <ComingSoonPanel
        feature={TAB_LABEL[resource.resourceType] ?? resource.resourceType}
        detail={resource.content.note}
      />
    );
  }

  switch (resource.resourceType) {
    case "lesson_plan":
      return (
        <LessonPlanView
          content={resource.content as unknown as LessonPlanContent}
        />
      );
    case "teaching_script":
      return (
        <ScriptView
          content={resource.content as unknown as TeachingScriptContent}
        />
      );
    case "questions":
      return (
        <QuestionBankView
          content={resource.content as unknown as QuestionSetContent}
        />
      );
    case "worksheet":
      return (
        <WorksheetViewer
          content={resource.content as unknown as WorksheetContent}
          chapterName={chapterName}
        />
      );
    case "presentation":
      return (
        <PptViewer
          resourceId={resource.id}
          content={resource.content as unknown as PresentationContent}
          chapterName={chapterName}
        />
      );
    case "mind_map":
      return (
        <MindMapCanvas content={resource.content as unknown as MindMapNode} />
      );
    default:
      return (
        <ComingSoonPanel
          feature={TAB_LABEL[resource.resourceType] ?? resource.resourceType}
        />
      );
  }
}

export function ResourceTabs({ resources, chapterName, pendingTypes }: Props) {
  const [activeType, setActiveType] = useState<ResourceType>("lesson_plan");
  // Keyed by type rather than merged into `resources`: a re-roll returns a new
  // resource id, and the parent's copy is still whatever the stream delivered.
  const [regenerated, setRegenerated] = useState<
    Partial<Record<ResourceType, GeneratedResource>>
  >({});
  const [regenerating, setRegenerating] = useState<ResourceType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const byType = new Map(resources.map((r) => [r.resourceType, r]));
  const tabs = TAB_ORDER.filter(
    (t) => byType.has(t) || pendingTypes.includes(t),
  );
  const active = regenerated[activeType] ?? byType.get(activeType);

  async function handleRegenerate() {
    if (!active) return;
    setRegenerating(activeType);
    setError(null);
    try {
      const next = await regenerateResource(active.id);
      setRegenerated((prev) => ({ ...prev, [activeType]: next }));
    } catch {
      setError("Couldn't regenerate this resource. Please try again.");
    } finally {
      setRegenerating(null);
    }
  }

  return (
    <div className="flex w-full flex-col gap-4">
      <div
        role="tablist"
        aria-label="Teaching kit resources"
        className="border-border flex gap-1 overflow-x-auto border-b print:hidden"
      >
        {tabs.map((type) => {
          const ready = byType.has(type);
          const selected = activeType === type;
          return (
            <button
              key={type}
              role="tab"
              type="button"
              aria-selected={selected}
              disabled={!ready}
              onClick={() => setActiveType(type)}
              className={`flex shrink-0 items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium whitespace-nowrap transition-colors ${
                selected
                  ? "border-primary text-foreground"
                  : "text-muted-foreground border-transparent"
              } ${ready ? "hover:text-foreground" : "cursor-not-allowed opacity-50"}`}
            >
              {!ready && <Loader2 className="size-3.5 animate-spin" />}
              {TAB_LABEL[type] ?? type}
            </button>
          );
        })}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {active ? (
        <div role="tabpanel" className="flex flex-col gap-4">
          {!NO_GENERATOR[activeType] && !isPlaceholder(active.content) && (
            <div className="flex items-center justify-between gap-3 print:hidden">
              {active.cacheHit && (
                <span className="text-muted-foreground text-xs">
                  From library
                </span>
              )}
              <button
                type="button"
                onClick={handleRegenerate}
                disabled={regenerating !== null}
                className="text-muted-foreground hover:text-foreground ml-auto flex items-center gap-1.5 text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw
                  className={`size-4 ${regenerating === activeType ? "animate-spin" : ""}`}
                />
                {regenerating === activeType ? "Regenerating…" : "Regenerate"}
              </button>
            </div>
          )}
          <ResourceBody resource={active} chapterName={chapterName} />
        </div>
      ) : (
        <div className="text-muted-foreground flex items-center justify-center gap-2 py-16 text-sm">
          <Loader2 className="size-4 animate-spin" />
          Generating…
        </div>
      )}
    </div>
  );
}
