"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { BrandMark } from "@/components/common/brand-mark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";

type Mode = "sign-in" | "sign-up";

// Email + password for now — deliberately simpler than the OTP/magic-link
// flow this replaced. That flow needed a Supabase email template exposing
// {{ .Token }} (the project's default only sends a link, not the code the
// UI asked for) and correct ES256 JWKS verification on the backend to work
// at all, for a product with no real users yet. Swap back to OTP + email
// confirmation once there's an actual pilot to protect against throwaway
// signups — password auth alone has no verification step.
export default function LoginPage() {
  const router = useRouter();
  const [supabase] = useState(() => {
    try {
      return createClient();
    } catch {
      return null;
    }
  });

  const [mode, setMode] = useState<Mode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!supabase) return;

    if (!email.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    const { data, error } =
      mode === "sign-in"
        ? await supabase.auth.signInWithPassword({
            email: email.trim(),
            password,
          })
        : await supabase.auth.signUp({ email: email.trim(), password });
    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }
    if (!data.session) {
      // Only reachable if email confirmation gets turned back on later —
      // signUp() returns no session until the address is confirmed.
      setError("Check your email to confirm your account, then sign in.");
      return;
    }
    router.push("/onboarding");
    router.refresh();
  }

  async function continueWithGoogle() {
    setError(null);
    if (!supabase) return;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) setError(error.message);
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="flex w-full max-w-sm flex-col items-center gap-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <BrandMark />
          <h1 className="font-heading text-2xl font-bold tracking-tight">
            Shiksha <span className="text-primary">Sathi</span>
          </h1>
          <p className="text-muted-foreground text-sm">
            Sign in to start teaching, in minutes.
          </p>
        </div>

        <div className="border-border bg-card flex w-full flex-col gap-5 rounded-2xl border p-5">
          {!supabase ? (
            <p className="text-muted-foreground text-sm">
              Supabase isn&apos;t configured yet — copy{" "}
              <code className="font-mono text-xs">apps/web/.env.example</code>{" "}
              to <code className="font-mono text-xs">.env.local</code> and fill
              in your project&apos;s URL and anon key to enable sign-in.
            </p>
          ) : (
            <>
              <div className="bg-secondary flex gap-1 rounded-full p-1">
                <button
                  type="button"
                  onClick={() => switchMode("sign-in")}
                  className={`flex-1 rounded-full py-2 text-sm font-semibold transition-colors ${
                    mode === "sign-in"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  Sign in
                </button>
                <button
                  type="button"
                  onClick={() => switchMode("sign-up")}
                  className={`flex-1 rounded-full py-2 text-sm font-semibold transition-colors ${
                    mode === "sign-up"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  Create account
                </button>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                <Input
                  type="email"
                  inputMode="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                {error && <p className="text-destructive text-sm">{error}</p>}
                <Button
                  type="submit"
                  disabled={loading || !email || !password}
                  className="w-full"
                >
                  {loading
                    ? mode === "sign-in"
                      ? "Signing in…"
                      : "Creating account…"
                    : mode === "sign-in"
                      ? "Sign in"
                      : "Create account"}
                </Button>
              </form>
            </>
          )}

          {supabase && (
            <>
              <div className="flex items-center gap-3">
                <div className="bg-border h-px flex-1" />
                <span className="text-muted-foreground text-xs">or</span>
                <div className="bg-border h-px flex-1" />
              </div>

              <Button
                type="button"
                variant="outline"
                onClick={continueWithGoogle}
                className="w-full"
              >
                Continue with Google
              </Button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
