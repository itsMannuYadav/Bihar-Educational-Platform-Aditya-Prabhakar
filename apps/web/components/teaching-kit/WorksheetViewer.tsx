"use client";

import type {
  WorksheetContent,
  WorksheetSection,
} from "@shiksha-sathi/shared-types";
import { KeyRound, Printer } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

const SECTION_TITLE: Record<WorksheetSection["type"], string> = {
  fill_blank: "Fill in the blanks",
  true_false: "True or False",
  match: "Match the following",
};

/** Deterministic derangement of `0..n-1`, used to shuffle the right-hand column
 * of a matching exercise so row `j` never already sits opposite its own answer.
 *
 * Seeded rather than random: the printed sheet and the answer key have to agree,
 * and a re-render must not reshuffle under a teacher who is mid-print. A plain
 * `j + 1` rotation is also fixed-point-free but shifts every row by the same
 * amount, so a student who works out one pair immediately has all of them —
 * hence a real shuffle, with a fixup pass for any index the shuffle left in
 * place. (At n = 2 and n = 3 every derangement is a rotation; nothing to do.)
 */
function shuffledIndices(n: number): number[] {
  const order = Array.from({ length: n }, (_, j) => j);
  if (n < 2) return order;

  let seed = (n * 2654435761) >>> 0;
  const next = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(next() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  // A single forward pass suffices: when order[i] === i, order[k] cannot also
  // be i, so the swap clears the fixed point without creating another.
  for (let i = 0; i < n; i++) {
    if (order[i] === i) {
      const k = (i + 1) % n;
      [order[i], order[k]] = [order[k], order[i]];
    }
  }
  return order;
}

interface Props {
  content: WorksheetContent;
  chapterName: string;
}

/** Printing goes through the browser rather than a server-rendered PDF.
 * ReportLab and its peers have no Indic shaping engine, so a server-made Hindi
 * worksheet comes out with its matras in the wrong order; the browser shapes
 * Devanagari correctly and "Save as PDF" already lives in its print dialog.
 * The print stylesheet in globals.css hides everything except the sheet — the
 * answer key included, so a teacher can print while it is on screen. */
export function WorksheetViewer({ content, chapterName }: Props) {
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap justify-end gap-2 print:hidden">
        <Button
          type="button"
          variant="ghost"
          onClick={() => setShowKey((v) => !v)}
        >
          <KeyRound />
          {showKey ? "Hide answer key" : "Answer key"}
        </Button>
        <Button type="button" variant="outline" onClick={() => window.print()}>
          <Printer />
          Print / Save as PDF
        </Button>
      </div>

      <div
        data-print-region="worksheet"
        className="border-border flex flex-col gap-6 rounded-xl border p-5 print:rounded-none print:border-0 print:p-0"
      >
        <header className="border-border flex flex-col gap-1 border-b pb-3">
          <h2 className="font-heading text-lg font-bold">{chapterName}</h2>
          <div className="text-muted-foreground flex flex-wrap gap-6 text-xs">
            <span>Name: ____________________</span>
            <span>Class: __________</span>
            <span>Date: __________</span>
          </div>
        </header>

        {content.sections.map((section, i) => {
          const order = shuffledIndices(section.match_items.length);
          return (
            <section key={i} className="flex flex-col gap-2">
              <h3 className="text-sm font-bold">
                {i + 1}. {SECTION_TITLE[section.type]}
              </h3>

              {section.type === "fill_blank" && (
                <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm">
                  {section.fill_blank_items.map((item, j) => (
                    <li key={j}>{item.text}</li>
                  ))}
                </ol>
              )}

              {section.type === "true_false" && (
                <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm">
                  {section.true_false_items.map((item, j) => (
                    <li key={j} className="flex justify-between gap-4">
                      <span>{item.statement}</span>
                      <span className="text-muted-foreground shrink-0">
                        T / F
                      </span>
                    </li>
                  ))}
                </ol>
              )}

              {section.type === "match" && (
                <table className="w-full text-sm">
                  <tbody>
                    {section.match_items.map((item, j) => (
                      <tr
                        key={j}
                        className="border-border border-b last:border-0"
                      >
                        <td className="w-8 py-1.5 align-top">
                          {String.fromCharCode(97 + j)}.
                        </td>
                        <td className="py-1.5 align-top">{item.left}</td>
                        <td className="text-muted-foreground w-10 py-1.5 text-center align-top">
                          ___
                        </td>
                        <td className="py-1.5 align-top">
                          {section.match_items[order[j]].right}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          );
        })}
      </div>

      {showKey && (
        <div className="border-border bg-muted/40 flex flex-col gap-4 rounded-xl border p-5 print:hidden">
          <h3 className="text-sm font-bold">Answer key</h3>
          {content.sections.map((section, i) => (
            <section key={i} className="flex flex-col gap-1">
              <h4 className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                {SECTION_TITLE[section.type]}
              </h4>
              <ol className="flex list-decimal flex-col gap-1 pl-5 text-sm">
                {section.type === "fill_blank" &&
                  section.fill_blank_items.map((item, j) => (
                    <li key={j}>{item.answer}</li>
                  ))}
                {section.type === "true_false" &&
                  section.true_false_items.map((item, j) => (
                    <li key={j}>{item.is_true ? "True" : "False"}</li>
                  ))}
                {section.type === "match" &&
                  section.match_items.map((item, j) => (
                    <li key={j}>
                      {item.left} → {item.right}
                    </li>
                  ))}
              </ol>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
