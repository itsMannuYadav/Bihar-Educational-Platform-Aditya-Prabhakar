"use client";

import type {
  PresentationContent,
  PresentationVersion,
} from "@shiksha-sathi/shared-types";
import { PRESENTATION_VERSIONS } from "@shiksha-sathi/shared-types";
import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { downloadPresentation } from "@/lib/api-client";

interface Props {
  resourceId: string;
  content: PresentationContent;
  chapterName: string;
}

export function PptViewer({ resourceId, content, chapterName }: Props) {
  const [version, setVersion] = useState<PresentationVersion>("10");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const slides = content.versions[version] ?? [];

  async function handleDownload() {
    setDownloading(true);
    setError(null);
    try {
      await downloadPresentation(
        resourceId,
        version,
        `${chapterName}-${version}-slides.pptx`,
      );
    } catch {
      setError("Couldn't download the deck. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="bg-secondary flex gap-1 rounded-full p-1">
          {PRESENTATION_VERSIONS.map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setVersion(v)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                version === v
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground"
              }`}
            >
              {v} slides
            </button>
          ))}
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={handleDownload}
          disabled={downloading}
        >
          {downloading ? <Loader2 className="animate-spin" /> : <Download />}
          {downloading ? "Preparing…" : "Download .pptx"}
        </Button>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {slides.map((slide, i) => (
          <figure
            key={i}
            className="border-border bg-card flex flex-col overflow-hidden rounded-xl border"
          >
            {/* 16:9, matching what the .pptx renderer produces, so the preview
                isn't a different shape from the file the teacher downloads. */}
            <div className="flex aspect-video flex-col gap-2 p-4">
              <div className="flex items-baseline justify-between gap-2">
                <h4
                  className={`font-heading font-bold ${
                    slide.layout === "title" ? "text-lg" : "text-sm"
                  }`}
                >
                  {slide.title}
                </h4>
                <span className="text-muted-foreground shrink-0 text-[10px]">
                  {i + 1}
                </span>
              </div>
              <ul className="flex flex-col gap-1 text-xs leading-relaxed">
                {slide.body.map((line, li) => (
                  <li key={li} className="flex gap-1.5">
                    <span className="text-primary">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </div>
            {slide.speaker_notes && (
              <figcaption className="bg-muted/60 text-muted-foreground border-border border-t px-4 py-2 text-[11px] leading-snug">
                <span className="font-semibold">Say: </span>
                {slide.speaker_notes}
              </figcaption>
            )}
          </figure>
        ))}
      </div>
    </div>
  );
}
