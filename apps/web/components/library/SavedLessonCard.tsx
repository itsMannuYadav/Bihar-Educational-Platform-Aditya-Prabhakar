import type { SavedLesson } from "@shiksha-sathi/shared-types";
import Link from "next/link";

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

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function SavedLessonCard({ lesson }: { lesson: SavedLesson }) {
  const badges = [
    LANGUAGE_LABEL[lesson.language] ?? lesson.language,
    `${lesson.duration} min`,
    MODE_LABEL[lesson.teachingMode] ?? lesson.teachingMode,
  ];

  return (
    <Link
      href={`/teaching-kit/${lesson.requestId}`}
      className="border-border bg-card hover:bg-accent/30 flex flex-col gap-2 rounded-2xl border p-4 transition-colors"
    >
      <div className="flex flex-col gap-0.5">
        <p className="text-muted-foreground text-xs">
          {lesson.classDisplayName} · {lesson.subjectName}
        </p>
        <p className="font-heading font-semibold leading-snug">{lesson.chapterName}</p>
      </div>

      <div className="flex flex-wrap gap-1">
        {badges.map((b) => (
          <span
            key={b}
            className="bg-secondary text-secondary-foreground rounded-full px-2 py-0.5 text-xs"
          >
            {b}
          </span>
        ))}
      </div>

      {lesson.note && (
        <p className="text-muted-foreground line-clamp-2 text-xs">{lesson.note}</p>
      )}

      <p className="text-muted-foreground mt-auto text-xs">
        Saved {formatDate(lesson.savedAt)}
      </p>
    </Link>
  );
}
