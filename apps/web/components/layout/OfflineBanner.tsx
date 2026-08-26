"use client";

import { WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

export function OfflineBanner() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    setOffline(!navigator.onLine);
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-2 bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow-md"
    >
      <WifiOff className="size-4 shrink-0" aria-hidden="true" />
      <span>
        इंटरनेट नहीं है — कुछ सुविधाएं उपलब्ध नहीं हो सकती हैं
        <span className="mx-2 opacity-70">·</span>
        You are offline — some features may be unavailable
      </span>
    </div>
  );
}
