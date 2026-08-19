"use client";

import type {
  KitCompleteEvent,
  ResourceReadyEvent,
  ResourceType,
} from "@shiksha-sathi/shared-types";
import { useEffect, useState } from "react";

import { getTeachingKitStreamUrl } from "@/lib/api-client";

export interface ResourceStreamEntry {
  status: "pending" | "ready";
  resourceId?: string;
  cacheHit?: boolean;
}

export type KitStreamStatus =
  "connecting" | "generating" | "complete" | "failed";

export interface TeachingKitStreamState {
  status: KitStreamStatus;
  resources: Partial<Record<ResourceType, ResourceStreamEntry>>;
  errorDetail: string | null;
}

function initialState(resourceTypes: ResourceType[]): TeachingKitStreamState {
  return {
    status: "connecting",
    resources: Object.fromEntries(
      resourceTypes.map((rt) => [rt, { status: "pending" as const }]),
    ) as TeachingKitStreamState["resources"],
    errorDetail: null,
  };
}

/** Subscribes to `GET /teaching-kit/{id}/stream` via EventSource. Native
 * EventSource can't send an Authorization header, so the URL carries the
 * access token as a query param (see getTeachingKitStreamUrl) — the backend
 * accepts that as a fallback only on this one endpoint. */
export function useTeachingKitStream(
  streamUrl: string | null,
  resourceTypes: ResourceType[],
): TeachingKitStreamState {
  const [state, setState] = useState<TeachingKitStreamState>(() =>
    initialState(resourceTypes),
  );
  const resourceTypesKey = resourceTypes.join(",");

  useEffect(() => {
    if (!streamUrl) return;

    let cancelled = false;
    let source: EventSource | null = null;

    // Deferred to a microtask so no setState call is synchronous within the
    // effect body itself (react-hooks/set-state-in-effect).
    queueMicrotask(() => {
      if (cancelled) return;
      setState(initialState(resourceTypesKey.split(",") as ResourceType[]));
    });

    getTeachingKitStreamUrl(streamUrl)
      .then((url) => {
        if (cancelled) return;
        source = new EventSource(url);

        source.addEventListener("open", () => {
          setState((s) =>
            s.status === "connecting" ? { ...s, status: "generating" } : s,
          );
        });

        source.addEventListener("resource_ready", (event) => {
          const data = JSON.parse(
            (event as MessageEvent).data,
          ) as ResourceReadyEvent;
          setState((s) => ({
            ...s,
            status: "generating",
            resources: {
              ...s.resources,
              [data.resourceType]: {
                status: "ready",
                resourceId: data.resourceId,
                cacheHit: data.cacheHit,
              },
            },
          }));
        });

        source.addEventListener("kit_complete", (event) => {
          void (JSON.parse((event as MessageEvent).data) as KitCompleteEvent);
          setState((s) => ({ ...s, status: "complete" }));
          source?.close();
        });

        // Named server event, not EventSource's native connection-error —
        // that one only fires without a `data` payload, handled separately below.
        source.addEventListener("generation_failed", (event) => {
          const data = JSON.parse((event as MessageEvent).data) as {
            detail: string;
          };
          setState((s) => ({
            ...s,
            status: "failed",
            errorDetail: data.detail,
          }));
          source?.close();
        });

        source.addEventListener("error", () => {
          setState((s) =>
            s.status === "complete" || s.status === "failed"
              ? s
              : {
                  ...s,
                  status: "failed",
                  errorDetail: s.errorDetail ?? "Connection lost.",
                },
          );
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState((s) => ({
          ...s,
          status: "failed",
          errorDetail:
            err instanceof Error ? err.message : "Failed to connect.",
        }));
      });

    return () => {
      cancelled = true;
      source?.close();
    };
  }, [streamUrl, resourceTypesKey]);

  return state;
}
