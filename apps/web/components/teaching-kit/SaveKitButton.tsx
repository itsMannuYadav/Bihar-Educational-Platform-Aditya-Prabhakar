"use client";

import type { SavedLesson } from "@shiksha-sathi/shared-types";
import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { ApiError, getSavedForRequest, saveLesson, unsaveLesson } from "@/lib/api-client";

interface Props {
  requestId: string;
}

export function SaveKitButton({ requestId }: Props) {
  const [saved, setSaved] = useState<SavedLesson | null | "loading">("loading");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getSavedForRequest(requestId)
      .then((s) => { if (!cancelled) setSaved(s); })
      .catch(() => { if (!cancelled) setSaved(null); });
    return () => { cancelled = true; };
  }, [requestId]);

  async function toggle() {
    if (busy || saved === "loading") return;
    setBusy(true);
    try {
      if (saved) {
        await unsaveLesson(saved.id);
        setSaved(null);
      } else {
        const s = await saveLesson(requestId);
        setSaved(s);
      }
    } catch (err) {
      console.error("Save toggle failed:", err instanceof ApiError ? err.message : err);
    } finally {
      setBusy(false);
    }
  }

  const isSaved = saved !== "loading" && saved !== null;

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={busy || saved === "loading"}
      aria-label={isSaved ? "Remove from saved lessons" : "Save this lesson"}
      title={isSaved ? "Saved — click to remove" : "Save to Library"}
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${
        isSaved
          ? "bg-primary/10 text-primary hover:bg-primary/20"
          : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
      }`}
    >
      {busy ? (
        <Loader2 className="size-3.5 animate-spin" />
      ) : isSaved ? (
        <BookmarkCheck className="size-3.5" />
      ) : (
        <Bookmark className="size-3.5" />
      )}
      {isSaved ? "Saved" : "Save"}
    </button>
  );
}
