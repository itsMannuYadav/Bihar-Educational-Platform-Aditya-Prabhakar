import type { LessonPlanContent } from "@shiksha-sathi/shared-types";

import {
  BulletList,
  ResourceSection,
} from "@/components/teaching-kit/ResourceSection";

export function LessonPlanView({ content }: { content: LessonPlanContent }) {
  return (
    <div className="flex flex-col gap-6">
      <ResourceSection title="Learning objectives">
        <BulletList items={content.objectives} />
      </ResourceSection>

      <ResourceSection title="Introduction">
        <p className="text-sm leading-relaxed">{content.introduction}</p>
      </ResourceSection>

      <ResourceSection title="Core concepts">
        <BulletList items={content.core_concepts} />
      </ResourceSection>

      <ResourceSection title="Classroom discussion">
        <BulletList items={content.classroom_discussion} />
      </ResourceSection>

      <ResourceSection title="Assessment">
        <BulletList items={content.assessment} />
      </ResourceSection>

      <ResourceSection title="Homework">
        <p className="text-sm leading-relaxed">{content.homework}</p>
      </ResourceSection>
    </div>
  );
}
