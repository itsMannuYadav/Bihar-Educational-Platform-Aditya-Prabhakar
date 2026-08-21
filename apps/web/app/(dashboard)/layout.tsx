import Link from "next/link";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { BrandMark } from "@/components/common/brand-mark";
import { getMeServer } from "@/lib/api-client.server";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const profile = await getMeServer();
  if (!profile) redirect("/onboarding");

  return (
    <div className="flex min-h-full flex-col">
      <header className="border-border flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <BrandMark size="sm" />
            <span className="font-heading text-lg font-bold">
              Shiksha <span className="text-primary">Sathi</span>
            </span>
          </div>
          <nav className="hidden items-center gap-1 sm:flex">
            <Link
              href="/dashboard"
              className="text-muted-foreground hover:text-foreground rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/library"
              className="text-muted-foreground hover:text-foreground rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
            >
              Library
            </Link>
            <Link
              href="/analytics"
              className="text-muted-foreground hover:text-foreground rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
            >
              Analytics
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground hidden text-sm sm:inline">{profile.name}</span>
          <SignOutButton />
        </div>
      </header>
      {children}
    </div>
  );
}
