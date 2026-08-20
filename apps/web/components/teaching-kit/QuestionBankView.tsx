"use client";

import type {
  QuestionDifficulty,
  QuestionItem,
  QuestionSetContent,
} from "@shiksha-sathi/shared-types";
import { Check, Eye, EyeOff } from "lucide-react";
import { useState } from "react";

const DIFFICULTIES: (QuestionDifficulty | "all")[] = [
  "all",
  "easy",
  "moderate",
  "advanced",
];

const TYPE_LABEL: Record<QuestionItem["type"], string> = {
  mcq: "MCQ",
  short_answer: "Short answer",
  long_answer: "Long answer",
  hots: "HOTS",
};

interface Props {
  content: QuestionSetContent;
}

export function QuestionBankView({ content }: Props) {
  const [difficulty, setDifficulty] = useState<QuestionDifficulty | "all">(
    "all",
  );
  // Answers hidden by default: a teacher often projects this straight onto the
  // board, and revealing the answer key to the class defeats the purpose.
  const [showAnswers, setShowAnswers] = useState(false);

  const questions = content.questions.filter(
    (q) => difficulty === "all" || q.difficulty === difficulty,
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="bg-secondary flex gap-1 rounded-full p-1">
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDifficulty(d)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition-colors ${
                difficulty === d
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground"
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => setShowAnswers((v) => !v)}
          className="text-muted-foreground hover:text-foreground flex items-center gap-1.5 text-sm font-medium"
        >
          {showAnswers ? (
            <EyeOff className="size-4" />
          ) : (
            <Eye className="size-4" />
          )}
          {showAnswers ? "Hide answers" : "Show answers"}
        </button>
      </div>

      {questions.length === 0 && (
        <p className="text-muted-foreground py-6 text-center text-sm">
          No {difficulty} questions in this set.
        </p>
      )}

      <ol className="flex flex-col gap-4">
        {questions.map((q, i) => (
          <li
            key={i}
            className="border-border flex flex-col gap-2 rounded-xl border p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="bg-secondary rounded-full px-2 py-0.5 text-xs font-semibold">
                {TYPE_LABEL[q.type]}
              </span>
              <span className="text-muted-foreground text-xs capitalize">
                {q.difficulty}
              </span>
            </div>

            <p className="text-sm font-medium">
              {i + 1}. {q.question_text}
            </p>

            {q.options && (
              <ul className="flex flex-col gap-1 pl-1">
                {q.options.map((opt, oi) => (
                  <li
                    key={oi}
                    className={`flex items-center gap-2 text-sm ${
                      showAnswers && opt.is_correct
                        ? "text-accent-foreground font-semibold"
                        : ""
                    }`}
                  >
                    <span className="text-muted-foreground w-5 shrink-0">
                      {opt.label}.
                    </span>
                    <span>{opt.text}</span>
                    {showAnswers && opt.is_correct && (
                      <Check className="size-4 shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
            )}

            {showAnswers && (
              <div className="bg-muted/60 flex flex-col gap-1 rounded-lg p-3 text-sm">
                <p>
                  <span className="font-semibold">Answer: </span>
                  {q.answer}
                </p>
                {q.explanation && (
                  <p className="text-muted-foreground text-xs">
                    {q.explanation}
                  </p>
                )}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
