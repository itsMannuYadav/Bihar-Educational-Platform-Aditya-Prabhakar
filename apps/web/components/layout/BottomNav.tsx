"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, Home } from "lucide-react";

const TABS = [
  { href: "/dashboard", icon: Home, hi: "होम", label: "Home" },
  { href: "/library", icon: BookOpen, hi: "मेरे किट्स", label: "My Kits" },
  { href: "/analytics", icon: BarChart3, hi: "विश्लेषण", label: "Analytics" },
] as const;

export function BottomNav() {
  const path = usePathname();

  function isActive(href: string) {
    if (href === "/dashboard") return path === "/dashboard";
    return path.startsWith(href);
  }

  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 flex border-t border-border bg-card md:hidden">
      {TABS.map(({ href, icon: Icon, hi, label }) => {
        const active = isActive(href);
        return (
          <Link
            key={label}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex flex-1 flex-col items-center gap-1 pb-3 pt-2 text-[11px] font-medium transition-colors ${
              active ? "text-primary" : "text-muted-foreground"
            }`}
          >
            <Icon
              className="size-5"
              strokeWidth={active ? 2.5 : 1.8}
            />
            <span className="flex flex-col items-center leading-none gap-0.5">
              <span className="text-[10px] font-semibold">{hi}</span>
              <span className="text-[9px] opacity-60">{label}</span>
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
