import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ResourceTabs } from "@/components/teaching-kit/ResourceTabs";
import type { GeneratedResource } from "@shiksha-sathi/shared-types";

// ---------------------------------------------------------------------------
// Mock sub-renderers so tests stay fast and isolated
// ---------------------------------------------------------------------------

vi.mock("@/components/teaching-kit/LessonPlanView", () => ({
  LessonPlanView: () => <div data-testid="lesson-plan-view">LessonPlan</div>,
}));
vi.mock("@/components/teaching-kit/ScriptView", () => ({
  ScriptView: () => <div data-testid="script-view">Script</div>,
}));
vi.mock("@/components/teaching-kit/QuestionBankView", () => ({
  QuestionBankView: () => <div data-testid="questions-view">Questions</div>,
}));
vi.mock("@/components/teaching-kit/WorksheetViewer", () => ({
  WorksheetViewer: () => <div data-testid="worksheet-view">Worksheet</div>,
}));
vi.mock("@/components/teaching-kit/PptViewer", () => ({
  PptViewer: () => <div data-testid="ppt-view">Slides</div>,
}));
vi.mock("@/components/teaching-kit/MindMapCanvas", () => ({
  MindMapCanvas: () => <div data-testid="mindmap-view">MindMap</div>,
}));
vi.mock("@/components/teaching-kit/AudioPlayer", () => ({
  AudioPlayer: ({ resourceId }: { resourceId: string }) => (
    <div data-testid="audio-player">{resourceId}</div>
  ),
}));
vi.mock("@/components/teaching-kit/ComingSoonPanel", () => ({
  ComingSoonPanel: ({ feature }: { feature: string }) => (
    <div data-testid="coming-soon">{feature}</div>
  ),
}));

// Mock the API call used by the Regenerate button
vi.mock("@/lib/api-client", () => ({
  regenerateResource: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeResource(
  resourceType: GeneratedResource["resourceType"],
  content: object = { learning_objectives: [] },
): GeneratedResource {
  return {
    id: `id-${resourceType}`,
    resourceType,
    content: content as GeneratedResource["content"],
    cacheHit: false,
    params: {},
    createdAt: new Date().toISOString(),
  };
}

const LESSON_PLAN = makeResource("lesson_plan", {
  learning_objectives: ["obj1"],
  introduction: "",
  core_concepts: [],
  classroom_discussion: [],
  assessment: [],
  homework: "",
});

const QUESTIONS = makeResource("questions", {
  questions: [],
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ResourceTabs", () => {
  it("renders tab buttons for each supplied resource", () => {
    render(
      <ResourceTabs
        resources={[LESSON_PLAN, QUESTIONS]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    expect(
      screen.getByRole("tab", { name: /lesson plan/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: /questions/i }),
    ).toBeInTheDocument();
  });

  it("activates the lesson_plan tab by default and renders its body", () => {
    render(
      <ResourceTabs
        resources={[LESSON_PLAN, QUESTIONS]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    const lpTab = screen.getByRole("tab", { name: /lesson plan/i });
    expect(lpTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTestId("lesson-plan-view")).toBeInTheDocument();
  });

  it("switches to the questions tab on click and renders its body", async () => {
    const user = userEvent.setup();

    render(
      <ResourceTabs
        resources={[LESSON_PLAN, QUESTIONS]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    await user.click(screen.getByRole("tab", { name: /questions/i }));

    expect(
      screen.getByRole("tab", { name: /questions/i }),
    ).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTestId("questions-view")).toBeInTheDocument();
    // Lesson plan body should no longer be visible
    expect(screen.queryByTestId("lesson-plan-view")).toBeNull();
  });

  it("renders pending tabs as disabled with a spinner", () => {
    render(
      <ResourceTabs
        resources={[LESSON_PLAN]}
        chapterName="Photosynthesis"
        pendingTypes={["questions"]}
      />,
    );

    const qTab = screen.getByRole("tab", { name: /questions/i });
    expect(qTab).toBeDisabled();
  });

  it("shows 'From library' badge when the active resource is a cache hit", () => {
    const cached: GeneratedResource = { ...LESSON_PLAN, cacheHit: true };

    render(
      <ResourceTabs
        resources={[cached]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    expect(screen.getByText("From library")).toBeInTheDocument();
  });

  it("renders AudioPlayer for audio resource type", async () => {
    const user = userEvent.setup();
    const audioResource = makeResource("audio", {
      one_minute: "audio text",
      three_minutes: "",
      five_minutes: "",
    });

    render(
      <ResourceTabs
        resources={[LESSON_PLAN, audioResource]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    await user.click(screen.getByRole("tab", { name: /audio/i }));

    expect(screen.getByTestId("audio-player")).toBeInTheDocument();
    expect(screen.getByTestId("audio-player")).toHaveTextContent(
      "id-audio",
    );
  });

  it("shows a tablist with aria-label", () => {
    render(
      <ResourceTabs
        resources={[LESSON_PLAN]}
        chapterName="Photosynthesis"
        pendingTypes={[]}
      />,
    );

    expect(
      screen.getByRole("tablist", { name: /teaching kit resources/i }),
    ).toBeInTheDocument();
  });
});
