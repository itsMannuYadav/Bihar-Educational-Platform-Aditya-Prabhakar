"use client";

import { BarChart3, RefreshCw, TrendingUp, Zap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { type CacheStatsResponse, type ResourceCacheStats, getCacheStats } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const RESOURCE_LABELS: Record<string, string> = {
  lesson_plan: "Lesson Plan",
  teaching_script: "Script",
  questions: "Questions",
  worksheet: "Worksheet",
  presentation: "Slides",
  mind_map: "Mind Map",
  audio: "Audio",
};

function label(rt: string) {
  return RESOURCE_LABELS[rt] ?? rt;
}

function hitRatePct(row: ResourceCacheStats): number | null {
  const total = row.event_hits + row.event_misses;
  if (total === 0) return null;
  return Math.round((row.event_hits / total) * 100);
}

// ---------------------------------------------------------------------------
// Bar component
// ---------------------------------------------------------------------------

function HitRateBar({ pct }: { pct: number }) {
  return (
    <div className="bg-muted relative h-2 w-full overflow-hidden rounded-full">
      <div
        className="bg-primary absolute inset-y-0 left-0 rounded-full transition-all duration-700"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AnalyticsPage() {
  const [data, setData] = useState<CacheStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getCacheStats());
    } catch {
      setError("Could not load analytics. Generate some kits first.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 text-primary flex size-10 items-center justify-center rounded-xl">
            <BarChart3 className="size-5" />
          </div>
          <div>
            <h1 className="font-heading text-xl font-bold">Cache Analytics</h1>
            <p className="text-muted-foreground text-sm">
              Hit rates by resource type — live from the cache layer.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="text-muted-foreground hover:text-foreground flex items-center gap-1.5 text-sm disabled:opacity-50"
        >
          <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Overall hit rate summary card */}
      {data?.overall_hit_rate_pct != null && (
        <div className="border-border bg-card mb-6 flex items-center gap-4 rounded-2xl border p-5">
          <div className="bg-primary/10 flex size-12 items-center justify-center rounded-xl">
            <TrendingUp className="text-primary size-6" />
          </div>
          <div>
            <p className="text-muted-foreground text-sm">Overall cache hit rate</p>
            <p className="font-heading text-3xl font-bold">
              {data.overall_hit_rate_pct}
              <span className="text-muted-foreground ml-1 text-lg font-normal">%</span>
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="border-border bg-card rounded-2xl border p-8 text-center">
          <p className="text-muted-foreground text-sm">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !data && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-muted h-20 animate-pulse rounded-2xl" />
          ))}
        </div>
      )}

      {/* Stats table */}
      {data && data.stats.length > 0 && (
        <div className="border-border bg-card divide-border divide-y overflow-hidden rounded-2xl border">
          {/* Header row */}
          <div className="text-muted-foreground grid grid-cols-[1fr_80px_80px_80px] gap-3 px-5 py-3 text-xs font-semibold uppercase tracking-wide">
            <span>Resource type</span>
            <span className="text-right">Cached</span>
            <span className="text-right">Total hits</span>
            <span className="text-right">Hit rate</span>
          </div>

          {data.stats.map((row) => {
            const pct = hitRatePct(row);
            return (
              <div
                key={row.resource_type}
                className="grid grid-cols-[1fr_80px_80px_80px] items-center gap-3 px-5 py-4"
              >
                <div className="flex flex-col gap-1.5 pr-4">
                  <span className="text-sm font-semibold">{label(row.resource_type)}</span>
                  {pct !== null && <HitRateBar pct={pct} />}
                </div>
                <span className="text-right text-sm tabular-nums">
                  {row.cache_entries}
                </span>
                <span className="text-right text-sm tabular-nums">
                  {row.total_hits.toLocaleString()}
                </span>
                <div className="flex flex-col items-end gap-0.5">
                  {pct !== null ? (
                    <>
                      <span
                        className={`text-sm font-semibold tabular-nums ${
                          pct >= 70
                            ? "text-green-600 dark:text-green-400"
                            : pct >= 40
                              ? "text-amber-600 dark:text-amber-400"
                              : "text-muted-foreground"
                        }`}
                      >
                        {pct}%
                      </span>
                      <span className="text-muted-foreground text-xs tabular-nums">
                        {row.event_hits}/{row.event_hits + row.event_misses}
                      </span>
                    </>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state — no kits generated yet */}
      {data && data.stats.length === 0 && !error && (
        <div className="border-border bg-card flex flex-col items-center gap-3 rounded-2xl border p-12 text-center">
          <Zap className="text-muted-foreground size-10 opacity-40" />
          <p className="text-muted-foreground text-sm">
            No cache entries yet — generate some kits to see hit rates here.
          </p>
        </div>
      )}

      <p className="text-muted-foreground mt-6 text-center text-xs">
        Cache hit rates are live from <code>resource_cache</code> and
        <code className="ml-1">analytics_events</code>.
      </p>
    </main>
  );
}
