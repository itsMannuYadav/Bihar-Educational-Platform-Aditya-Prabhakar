import { GenerateKitForm } from "@/components/dashboard/GenerateKitForm";
import { getMeServer } from "@/lib/api-client.server";

const LANGUAGE_LABEL: Record<string, string> = {
  en: "English",
  hi: "हिंदी",
  hinglish: "Hinglish",
};

async function getApiHealth(): Promise<{ ok: boolean; detail: string }> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${apiUrl}/api/v1/health`, { cache: "no-store" });
    if (!res.ok)
      return { ok: false, detail: `API responded with ${res.status}` };
    const data = await res.json();
    return { ok: data.status === "ok", detail: JSON.stringify(data) };
  } catch {
    return { ok: false, detail: `Could not reach API at ${apiUrl}` };
  }
}

export default async function DashboardPage() {
  const [profile, health] = await Promise.all([getMeServer(), getApiHealth()]);

  return (
    <main className="flex flex-1 flex-col items-center gap-8 px-6 py-16">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="font-heading text-2xl font-bold tracking-tight">
          Namaste, {profile?.name.split(" ")[0]}
        </h1>
        <p className="text-muted-foreground max-w-sm text-sm">
          Pick a class, subject and chapter — the teaching kit streams in as
          each piece is ready.
        </p>
      </div>

      <GenerateKitForm defaultLanguage={profile?.preferredLanguage ?? "hi"} />

      <div className="flex w-full max-w-sm flex-col gap-3">
        <div className="border-border bg-card flex flex-col gap-3 rounded-2xl border p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Your profile</span>
          </div>
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-sm">
            <dt className="text-muted-foreground">Role</dt>
            <dd className="capitalize">{profile?.role.replace("_", " ")}</dd>
            <dt className="text-muted-foreground">Language</dt>
            <dd>{profile ? LANGUAGE_LABEL[profile.preferredLanguage] : "—"}</dd>
          </dl>
        </div>

        <div className="border-border bg-card flex flex-col gap-3 rounded-2xl border p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Backend API</span>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                health.ok
                  ? "bg-accent text-accent-foreground"
                  : "bg-destructive/10 text-destructive"
              }`}
            >
              {health.ok ? "Connected" : "Unreachable"}
            </span>
          </div>
          <p className="text-muted-foreground text-xs">{health.detail}</p>
        </div>
      </div>
    </main>
  );
}
