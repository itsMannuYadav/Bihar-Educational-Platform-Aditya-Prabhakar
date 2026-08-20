"use client";

import type {
  ResourceType,
  TeachingKitState,
} from "@shiksha-sathi/shared-types";
import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { GenerationProgress } from "@/components/teaching-kit/GenerationProgress";
import { ResourceTabs } from "@/components/teaching-kit/ResourceTabs";
import { TeachingKitHeader } from "@/components/teaching-kit/TeachingKitHeader";
import type { TeachingKitStreamState } from "@/hooks/useTeachingKitStream";
import { useTeachingKitStream } from "@/hooks/useTeachingKitStream";
import { getTeachingKit } from "@/lib/api-client";

const POLL_INTERVAL_MS = 2500;

export function TeachingKitResult({ requestId }: { requestId: string }) {
  const [kit, setKit] = useState<TeachingKitState | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Only set once the initial fetch says this kit hasn't started yet. Opening
  // the stream is what *runs* generation, not just what observes it, so a
  // reload mid-run must poll instead — otherwise the whole kit regenerates in
  // parallel with the run already in flight.
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  const requestedTypes: ResourceType[] = kit?.requestedResourceTypes ?? [];
  const stream = useTeachingKitStream(streamUrl, requestedTypes);

  const refresh = useCallback(async () => {
    const next = await getTeachingKit(requestId);
    setKit(next);
    return next;
  }, [requestId]);

  // The queueMicrotask wrappers below keep every setState out of the effect
  // body itself (react-hooks/set-state-in-effect, a React Compiler rule) —
  // the same pattern as useTeachingKitStream and onboarding/page.tsx. The
  // lint rule can't see that `refresh` only sets state after an await.
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      refresh()
        .then((initial) => {
          if (cancelled) return;
          if (initial.status === "pending") {
            setStreamUrl(`/api/v1/teaching-kit/${requestId}/stream`);
          }
        })
        .catch(() => {
          if (!cancelled) setError("Couldn't load this teaching kit.");
        });
    });
    return () => {
      cancelled = true;
    };
  }, [refresh, requestId]);

  // Two paths land here: our own stream finishing, and a kit that was already
  // running when this page loaded. Both end with one authoritative re-fetch.
  useEffect(() => {
    if (stream.status !== "complete") return;
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) void refresh();
    });
    return () => {
      cancelled = true;
    };
  }, [stream.status, refresh]);

  useEffect(() => {
    if (kit === null || streamUrl !== null) return;
    if (kit.status !== "generating" && kit.status !== "pending") return;

    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [kit, streamUrl, refresh]);

  if (error) {
    return <p className="text-destructive text-sm">{error}</p>;
  }

  if (kit === null) {
    return (
      <div className="text-muted-foreground flex items-center justify-center gap-2 py-24 text-sm">
        <Loader2 className="size-4 animate-spin" />
        Loading…
      </div>
    );
  }

  const readyTypes = new Set(kit.resources.map((r) => r.resourceType));
  const pendingTypes = requestedTypes.filter((t) => !readyTypes.has(t));
  const generating = pendingTypes.length > 0 && kit.status !== "failed";

  // On the polling path there is no stream to read progress from, so the
  // fetched kit *is* the progress. Without this the tiles would all sit
  // spinning on a reload even as resources land.
  const progress: TeachingKitStreamState =
    streamUrl !== null
      ? stream
      : {
          status: kit.status === "failed" ? "failed" : "generating",
          resources: Object.fromEntries(
            kit.resources.map((r) => [
              r.resourceType,
              {
                status: "ready" as const,
                resourceId: r.id,
                cacheHit: r.cacheHit,
              },
            ]),
          ),
          errorDetail: null,
        };

  return (
    <>
      <TeachingKitHeader kit={kit} />

      {generating && (
        <GenerationProgress resourceTypes={requestedTypes} stream={progress} />
      )}

      <ResourceTabs
        resources={kit.resources}
        chapterName={kit.chapterName}
        pendingTypes={pendingTypes}
      />
    </>
  );
}
