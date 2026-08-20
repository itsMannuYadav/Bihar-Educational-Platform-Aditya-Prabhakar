import type {
  Chapter,
  CreateChapterInput,
  CreateUserProfileInput,
  GeneratedResource,
  GenerateTeachingKitRequest,
  PresentationVersion,
  School,
  SchoolClass,
  Subject,
  TeachingKitRequestSummary,
  TeachingKitState,
  UserProfile,
} from "@shiksha-sathi/shared-types";

import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function authedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) throw new ApiError("Not signed in", 401);

  return fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${session.access_token}`,
      ...(init.body ? { "Content-Type": "application/json" } : {}),
    },
  });
}

/** null means "authenticated but no profile yet" — the onboarding-required case. */
export async function getMe(): Promise<UserProfile | null> {
  const res = await authedFetch("/api/v1/me");
  if (res.status === 404) return null;
  if (!res.ok) throw new ApiError("Failed to load profile", res.status);
  return res.json();
}

export async function createMe(
  input: CreateUserProfileInput,
): Promise<UserProfile> {
  const res = await authedFetch("/api/v1/me", {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new ApiError("Failed to create profile", res.status);
  return res.json();
}

export async function searchSchools(query: string): Promise<School[]> {
  const params = query ? `?q=${encodeURIComponent(query)}` : "";
  const res = await authedFetch(`/api/v1/schools${params}`);
  if (!res.ok) throw new ApiError("Failed to search schools", res.status);
  return res.json();
}

export async function getClasses(): Promise<SchoolClass[]> {
  const res = await authedFetch("/api/v1/catalog/classes");
  if (!res.ok) throw new ApiError("Failed to load classes", res.status);
  return res.json();
}

export async function getSubjects(classId: string): Promise<Subject[]> {
  const res = await authedFetch(`/api/v1/catalog/subjects?class_id=${classId}`);
  if (!res.ok) throw new ApiError("Failed to load subjects", res.status);
  return res.json();
}

export async function getChapters(subjectId: string): Promise<Chapter[]> {
  const res = await authedFetch(
    `/api/v1/catalog/chapters?subject_id=${subjectId}`,
  );
  if (!res.ok) throw new ApiError("Failed to load chapters", res.status);
  return res.json();
}

/** Get-or-create: an existing chapter name for this subject (case-insensitive)
 * returns that chapter rather than forking the catalog. */
export async function createChapter(
  input: CreateChapterInput,
): Promise<Chapter> {
  const res = await authedFetch("/api/v1/catalog/chapters", {
    method: "POST",
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new ApiError("Failed to add chapter", res.status);
  return res.json();
}

export async function generateTeachingKit(
  payload: GenerateTeachingKitRequest,
): Promise<TeachingKitRequestSummary> {
  const res = await authedFetch("/api/v1/teaching-kit/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new ApiError("Failed to start generation", res.status);
  return res.json();
}

/** Native EventSource can't send an Authorization header, so the SSE stream
 * takes the access token as a query param instead (backend: get_current_claims
 * query-param fallback). Only used for the one streaming endpoint. */
export async function getTeachingKitStreamUrl(
  streamUrl: string,
): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new ApiError("Not signed in", 401);
  return `${API_URL}${streamUrl}?token=${encodeURIComponent(session.access_token)}`;
}

export async function getTeachingKit(
  requestId: string,
): Promise<TeachingKitState> {
  const res = await authedFetch(`/api/v1/teaching-kit/${requestId}`);
  if (!res.ok) throw new ApiError("Failed to load teaching kit", res.status);
  return res.json();
}

export async function getResource(
  resourceId: string,
): Promise<GeneratedResource> {
  const res = await authedFetch(`/api/v1/resources/${resourceId}`);
  if (!res.ok) throw new ApiError("Failed to load resource", res.status);
  return res.json();
}

/** Re-rolls one resource with type-specific params (difficulty mix, worksheet
 * section list…). Returns a *new* resource — the original row is kept, since
 * identical params resolve to the same cache entry rather than regenerating. */
export async function regenerateResource(
  resourceId: string,
  params: Record<string, unknown> = {},
): Promise<GeneratedResource> {
  const res = await authedFetch(`/api/v1/resources/${resourceId}/regenerate`, {
    method: "POST",
    body: JSON.stringify({ params }),
  });
  if (!res.ok) throw new ApiError("Failed to regenerate resource", res.status);
  return res.json();
}

/** Fetches the .pptx as a blob and hands it to the browser as a download.
 * A plain <a href> can't carry the Authorization header this endpoint needs. */
export async function downloadPresentation(
  resourceId: string,
  version: PresentationVersion,
  filename: string,
): Promise<void> {
  const res = await authedFetch(
    `/api/v1/resources/${resourceId}/export?format=pptx&version=${version}`,
  );
  if (!res.ok) throw new ApiError("Failed to export deck", res.status);

  const url = URL.createObjectURL(await res.blob());
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  } finally {
    // Revoking synchronously after click() is safe: the browser has already
    // resolved the blob by then, and leaving it un-revoked leaks the whole
    // file until the tab is closed.
    URL.revokeObjectURL(url);
  }
}
