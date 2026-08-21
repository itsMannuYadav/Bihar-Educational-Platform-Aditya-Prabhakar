"use client";

import type { AppLanguage } from "@shiksha-sathi/shared-types";
import { Loader2, Mic, Square } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { ApiError, transcribeVoice } from "@/lib/api-client";

type RecordingState = "idle" | "recording" | "transcribing" | "error";

interface Props {
  language?: AppLanguage;
  onTranscription: (text: string) => void;
  className?: string;
}

export function VoiceInputButton({ language, onTranscription, className }: Props) {
  const [state, setState] = useState<RecordingState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const isSupported =
    typeof window !== "undefined" &&
    "MediaRecorder" in window &&
    "mediaDevices" in navigator;

  const startRecording = useCallback(async () => {
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";
      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("transcribing");
        try {
          const blob = new Blob(chunksRef.current, { type: mimeType });
          const text = await transcribeVoice(blob, language);
          onTranscription(text);
          setState("idle");
        } catch (err) {
          setErrorMsg(
            err instanceof ApiError ? err.message : "Transcription failed. Please try again.",
          );
          setState("error");
        }
      };

      recorder.start();
      recorderRef.current = recorder;
      setState("recording");
    } catch {
      setErrorMsg("Microphone access denied. Allow microphone to use voice input.");
      setState("error");
    }
  }, [language, onTranscription]);

  const stopRecording = useCallback(() => {
    recorderRef.current?.stop();
    recorderRef.current = null;
  }, []);

  if (!isSupported) return null;

  if (state === "error") {
    return (
      <div className="flex items-center gap-2">
        <p className="text-destructive text-xs">{errorMsg}</p>
        <button
          type="button"
          onClick={() => setState("idle")}
          className="text-muted-foreground text-xs underline"
        >
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      aria-label={state === "recording" ? "Stop recording" : "Start voice input"}
      disabled={state === "transcribing"}
      onClick={state === "recording" ? stopRecording : startRecording}
      className={`inline-flex size-9 items-center justify-center rounded-full transition-colors disabled:opacity-50 ${
        state === "recording"
          ? "bg-destructive text-destructive-foreground animate-pulse"
          : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
      } ${className ?? ""}`}
    >
      {state === "transcribing" ? (
        <Loader2 className="size-4 animate-spin" />
      ) : state === "recording" ? (
        <Square className="size-3.5 fill-current" />
      ) : (
        <Mic className="size-4" />
      )}
    </button>
  );
}
