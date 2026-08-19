import "server-only";

import type { UserProfile } from "@shiksha-sathi/shared-types";

import { createClient } from "@/lib/supabase/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Server Component / layout variant of getMe() — lib/api-client.ts's version
 * depends on the browser Supabase client and can't run here. Used to gate
 * app/(dashboard)/layout.tsx before rendering any protected page. */
export async function getMeServer(): Promise<UserProfile | null> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) return null;

  const res = await fetch(`${API_URL}/api/v1/me`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
    cache: "no-store",
  });

  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`);
  return res.json();
}
