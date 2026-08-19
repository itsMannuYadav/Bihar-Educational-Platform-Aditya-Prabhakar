"use client";

import type { DurationOption, TeachingMode } from "@shiksha-sathi/shared-types";

const DURATIONS: { value: DurationOption; label: string }[] = [
  { value: "30", label: "30 min" },
  { value: "40", label: "40 min" },
  { value: "60", label: "60 min" },
];

const TEACHING_MODES: { value: TeachingMode; label: string }[] = [
  { value: "concept", label: "Concept" },
  { value: "story", label: "Story" },
  { value: "activity", label: "Activity" },
  { value: "exam", label: "Exam" },
  { value: "quick_revision", label: "Quick revision" },
];

interface PillGroupProps<T extends string> {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}

function PillGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: PillGroupProps<T>) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">{label}</span>
      <div className="bg-secondary flex flex-wrap gap-1 rounded-full p-1">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`flex-1 rounded-full px-3 py-2 text-sm font-semibold whitespace-nowrap transition-colors ${
              value === opt.value
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

interface Props {
  duration: DurationOption;
  onDurationChange: (value: DurationOption) => void;
  teachingMode: TeachingMode;
  onTeachingModeChange: (value: TeachingMode) => void;
}

export function GenerationOptionsBar({
  duration,
  onDurationChange,
  teachingMode,
  onTeachingModeChange,
}: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <PillGroup
        label="Class duration"
        options={DURATIONS}
        value={duration}
        onChange={onDurationChange}
      />
      <PillGroup
        label="Teaching style"
        options={TEACHING_MODES}
        value={teachingMode}
        onChange={onTeachingModeChange}
      />
    </div>
  );
}
