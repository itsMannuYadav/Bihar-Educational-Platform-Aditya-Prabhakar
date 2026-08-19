import { type NextRequest, NextResponse } from "next/server";

import { createMiddlewareClient } from "@/lib/supabase/middleware";

const PUBLIC_ONLY_PATHS = new Set(["/login"]);

function redirectTo(request: NextRequest, path: string, refreshedResponse: NextResponse) {
  const redirect = NextResponse.redirect(new URL(path, request.url));
  // Carry over any Set-Cookie from a token refresh that happened during
  // getClaims() below — a fresh NextResponse.redirect() would otherwise drop it.
  for (const cookie of refreshedResponse.cookies.getAll()) {
    redirect.cookies.set(cookie);
  }
  return redirect;
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  let isAuthenticated = false;
  let response = NextResponse.next({ request });

  try {
    const { supabase, getResponse } = createMiddlewareClient(request);
    const { data } = await supabase.auth.getClaims();
    isAuthenticated = data !== null;
    response = getResponse();
  } catch (err) {
    // Supabase isn't configured yet (see apps/web/.env.example, docs/07-roadmap.md
    // Phase 2) — fail closed to "signed out" so /login still renders instead of
    // every route 500ing.
    console.warn("[proxy] Supabase auth check failed, treating as signed out:", err);
  }

  if (PUBLIC_ONLY_PATHS.has(pathname)) {
    return isAuthenticated ? redirectTo(request, "/dashboard", response) : response;
  }

  if (!isAuthenticated) {
    return redirectTo(request, "/login", response);
  }

  if (pathname === "/") {
    return redirectTo(request, "/dashboard", response);
  }

  return response;
}

export const config = {
  matcher: ["/", "/login", "/onboarding", "/dashboard/:path*"],
};
