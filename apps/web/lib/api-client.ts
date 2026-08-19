import type { CreateUserProfileInput, School, UserProfile } from "@shiksha-sathi/shared-types";

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

async function authedFetch(path: string, init: RequestInit = {}): Promise<Response> {
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

export async function createMe(input: CreateUserProfileInput): Promise<UserProfile> {
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
