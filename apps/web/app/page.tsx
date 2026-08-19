import { redirect } from "next/navigation";

// proxy.ts (see apps/web/proxy.ts) sends authenticated visitors to /dashboard
// and everyone else to /login before this ever renders — this redirect only
// covers the case where proxy didn't run for some reason.
export default function Home() {
  redirect("/login");
}
