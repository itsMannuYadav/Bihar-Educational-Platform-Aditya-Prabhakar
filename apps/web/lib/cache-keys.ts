import type {
  AppLanguage,
  DurationOption,
  ResourceType,
  TeachingMode,
} from "@shiksha-sathi/shared-types";

export interface CacheKeyInput {
  classId: string;
  subjectId: string;
  chapterId: string;
  language: AppLanguage;
  duration: DurationOption;
  teachingMode: TeachingMode;
  resourceType: ResourceType;
  params?: Record<string, unknown>;
}

/** Byte-for-byte port of Python's `json.dumps(params, sort_keys=True,
 * separators=(",", ":"))`.
 *
 * `JSON.stringify` alone is not equivalent: it preserves insertion order
 * instead of sorting keys, so `{a:1,b:2}` and `{b:2,a:1}` would hash
 * differently here but identically on the backend. Sorting has to recurse —
 * Python sorts keys at every level, not just the top one.
 */
function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;

  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([, v]) => v !== undefined)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(",")}}`;
}

/** sha256 of the pipe-joined generation params, matching
 * `apps/api/app/cache/keys.py::compute_cache_key` exactly — the field order,
 * the separator and the params encoding are all load-bearing. If the two ever
 * disagree, the frontend's optimistic cache lookups silently miss every time
 * and every "instant" repeat request pays for a full regeneration.
 *
 * Async because SubtleCrypto is: it is only available in secure contexts
 * (https or localhost), which the app already requires for Supabase auth.
 */
export async function computeCacheKey(input: CacheKeyInput): Promise<string> {
  const raw = [
    input.classId,
    input.subjectId,
    input.chapterId,
    input.language,
    input.duration,
    input.teachingMode,
    input.resourceType,
    canonicalJson(input.params ?? {}),
  ].join("|");

  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(raw),
  );
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
