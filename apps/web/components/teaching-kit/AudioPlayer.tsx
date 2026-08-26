"use client";

import type { AudioDuration } from "@shiksha-sathi/shared-types";
import {
  Download,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  Volume2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, getAudioBlobUrl } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type LoadState = "idle" | "loading" | "ready" | "error";

interface DurationOption {
  value: AudioDuration;
  label: string;
  description: string;
}

const DURATIONS: DurationOption[] = [
  { value: "1", label: "1 min", description: "Quick summary" },
  { value: "3", label: "3 min", description: "Key concepts" },
  { value: "5", label: "5 min", description: "Full narration" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || isNaN(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// Simple CSS waveform bars — animate when playing, static otherwise
function Waveform({ playing }: { playing: boolean }) {
  const bars = [3, 5, 8, 5, 10, 7, 4, 9, 6, 11, 8, 5, 7, 4, 9];
  return (
    <div
      className="flex items-center justify-center gap-0.5"
      aria-hidden="true"
    >
      {bars.map((h, i) => (
        <span
          key={i}
          className={`bg-primary inline-block w-1 rounded-full transition-all ${
            playing ? "animate-pulse" : "opacity-30"
          }`}
          style={{
            height: `${h * 2}px`,
            animationDelay: playing ? `${i * 60}ms` : "0ms",
            animationDuration: "800ms",
          }}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface Props {
  resourceId: string;
}

export function AudioPlayer({ resourceId }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  // Blob URLs keyed by duration — stays populated so switching back doesn't re-fetch
  const blobUrls = useRef<Partial<Record<AudioDuration, string>>>({});

  const [activeDuration, setActiveDuration] = useState<AudioDuration>("3");
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [ended, setEnded] = useState(false);

  // ---------------------------------------------------------------------------
  // Load audio on demand
  // ---------------------------------------------------------------------------

  const loadAndPlay = useCallback(
    async (dur: AudioDuration, autoplay = true) => {
      setErrorMsg(null);

      // Already cached
      if (blobUrls.current[dur]) {
        const audio = audioRef.current;
        if (!audio) return;
        audio.src = blobUrls.current[dur]!;
        audio.currentTime = 0;
        setCurrentTime(0);
        setEnded(false);
        setLoadState("ready");
        if (autoplay) {
          await audio.play().catch(() => {/* autoplay blocked — teacher will tap play */});
        }
        return;
      }

      setLoadState("loading");
      try {
        const url = await getAudioBlobUrl(resourceId, dur);
        blobUrls.current[dur] = url;
        const audio = audioRef.current;
        if (!audio) return;
        audio.src = url;
        audio.currentTime = 0;
        setCurrentTime(0);
        setEnded(false);
        setLoadState("ready");
        if (autoplay) {
          await audio.play().catch(() => {/* autoplay blocked */});
        }
      } catch (err) {
        setErrorMsg(
          err instanceof ApiError ? err.message : "Audio unavailable. Please try again.",
        );
        setLoadState("error");
      }
    },
    [resourceId],
  );

  // Switch duration
  async function handleSelectDuration(dur: AudioDuration) {
    if (dur === activeDuration && loadState === "ready") return;
    const wasPlaying = playing;
    const audio = audioRef.current;
    if (audio && wasPlaying) audio.pause();
    setPlaying(false);
    setActiveDuration(dur);
    await loadAndPlay(dur, wasPlaying);
  }

  // Play / pause / replay
  async function handlePlayPause() {
    const audio = audioRef.current;
    if (!audio) return;

    if (loadState === "idle") {
      await loadAndPlay(activeDuration, true);
      return;
    }
    if (loadState === "loading") return;
    if (loadState === "error") {
      await loadAndPlay(activeDuration, true);
      return;
    }

    if (ended) {
      audio.currentTime = 0;
      setEnded(false);
      await audio.play();
    } else if (playing) {
      audio.pause();
    } else {
      await audio.play();
    }
  }

  // Seek
  function handleSeek(e: React.ChangeEvent<HTMLInputElement>) {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    const t = (Number(e.target.value) / 100) * duration;
    audio.currentTime = t;
    setCurrentTime(t);
    setEnded(false);
  }

  // Download
  async function handleDownload() {
    const dur = activeDuration;
    if (!blobUrls.current[dur] && loadState !== "ready") {
      await loadAndPlay(dur, false);
    }
    const url = blobUrls.current[dur];
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `narration-${dur}min.mp3`;
    a.click();
  }

  // ---------------------------------------------------------------------------
  // Audio element event wiring
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onDurationChange = () => setDuration(audio.duration);
    const onEnded = () => { setPlaying(false); setEnded(true); };

    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("durationchange", onDurationChange);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("durationchange", onDurationChange);
      audio.removeEventListener("ended", onEnded);
    };
  }, []);

  // Revoke blob URLs on unmount
  useEffect(() => {
    const urls = blobUrls.current;
    return () => {
      Object.values(urls).forEach((u) => u && URL.revokeObjectURL(u));
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Derived UI state
  // ---------------------------------------------------------------------------

  const progressPct = duration > 0 ? (currentTime / duration) * 100 : 0;
  const isLoading = loadState === "loading";

  const PlayIcon = ended ? RotateCcw : playing ? Pause : Play;

  return (
    <div className="border-border bg-card flex flex-col gap-6 rounded-2xl border p-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Volume2 className="text-primary size-5" />
        <h3 className="font-heading text-base font-semibold">Audio Narration</h3>
      </div>

      {/* Duration selector */}
      <div className="flex gap-2">
        {DURATIONS.map((d) => (
          <button
            key={d.value}
            type="button"
            disabled={isLoading}
            onClick={() => handleSelectDuration(d.value)}
            className={`flex flex-1 flex-col items-center gap-0.5 rounded-xl border px-3 py-2.5 text-center transition-all disabled:opacity-50 ${
              activeDuration === d.value
                ? "border-primary bg-primary/5 text-primary"
                : "border-border text-muted-foreground hover:border-primary/40 hover:text-foreground"
            }`}
          >
            <span className="text-sm font-semibold">{d.label}</span>
            <span className="text-xs opacity-70">{d.description}</span>
          </button>
        ))}
      </div>

      {/* Waveform */}
      <div className="flex h-12 items-center justify-center">
        {isLoading ? (
          <div className="text-muted-foreground flex items-center gap-2 text-sm">
            <Loader2 className="size-4 animate-spin" />
            Generating audio…
          </div>
        ) : (
          <Waveform playing={playing} />
        )}
      </div>

      {/* Progress bar */}
      <div className="flex flex-col gap-1.5">
        <input
          type="range"
          min={0}
          max={100}
          value={progressPct}
          onChange={handleSeek}
          disabled={loadState !== "ready" || duration === 0}
          aria-label="Audio progress"
          className="accent-primary h-1.5 w-full cursor-pointer disabled:cursor-default disabled:opacity-40"
        />
        <div className="text-muted-foreground flex justify-between text-xs tabular-nums">
          <span>{formatTime(currentTime)}</span>
          <span>{duration > 0 ? formatTime(duration) : `~${activeDuration}:00`}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={handlePlayPause}
          disabled={isLoading}
          aria-label={playing ? "Pause" : ended ? "Replay" : "Play"}
          className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex size-14 items-center justify-center rounded-full shadow-md transition-all active:scale-95 disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2 className="size-6 animate-spin" />
          ) : (
            <PlayIcon className="size-6" />
          )}
        </button>
      </div>

      {/* Error */}
      {loadState === "error" && (
        <p className="text-destructive text-center text-sm">{errorMsg}</p>
      )}

      {/* Download */}
      {loadState === "ready" && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleDownload}
            className="text-muted-foreground hover:text-foreground flex items-center gap-1.5 text-xs font-medium"
          >
            <Download className="size-3.5" />
            Download MP3
          </button>
        </div>
      )}

      {/* Hidden audio element */}
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={audioRef} preload="none" />
    </div>
  );
}
