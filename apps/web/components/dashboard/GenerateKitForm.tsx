"use client";

import type {
  AppLanguage,
  DurationOption,
  TeachingMode,
} from "@shiksha-sathi/shared-types";
import { MVP_RESOURCE_TYPES } from "@shiksha-sathi/shared-types";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import {
  ClassSubjectChapterPicker,
  type ClassSubjectChapterSelection,
} from "@/components/dashboard/ClassSubjectChapterPicker";
import { GenerationOptionsBar } from "@/components/dashboard/GenerationOptionsBar";
import { VoiceInputButton } from "@/components/dashboard/VoiceInputButton";
import { Button } from "@/components/ui/button";
import { generateTeachingKit } from "@/lib/api-client";

const LANGUAGES: { value: AppLanguage; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिंदी" },
  { value: "hinglish", label: "Hinglish" },
];

const EMPTY_SELECTION: ClassSubjectChapterSelection = {
  schoolClass: null,
  subject: null,
  chapter: null,
};

interface Props {
  defaultLanguage: AppLanguage;
}

export function GenerateKitForm({ defaultLanguage }: Props) {
  const [selection, setSelection] =
    useState<ClassSubjectChapterSelection>(EMPTY_SELECTION);
  const [language, setLanguage] = useState<AppLanguage>(defaultLanguage);
  const [duration, setDuration] = useState<DurationOption>("40");
  const [teachingMode, setTeachingMode] = useState<TeachingMode>("concept");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chapterHint, setChapterHint] = useState<
    { text: string; key: number } | undefined
  >();
  const router = useRouter();

  const canGenerate = Boolean(
    selection.schoolClass && selection.subject && selection.chapter,
  );

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selection.schoolClass || !selection.subject || !selection.chapter)
      return;

    setSubmitting(true);
    setError(null);
    try {
      const summary = await generateTeachingKit({
        classId: selection.schoolClass.id,
        subjectId: selection.subject.id,
        chapterId: selection.chapter.id,
        language,
        duration,
        teachingMode,
        resourceTypes: MVP_RESOURCE_TYPES,
      });
      // Deliberately no setSubmitting(false) on success: the button stays
      // disabled through the navigation, so a double tap on a slow connection
      // can't create a second request.
      router.push(`/teaching-kit/${summary.requestId}`);
    } catch {
      setError("Couldn't start generation. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-border bg-card flex w-full max-w-2xl flex-col gap-5 rounded-2xl border p-5"
    >
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground text-xs">
          Speak a chapter name to search faster
        </span>
        <VoiceInputButton
          language={language}
          onTranscription={(text) =>
            setChapterHint((prev) => ({ text, key: (prev?.key ?? 0) + 1 }))
          }
        />
      </div>

      <ClassSubjectChapterPicker
        value={selection}
        onChange={(s) => {
          setSelection(s);
          if (s.chapter) setChapterHint(undefined);
        }}
        chapterHint={chapterHint}
      />

      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">Language</span>
        <div className="bg-secondary flex gap-1 rounded-full p-1">
          {LANGUAGES.map((l) => (
            <button
              key={l.value}
              type="button"
              onClick={() => setLanguage(l.value)}
              className={`flex-1 rounded-full py-2 text-sm font-semibold transition-colors ${
                language === l.value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <GenerationOptionsBar
        duration={duration}
        onDurationChange={setDuration}
        teachingMode={teachingMode}
        onTeachingModeChange={setTeachingMode}
      />

      {error && <p className="text-destructive text-sm">{error}</p>}

      <Button type="submit" disabled={!canGenerate || submitting}>
        {submitting ? "Starting…" : "Generate Teaching Kit"}
      </Button>
    </form>
  );
}
