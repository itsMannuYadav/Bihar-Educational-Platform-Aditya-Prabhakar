import { Clock } from "lucide-react";

interface Props {
  feature: string;
  detail?: string;
}

/** Shown for resource types the schema and API already model but no generator
 * fills yet (audio → Phase 5, video → deliberately never for MVP). Says which
 * one and stops there — a teacher hitting an empty tab should not have to
 * wonder whether generation failed. */
export function ComingSoonPanel({ feature, detail }: Props) {
  return (
    <div className="border-border text-muted-foreground flex flex-col items-center gap-2 rounded-xl border border-dashed px-6 py-12 text-center">
      <Clock className="size-6" />
      <p className="text-foreground text-sm font-semibold">{feature}</p>
      <p className="max-w-xs text-xs">
        {detail ?? "This is on the way — everything else in the kit is ready."}
      </p>
    </div>
  );
}
