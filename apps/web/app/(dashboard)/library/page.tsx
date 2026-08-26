"use client";

import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import { SavedLessonCard } from "@/components/library/SavedLessonCard";
import { getSavedLessons, searchSavedLessons } from "@/lib/api-client";
import type { SavedLesson, SavedLessonsPage } from "@shiksha-sathi/shared-types";

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export default function LibraryPage() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  const [page, setPage] = useState<SavedLessonsPage | null>(null);
  const [searchResults, setSearchResults] = useState<SavedLesson[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch the default list on mount
  useEffect(() => {
    setLoading(true);
    getSavedLessons()
      .then(setPage)
      .catch(() => setError("Couldn't load your saved lessons."))
      .finally(() => setLoading(false));
  }, []);

  // Search when query changes
  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setSearchResults(null);
      return;
    }
    let cancelled = false;
    searchSavedLessons(debouncedQuery)
      .then((r) => { if (!cancelled) setSearchResults(r); })
      .catch(() => { if (!cancelled) setSearchResults([]); });
    return () => { cancelled = true; };
  }, [debouncedQuery]);

  const displayed: SavedLesson[] =
    searchResults !== null ? searchResults : (page?.items ?? []);

  const isSearching = debouncedQuery.trim().length > 0;

  return (
    <main className="flex flex-1 flex-col gap-6 px-6 py-10 sm:px-8">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-bold tracking-tight">Saved Lessons</h1>
        <p className="text-muted-foreground text-sm">
          Teaching kits you've bookmarked for quick access.
        </p>
      </div>

      {/* Search */}
      <div className="relative w-full max-w-sm">
        <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        <input
          type="search"
          placeholder="Search by chapter or subject…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 pl-9 text-sm shadow-sm transition-colors focus-visible:ring-1 focus-visible:outline-none"
        />
      </div>

      {/* Results */}
      {loading ? (
        <p className="text-muted-foreground text-sm">Loading…</p>
      ) : error ? (
        <p className="text-destructive text-sm">{error}</p>
      ) : displayed.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-16 text-center">
          <p className="text-muted-foreground text-sm">
            {isSearching
              ? `No saved lessons match "${debouncedQuery}".`
              : "You haven't saved any lessons yet. Hit the Save button on any teaching kit!"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {displayed.map((lesson) => (
            <SavedLessonCard key={lesson.id} lesson={lesson} />
          ))}
        </div>
      )}

      {/* Load more (list view only) */}
      {!isSearching && page?.nextCursor && (
        <button
          type="button"
          className="text-primary mx-auto text-sm underline"
          onClick={() => {
            getSavedLessons(page.nextCursor ?? undefined).then((next) =>
              setPage((prev) => ({
                items: [...(prev?.items ?? []), ...next.items],
                nextCursor: next.nextCursor,
              })),
            );
          }}
        >
          Load more
        </button>
      )}
    </main>
  );
}
