import Link from "next/link";
import { BrandMark } from "@/components/common/brand-mark";

const FEATURES = [
  {
    icon: "📚",
    hi: "पाठ योजना",
    en: "Lesson Plans",
    desc: "BSEB-aligned lesson plans generated in seconds",
  },
  {
    icon: "🎙️",
    hi: "आवाज़ इनपुट",
    en: "Voice Input",
    desc: "Speak in Hindi or Hinglish — no typing needed",
  },
  {
    icon: "🗺️",
    hi: "मन-मैप",
    en: "Mind Maps",
    desc: "Interactive visual maps for every chapter",
  },
  {
    icon: "📝",
    hi: "वर्कशीट",
    en: "Worksheets",
    desc: "Printable worksheets with MCQs and answers",
  },
  {
    icon: "🎧",
    hi: "ऑडियो पाठ",
    en: "Audio Lessons",
    desc: "1, 3 and 5-minute spoken explanations",
  },
  {
    icon: "📊",
    hi: "प्रेज़ेंटेशन",
    en: "Presentations",
    desc: "Ready-to-use PPTX slides, 5 / 10 / 15 slides",
  },
] as const;

const STATS = [
  { value: "5", label: "कक्षाएं\nClasses 6–10" },
  { value: "5", label: "विषय\nCore Subjects" },
  { value: "6", label: "संसाधन\nKit Resources" },
  { value: "AI", label: "संचालित\nPowered" },
] as const;

export default function LandingPage() {
  return (
    <div className="flex min-h-full flex-col">
      {/* ── Nav ── */}
      <header className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3">
          <div className="flex items-center gap-2.5">
            <BrandMark size="sm" />
            <span className="font-heading text-lg font-bold">
              Shiksha <span className="text-primary">Sathi</span>
            </span>
          </div>
          <Link
            href="/login"
            className="bg-primary text-primary-foreground rounded-full px-5 py-2 text-sm font-semibold transition-opacity hover:opacity-90"
          >
            Sign in
          </Link>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="mx-auto flex w-full max-w-5xl flex-col items-center gap-6 px-5 py-20 text-center">
        <div className="bg-primary/10 text-primary rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-widest">
          Bihar State Education Board · BSEB
        </div>

        <h1 className="font-heading text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl">
          <span className="text-primary">शिक्षा सारथी</span>
          <br />
          <span className="text-foreground">Shiksha Sathi</span>
        </h1>

        <p className="max-w-xl text-lg text-muted-foreground">
          बिहार के सरकारी स्कूल शिक्षकों के लिए AI शिक्षण सहायक
          <br />
          <span className="text-sm">
            AI Teaching Companion for Bihar Government School Teachers
          </span>
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/login"
            className="bg-primary text-primary-foreground rounded-full px-8 py-3 text-base font-semibold shadow-lg transition-opacity hover:opacity-90"
          >
            अभी शुरू करें · Get Started
          </Link>
          <a
            href="#features"
            className="border-border rounded-full border px-8 py-3 text-base font-semibold text-muted-foreground transition-colors hover:text-foreground"
          >
            और जानें · Learn More
          </a>
        </div>
      </section>

      {/* ── Stats strip ── */}
      <section className="bg-primary/5 border-y border-border py-10">
        <div className="mx-auto grid max-w-3xl grid-cols-4 divide-x divide-border">
          {STATS.map(({ value, label }) => (
            <div key={value + label} className="flex flex-col items-center gap-1 px-4 text-center">
              <span className="font-heading text-3xl font-extrabold text-primary">{value}</span>
              <span className="whitespace-pre-line text-xs text-muted-foreground leading-snug">{label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="mx-auto w-full max-w-5xl px-5 py-20">
        <div className="mb-12 text-center">
          <h2 className="font-heading text-3xl font-bold">
            एक बटन से पूरा पाठ किट
          </h2>
          <p className="mt-2 text-muted-foreground">
            Complete Teaching Kit with One Click
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon, hi, en, desc }) => (
            <div
              key={en}
              className="border-border bg-card rounded-2xl border p-6 transition-shadow hover:shadow-md"
            >
              <div className="mb-4 text-3xl">{icon}</div>
              <h3 className="font-heading text-lg font-bold">
                {hi} <span className="text-muted-foreground font-normal text-base">· {en}</span>
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="bg-muted/50 border-y border-border py-20">
        <div className="mx-auto max-w-4xl px-5 text-center">
          <h2 className="font-heading text-3xl font-bold mb-2">कैसे काम करता है?</h2>
          <p className="text-muted-foreground mb-12">How it works — 3 simple steps</p>

          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            {[
              { step: "1", hi: "कक्षा चुनें", en: "Pick your class, subject & chapter" },
              { step: "2", hi: "AI बनाए", en: "AI streams 6 resources in parallel" },
              { step: "3", hi: "पढ़ाएं!", en: "Download, print & teach" },
            ].map(({ step, hi, en }) => (
              <div key={step} className="flex flex-col items-center gap-3">
                <div className="bg-primary text-primary-foreground flex size-12 items-center justify-center rounded-full font-heading text-xl font-bold">
                  {step}
                </div>
                <p className="font-heading text-lg font-bold">{hi}</p>
                <p className="text-sm text-muted-foreground">{en}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="mx-auto w-full max-w-xl px-5 py-20 text-center">
        <h2 className="font-heading text-2xl font-bold mb-3">
          बिहार के शिक्षकों के लिए बना है
        </h2>
        <p className="text-muted-foreground mb-8 text-sm">
          Built for Bihar's 4 lakh+ government school teachers · BSEB curriculum · Hindi &amp; Hinglish support
        </p>
        <Link
          href="/login"
          className="bg-primary text-primary-foreground rounded-full px-10 py-4 text-lg font-semibold shadow-xl transition-opacity hover:opacity-90"
        >
          निःशुल्क शुरू करें · Start for Free
        </Link>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-border bg-card px-5 py-8 text-center text-xs text-muted-foreground">
        <p className="font-semibold text-sm mb-1">
          Shiksha Sathi · शिक्षा सारथी
        </p>
        <p>Bihar State Education Board (BSEB) · Government School Initiative</p>
        <p className="mt-2 opacity-60">
          Built with ❤️ for Bihar's teachers · Class 6–10 · Science, Math, Hindi, English, Social Science
        </p>
      </footer>
    </div>
  );
}
