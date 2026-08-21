"use client";

import type { ResourceType } from "@shiksha-sathi/shared-types";
import { Check, Loader2 } from "lucide-react";

import type { TeachingKitStreamState } from "@/hooks/useTeachingKitStream";

const RESOURCE_LABELS: Partial<Record<ResourceType, string>> = {
  lesson_plan: "Lesson Plan",
  teaching_script: "Teaching Script",
  questions: "Questions",
  worksheet: "Worksheet",
  presentation: "Presentation",
  mind_map: "Mind Map",
  audio: "Audio",
};

interface Props {
  resourceTypes: ResourceType[];
  stream: TeachingKitStreamState;
}

function friendlyError(detail: string | null): string {
  if (detail === "RATE_LIMIT_DAILY") {
    return "You've used up today's free Gemini quota. Your kit will be ready to generate again after midnight when the limit resets.";
  }
  if (detail === "RATE_LIMIT_MINUTE") {
    return "Gemini is a little busy right now. Please wait a minute and try generating again.";
  }
  return "Something went wrong while generating this kit. Please try again.";
}

// No cache-hit/miss jargon exposed to the teacher — just a "Ready" state and
// a subtle "From library" tag, per docs/05-user-flows.md §3.
export function GenerationProgress({ resourceTypes, stream }: Props) {
  return (
    <div className="flex flex-col gap-3">
      {stream.status === "failed" && (
        <p className="text-destructive text-sm">
          {friendlyError(stream.errorDetail)}
        </p>
      )}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {resourceTypes.map((resourceType) => {
          const entry = stream.resources[resourceType];
          const ready = entry?.status === "ready";
          return (
            <div
              key={resourceType}
              className={`border-border flex items-center gap-2 rounded-xl border p-3 text-sm transition-colors ${
                ready ? "bg-card" : "bg-muted/40"
              }`}
            >
              {ready ? (
                <Check className="text-primary size-4 shrink-0" />
              ) : (
                <Loader2 className="text-muted-foreground size-4 shrink-0 animate-spin" />
              )}
              <div className="flex flex-1 flex-col">
                <span className="font-medium">
                  {RESOURCE_LABELS[resourceType] ?? resourceType}
                </span>
                {ready && entry?.cacheHit && (
                  <span className="text-muted-foreground text-xs">
                    From library
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
