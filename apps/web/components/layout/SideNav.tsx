"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, BookOpen, HelpCircle, Home, LogOut, Users } from "lucide-react";

import { BrandMark } from "@/components/common/brand-mark";
import { createClient } from "@/lib/supabase/client";

const NAV_LINKS = [
  { href: "/dashboard", icon: Home, hi: "होम", label: "Home" },
  { href: "/library", icon: BookOpen, hi: "मेरे किट्स", label: "My Kits" },
  { href: "/analytics", icon: BarChart3, hi: "विश्लेषण", label: "Analytics" },
] as const;

const COMING_SOON = [
  { icon: Users, label: "Community" },
  { icon: HelpCircle, label: "Help" },
] as const;

export function SideNav({ profileName }: { profileName: string }) {
  const path = usePathname();
  const router = useRouter();

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  function isActive(href: string) {
    if (href === "/dashboard") return path === "/dashboard";
    return path.startsWith(href);
  }

  return (
    <aside className="hidden md:flex sticky top-0 h-screen w-60 shrink-0 flex-col overflow-y-auto border-r border-border bg-card">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 pb-5 pt-5">
        <BrandMark size="sm" />
        <span className="font-heading text-lg font-bold">
          Shiksha <span className="text-primary">Sathi</span>
        </span>
      </div>

      {/* Profile chip */}
      <div className="mx-3 mb-5 rounded-xl bg-muted px-3 py-2.5">
        <p className="text-xs text-muted-foreground">Signed in as</p>
        <p className="truncate text-sm font-semibold text-foreground">{profileName}</p>
      </div>

      {/* Nav links */}
      <ul className="flex flex-1 flex-col gap-0.5 px-2">
        {NAV_LINKS.map(({ href, icon: Icon, label }) => {
          const active = isActive(href);
          return (
            <li key={label}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="size-4.5 shrink-0" />
                <span className="flex flex-col leading-tight">
                  <span className="text-[11px] font-semibold">{hi}</span>
                  <span className="text-[10px] opacity-60">{label}</span>
                </span>
              </Link>
            </li>
          );
        })}

        {COMING_SOON.map(({ icon: Icon, label }) => (
          <li key={label}>
            <span className="flex cursor-default select-none items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground/50">
              <Icon className="size-4.5 shrink-0" />
              {label}
              <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                Soon
              </span>
            </span>
          </li>
        ))}
      </ul>

      {/* Sign out */}
      <div className="border-t border-border px-2 py-4">
        <button
          type="button"
          onClick={signOut}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <LogOut className="size-4.5 shrink-0" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
