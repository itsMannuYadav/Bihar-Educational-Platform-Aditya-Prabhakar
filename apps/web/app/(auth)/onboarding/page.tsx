"use client";

import type { AppLanguage, School } from "@shiksha-sathi/shared-types";
import { Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { BrandMark } from "@/components/common/brand-mark";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { createMe, getMe, searchSchools } from "@/lib/api-client";

const LANGUAGES: { value: AppLanguage; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिंदी" },
  { value: "hinglish", label: "Hinglish" },
];

export default function OnboardingPage() {
  const router = useRouter();

  const [checkingProfile, setCheckingProfile] = useState(true);
  const [name, setName] = useState("");
  const [schoolQuery, setSchoolQuery] = useState("");
  const [schoolResults, setSchoolResults] = useState<School[]>([]);
  const [selectedSchool, setSelectedSchool] = useState<School | null>(null);
  const [schoolPickerOpen, setSchoolPickerOpen] = useState(false);
  const [language, setLanguage] = useState<AppLanguage>("hi");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then((profile) => {
        if (profile) router.replace("/dashboard");
        else setCheckingProfile(false);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  useEffect(() => {
    if (!schoolPickerOpen) return;
    const timer = setTimeout(() => {
      searchSchools(schoolQuery).then(setSchoolResults).catch(() => setSchoolResults([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [schoolQuery, schoolPickerOpen]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Enter your name.");
      return;
    }

    setSubmitting(true);
    try {
      await createMe({
        name: name.trim(),
        schoolId: selectedSchool?.id,
        preferredLanguage: language,
      });
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (checkingProfile) {
    return <main className="flex flex-1 items-center justify-center" />;
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="flex w-full max-w-sm flex-col items-center gap-6">
        <div className="flex flex-col items-center gap-3 text-center">
          <BrandMark />
          <h1 className="font-heading text-2xl font-bold tracking-tight">Welcome, teacher</h1>
          <p className="text-muted-foreground text-sm">
            A few details, then you&apos;re ready to teach.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-border bg-card flex w-full flex-col gap-5 rounded-2xl border p-5"
        >
          <div className="flex flex-col gap-1.5">
            <label htmlFor="name" className="text-sm font-medium">
              Your name
            </label>
            <Input
              id="name"
              placeholder="Anita Kumari"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">School</span>
            <Popover open={schoolPickerOpen} onOpenChange={setSchoolPickerOpen}>
              <PopoverTrigger
                className={buttonVariants({
                  variant: "outline",
                  className: "justify-start font-normal",
                })}
              >
                {selectedSchool ? selectedSchool.name : "Search for your school…"}
              </PopoverTrigger>
              <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
                <Command shouldFilter={false}>
                  <CommandInput
                    placeholder="Type your school's name…"
                    value={schoolQuery}
                    onValueChange={setSchoolQuery}
                  />
                  <CommandList>
                    <CommandEmpty>No school found — you can add this later.</CommandEmpty>
                    <CommandGroup>
                      {schoolResults.map((school) => (
                        <CommandItem
                          key={school.id}
                          value={school.id}
                          onSelect={() => {
                            setSelectedSchool(school);
                            setSchoolPickerOpen(false);
                          }}
                        >
                          <Check
                            className={`size-4 ${selectedSchool?.id === school.id ? "opacity-100" : "opacity-0"}`}
                          />
                          <div className="flex flex-col">
                            <span>{school.name}</span>
                            {school.district && (
                              <span className="text-muted-foreground text-xs">
                                {school.district}
                              </span>
                            )}
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Preferred language</span>
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

          {error && <p className="text-destructive text-sm">{error}</p>}

          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? "Setting up…" : "Start teaching"}
          </Button>
        </form>
      </div>
    </main>
  );
}
