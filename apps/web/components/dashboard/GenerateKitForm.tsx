"use client";

import type {
  AppLanguage,
  DurationOption,
  TeachingMode,
} from "@shiksha-sathi/shared-types";
import { MVP_RESOURCE_TYPES } from "@shiksha-sathi/shared-types";
import { type FormEvent, useState } from "react";

import {
  ClassSubjectChapterPicker,
  type ClassSubjectChapterSelection,
} from "@/components/dashboard/ClassSubjectChapterPicker";
import { GenerationOptionsBar } from "@/components/dashboard/GenerationOptionsBar";
import { GenerationProgress } from "@/components/teaching-kit/GenerationProgress";
import { Button } from "@/components/ui/button";
import { useTeachingKitStream } from "@/hooks/useTeachingKitStream";
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
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  const stream = useTeachingKitStream(streamUrl, MVP_RESOURCE_TYPES);
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
      setStreamUrl(summary.streamUrl);
    } catch {
      setError("Couldn't start generation. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-border bg-card flex w-full max-w-2xl flex-col gap-5 rounded-2xl border p-5"
    >
      <ClassSubjectChapterPicker value={selection} onChange={setSelection} />

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

      <Button
        type="submit"
        disabled={!canGenerate || submitting || streamUrl !== null}
      >
        {submitting ? "Starting…" : "Generate Teaching Kit"}
      </Button>

      {streamUrl && (
        <>
          <GenerationProgress
            resourceTypes={MVP_RESOURCE_TYPES}
            stream={stream}
          />
          {stream.status === "complete" && (
            <button
              type="button"
              onClick={() => {
                setStreamUrl(null);
                setSelection(EMPTY_SELECTION);
              }}
              className="text-primary self-start text-sm font-medium underline-offset-4 hover:underline"
            >
              Generate another kit
            </button>
          )}
        </>
      )}
    </form>
  );
}
