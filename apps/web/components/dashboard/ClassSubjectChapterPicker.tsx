"use client";

import type {
  Chapter,
  SchoolClass,
  Subject,
} from "@shiksha-sathi/shared-types";
import { Check, ChevronsUpDown } from "lucide-react";
import { useEffect, useState } from "react";

import { buttonVariants } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { getChapters, getClasses, getSubjects } from "@/lib/api-client";

export interface ClassSubjectChapterSelection {
  schoolClass: SchoolClass | null;
  subject: Subject | null;
  chapter: Chapter | null;
}

interface PickerFieldProps<T extends { id: string }> {
  label: string;
  placeholder: string;
  items: T[];
  loading: boolean;
  disabled: boolean;
  selected: T | null;
  getLabel: (item: T) => string;
  onSelect: (item: T) => void;
}

function PickerField<T extends { id: string }>({
  label,
  placeholder,
  items,
  loading,
  disabled,
  selected,
  getLabel,
  onSelect,
}: PickerFieldProps<T>) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">{label}</span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          disabled={disabled}
          className={buttonVariants({
            variant: "outline",
            className: "justify-between font-normal",
          })}
        >
          <span className="truncate">
            {selected ? getLabel(selected) : placeholder}
          </span>
          <ChevronsUpDown className="size-4 opacity-50" />
        </PopoverTrigger>
        <PopoverContent
          className="w-(--radix-popover-trigger-width) p-0"
          align="start"
        >
          <Command>
            <CommandInput placeholder={`Search ${label.toLowerCase()}…`} />
            <CommandList>
              <CommandEmpty>
                {loading ? "Loading…" : "Nothing found."}
              </CommandEmpty>
              <CommandGroup>
                {items.map((item) => (
                  <CommandItem
                    key={item.id}
                    value={getLabel(item)}
                    onSelect={() => {
                      onSelect(item);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={`size-4 ${selected?.id === item.id ? "opacity-100" : "opacity-0"}`}
                    />
                    {getLabel(item)}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}

interface Props {
  value: ClassSubjectChapterSelection;
  onChange: (value: ClassSubjectChapterSelection) => void;
}

export function ClassSubjectChapterPicker({ value, onChange }: Props) {
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);

  useEffect(() => {
    getClasses()
      .then(setClasses)
      .catch(() => setClasses([]))
      .finally(() => setLoadingClasses(false));
  }, []);

  useEffect(() => {
    const schoolClass = value.schoolClass;
    // Deferred to a microtask so no setState call is synchronous within the
    // effect body itself (react-hooks/set-state-in-effect) — same shape as
    // the debounced fetch in app/(auth)/onboarding/page.tsx.
    queueMicrotask(() => {
      if (!schoolClass) {
        setSubjects([]);
        return;
      }
      setLoadingSubjects(true);
      getSubjects(schoolClass.id)
        .then(setSubjects)
        .catch(() => setSubjects([]))
        .finally(() => setLoadingSubjects(false));
    });
  }, [value.schoolClass]);

  useEffect(() => {
    const subject = value.subject;
    queueMicrotask(() => {
      if (!subject) {
        setChapters([]);
        return;
      }
      setLoadingChapters(true);
      getChapters(subject.id)
        .then(setChapters)
        .catch(() => setChapters([]))
        .finally(() => setLoadingChapters(false));
    });
  }, [value.subject]);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <PickerField
        label="Class"
        placeholder="Select class…"
        items={classes}
        loading={loadingClasses}
        disabled={false}
        selected={value.schoolClass}
        getLabel={(c) => c.displayName}
        onSelect={(schoolClass) =>
          onChange({ schoolClass, subject: null, chapter: null })
        }
      />
      <PickerField
        label="Subject"
        placeholder="Select subject…"
        items={subjects}
        loading={loadingSubjects}
        disabled={!value.schoolClass}
        selected={value.subject}
        getLabel={(s) => s.name}
        onSelect={(subject) => onChange({ ...value, subject, chapter: null })}
      />
      <PickerField
        label="Chapter"
        placeholder="Select chapter…"
        items={chapters}
        loading={loadingChapters}
        disabled={!value.subject}
        selected={value.chapter}
        getLabel={(c) => c.name}
        onSelect={(chapter) => onChange({ ...value, chapter })}
      />
    </div>
  );
}
