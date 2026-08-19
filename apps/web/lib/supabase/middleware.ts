import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

import { getSupabaseEnv } from "./env";

/** Session-refreshing Supabase client for proxy.ts (Next.js 16's renamed
 * `middleware.ts`) — the one place a token refresh's Set-Cookie can still land
 * on the response before it's committed. See lib/supabase/server.ts for why
 * Server Components can't do this themselves. */
export function createMiddlewareClient(request: NextRequest) {
  let response = NextResponse.next({ request });
  const { url, anonKey } = getSupabaseEnv();

  const supabase = createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  return { supabase, getResponse: () => response };
}
