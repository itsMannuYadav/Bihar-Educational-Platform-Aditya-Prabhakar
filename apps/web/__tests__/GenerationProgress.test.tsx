import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GenerationProgress } from "@/components/teaching-kit/GenerationProgress";
import type { TeachingKitStreamState } from "@/hooks/useTeachingKitStream";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeStream(
  overrides: Partial<TeachingKitStreamState> = {},
): TeachingKitStreamState {
  return {
    status: "generating",
    resources: {},
    errorDetail: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("GenerationProgress", () => {
  it("renders a spinner for each pending resource", () => {
    const stream = makeStream({
      resources: {
        lesson_plan: { status: "pending" },
        questions: { status: "pending" },
      },
    });

    render(
      <GenerationProgress
        resourceTypes={["lesson_plan", "questions"]}
        stream={stream}
      />,
    );

    // Labels present
    expect(screen.getByText("Lesson Plan")).toBeInTheDocument();
    expect(screen.getByText("Questions")).toBeInTheDocument();

    // No check icons — still pending
    expect(screen.queryByRole("img", { hidden: true })).toBeNull();
  });

  it("shows a check icon and no spinner when a resource is ready", () => {
    const stream = makeStream({
      status: "complete",
      resources: {
        lesson_plan: { status: "ready", cacheHit: false },
      },
    });

    render(
      <GenerationProgress resourceTypes={["lesson_plan"]} stream={stream} />,
    );

    // The Check icon from lucide is an svg, but we verify the label is there
    expect(screen.getByText("Lesson Plan")).toBeInTheDocument();
    // The "From library" subtitle must NOT appear when cacheHit is false
    expect(screen.queryByText("From library")).toBeNull();
  });

  it("shows 'From library' subtitle when the resource is a cache hit", () => {
    const stream = makeStream({
      status: "complete",
      resources: {
        questions: { status: "ready", cacheHit: true },
      },
    });

    render(
      <GenerationProgress resourceTypes={["questions"]} stream={stream} />,
    );

    expect(screen.getByText("From library")).toBeInTheDocument();
  });

  it("shows a daily-limit message for RATE_LIMIT_DAILY", () => {
    const stream = makeStream({
      status: "failed",
      errorDetail: "RATE_LIMIT_DAILY",
    });

    render(
      <GenerationProgress resourceTypes={["lesson_plan"]} stream={stream} />,
    );

    expect(screen.getByText(/daily.*quota|quota.*daily/i)).toBeInTheDocument();
  });

  it("shows a minute-limit message for RATE_LIMIT_MINUTE", () => {
    const stream = makeStream({
      status: "failed",
      errorDetail: "RATE_LIMIT_MINUTE",
    });

    render(
      <GenerationProgress resourceTypes={["lesson_plan"]} stream={stream} />,
    );

    expect(screen.getByText(/busy right now/i)).toBeInTheDocument();
  });

  it("shows a fallback error message for unknown errorDetail", () => {
    const stream = makeStream({
      status: "failed",
      errorDetail: "Generation timed out.",
    });

    render(
      <GenerationProgress resourceTypes={["lesson_plan"]} stream={stream} />,
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("shows a fallback error message when errorDetail is null and status is failed", () => {
    const stream = makeStream({ status: "failed", errorDetail: null });

    render(
      <GenerationProgress resourceTypes={["worksheet"]} stream={stream} />,
    );

    expect(
      screen.getByText(/something went wrong/i),
    ).toBeInTheDocument();
  });

  it("renders all 7 resource type labels when all are present", () => {
    const allTypes = [
      "lesson_plan",
      "teaching_script",
      "questions",
      "worksheet",
      "presentation",
      "mind_map",
      "audio",
    ] as const;

    const resources = Object.fromEntries(
      allTypes.map((t) => [t, { status: "pending" as const }]),
    );

    const stream = makeStream({ resources });

    render(
      <GenerationProgress resourceTypes={[...allTypes]} stream={stream} />,
    );

    expect(screen.getByText("Lesson Plan")).toBeInTheDocument();
    expect(screen.getByText("Teaching Script")).toBeInTheDocument();
    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText("Worksheet")).toBeInTheDocument();
    expect(screen.getByText("Presentation")).toBeInTheDocument();
    expect(screen.getByText("Mind Map")).toBeInTheDocument();
    expect(screen.getByText("Audio")).toBeInTheDocument();
  });
});
