import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { BrandMark } from "@/components/common/brand-mark";
import { BottomNav } from "@/components/layout/BottomNav";
import { SideNav } from "@/components/layout/SideNav";
import { getMeServer } from "@/lib/api-client.server";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const profile = await getMeServer();
  if (!profile) redirect("/onboarding");

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <SideNav profileName={profile.name} />

      {/* Main content column */}
      <div className="flex min-w-0 flex-1 flex-col pb-16 md:pb-0">
        {/* Mobile-only top bar */}
        <header className="flex items-center justify-between border-b border-border px-4 py-3 md:hidden">
          <div className="flex items-center gap-2.5">
            <BrandMark size="sm" />
            <span className="font-heading text-lg font-bold">
              Shiksha <span className="text-primary">Sathi</span>
            </span>
          </div>
          <SignOutButton />
        </header>

        {children}
      </div>

      {/* Mobile bottom nav */}
      <BottomNav />
    </div>
  );
}
