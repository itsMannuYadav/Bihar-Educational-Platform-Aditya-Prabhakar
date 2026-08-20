import type { ReactNode } from "react";

interface Props {
  title: string;
  children: ReactNode;
}

/** One labelled block inside a resource view. Every viewer is built from these
 * so a teacher scanning between tabs meets the same visual rhythm rather than
 * a different layout per resource type. */
export function ResourceSection({ title, children }: Props) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
        {title}
      </h3>
      {children}
    </section>
  );
}

export function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm leading-relaxed">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}
