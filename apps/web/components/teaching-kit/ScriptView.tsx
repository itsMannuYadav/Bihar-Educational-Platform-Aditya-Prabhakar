"use client";

import type { TeachingScriptContent } from "@shiksha-sathi/shared-types";
import { MessageCircleQuestion } from "lucide-react";
import { useState } from "react";

interface Props {
  content: TeachingScriptContent;
}

/** The script is meant to be read aloud mid-class, so Blackboard Mode is not a
 * styling toggle — it strips everything except the words the teacher says and
 * sets them large enough to glance at from the front of the room. */
export function ScriptView({ content }: Props) {
  const [blackboardMode, setBlackboardMode] = useState(false);

  const bodyClass = blackboardMode
    ? "text-lg leading-loose sm:text-xl"
    : "text-sm leading-relaxed";

  return (
    <div className="flex flex-col gap-5">
      <label className="flex items-center gap-2 self-start text-sm">
        <input
          type="checkbox"
          checked={blackboardMode}
          onChange={(e) => setBlackboardMode(e.target.checked)}
          className="accent-primary size-4"
        />
        <span className="font-medium">Blackboard Mode</span>
        <span className="text-muted-foreground text-xs">
          large text, script only
        </span>
      </label>

      <p className={bodyClass}>{content.opening}</p>

      {content.sections.map((section, i) => (
        <div key={i} className="flex flex-col gap-2">
          {!blackboardMode && (
            <h3 className="font-heading text-base font-bold">
              {section.heading}
            </h3>
          )}
          <p className={bodyClass}>{section.script}</p>
          {!blackboardMode && section.discussion_prompt && (
            <p className="bg-accent text-accent-foreground flex items-start gap-2 rounded-xl p-3 text-sm">
              <MessageCircleQuestion className="mt-0.5 size-4 shrink-0" />
              <span>{section.discussion_prompt}</span>
            </p>
          )}
        </div>
      ))}

      <p className={bodyClass}>{content.closing}</p>
    </div>
  );
}
