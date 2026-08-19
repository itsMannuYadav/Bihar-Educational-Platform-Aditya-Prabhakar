"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { BrandMark } from "@/components/common/brand-mark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";

type Method = "phone" | "email";
type Step = "identify" | "verify";

/** Bihar-focused: bare 10-digit numbers are assumed local (+91). A leading
 * `+` is taken as an already-international number. */
function toE164(input: string): string {
  const trimmed = input.trim();
  const digits = trimmed.replace(/\D/g, "");
  if (trimmed.startsWith("+")) return `+${digits}`;
  return `+91${digits}`;
}

export default function LoginPage() {
  const router = useRouter();
  const [supabase] = useState(() => {
    try {
      return createClient();
    } catch {
      return null;
    }
  });

  const [method, setMethod] = useState<Method>("phone");
  const [step, setStep] = useState<Step>("identify");
  const [identifier, setIdentifier] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function switchMethod(next: Method) {
    setMethod(next);
    setStep("identify");
    setIdentifier("");
    setCode("");
    setError(null);
  }

  async function sendCode(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!supabase) return;

    if (method === "phone" && identifier.replace(/\D/g, "").length < 10) {
      setError("Enter a valid 10-digit mobile number.");
      return;
    }
    if (method === "email" && !identifier.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }

    setLoading(true);
    const { error } =
      method === "phone"
        ? await supabase.auth.signInWithOtp({ phone: toE164(identifier) })
        : await supabase.auth.signInWithOtp({ email: identifier.trim() });
    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }
    setStep("verify");
  }

  async function verifyCode(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!supabase) return;

    if (code.trim().length < 6) {
      setError("Enter the 6-digit code.");
      return;
    }

    setLoading(true);
    const { error } =
      method === "phone"
        ? await supabase.auth.verifyOtp({ phone: toE164(identifier), token: code, type: "sms" })
        : await supabase.auth.verifyOtp({ email: identifier.trim(), token: code, type: "email" });
    setLoading(false);

    if (error) {
      setError(error.message);
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
          <p className="text-muted-foreground text-sm">Sign in to start teaching, in minutes.</p>
        </div>

        <div className="border-border bg-card flex w-full flex-col gap-5 rounded-2xl border p-5">
          {!supabase ? (
            <p className="text-muted-foreground text-sm">
              Supabase isn&apos;t configured yet — copy{" "}
              <code className="font-mono text-xs">apps/web/.env.example</code> to{" "}
              <code className="font-mono text-xs">.env.local</code> and fill in your project&apos;s
              URL and anon key to enable sign-in.
            </p>
          ) : step === "identify" ? (
            <>
              <div className="bg-secondary flex gap-1 rounded-full p-1">
                <button
                  type="button"
                  onClick={() => switchMethod("phone")}
                  className={`flex-1 rounded-full py-2 text-sm font-semibold transition-colors ${
                    method === "phone"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  Mobile OTP
                </button>
                <button
                  type="button"
                  onClick={() => switchMethod("email")}
                  className={`flex-1 rounded-full py-2 text-sm font-semibold transition-colors ${
                    method === "email"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  Email OTP
                </button>
              </div>

              <form onSubmit={sendCode} className="flex flex-col gap-3">
                <Input
                  type={method === "phone" ? "tel" : "email"}
                  inputMode={method === "phone" ? "tel" : "email"}
                  placeholder={method === "phone" ? "98765 43210" : "you@example.com"}
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  autoFocus
                />
                {error && <p className="text-destructive text-sm">{error}</p>}
                <Button type="submit" disabled={loading || !identifier} className="w-full">
                  {loading ? "Sending…" : "Send code"}
                </Button>
              </form>
            </>
          ) : (
            <form onSubmit={verifyCode} className="flex flex-col gap-3">
              <p className="text-sm">
                Enter the code sent to <span className="font-semibold">{identifier}</span>
              </p>
              <Input
                inputMode="numeric"
                maxLength={6}
                placeholder="123456"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                autoFocus
                className="text-center text-lg tracking-[0.4em]"
              />
              {error && <p className="text-destructive text-sm">{error}</p>}
              <Button type="submit" disabled={loading || code.length < 6} className="w-full">
                {loading ? "Verifying…" : "Verify & continue"}
              </Button>
              <button
                type="button"
                onClick={() => setStep("identify")}
                className="text-muted-foreground text-sm underline-offset-2 hover:underline"
              >
                Use a different {method === "phone" ? "number" : "email"}
              </button>
            </form>
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
