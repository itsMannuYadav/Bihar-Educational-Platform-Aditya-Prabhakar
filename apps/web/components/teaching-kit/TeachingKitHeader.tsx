import type { TeachingKitState } from "@shiksha-sathi/shared-types";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

import { SaveKitButton } from "@/components/teaching-kit/SaveKitButton";

const LANGUAGE_LABEL: Record<string, string> = {
  en: "English",
  hi: "हिंदी",
  hinglish: "Hinglish",
};

const MODE_LABEL: Record<string, string> = {
  concept: "Concept",
  story: "Story",
  activity: "Activity",
  exam: "Exam",
  quick_revision: "Quick revision",
};

export function TeachingKitHeader({ kit }: { kit: TeachingKitState }) {
  return (
    <header className="flex flex-col gap-3 print:hidden">
      <Link
        href="/dashboard"
        className="text-muted-foreground hover:text-foreground flex w-fit items-center gap-1 text-sm font-medium"
      >
        <ChevronLeft className="size-4" />
        Dashboard
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground text-xs">
            {kit.classDisplayName} · {kit.subjectName}
          </p>
          <h1 className="font-heading text-xl font-bold tracking-tight sm:text-2xl">
            {kit.chapterName}
          </h1>
        </div>
        <SaveKitButton requestId={kit.requestId} />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {[
          LANGUAGE_LABEL[kit.language] ?? kit.language,
          `${kit.duration} min`,
          MODE_LABEL[kit.teachingMode] ?? kit.teachingMode,
        ].map((badge) => (
          <span
            key={badge}
            className="bg-secondary text-secondary-foreground rounded-full px-2.5 py-0.5 text-xs font-medium"
          >
            {badge}
          </span>
        ))}
      </div>
    </header>
  );
}
