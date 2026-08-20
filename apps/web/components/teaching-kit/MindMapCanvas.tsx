"use client";

import type { MindMapNode } from "@shiksha-sathi/shared-types";
import { Printer } from "lucide-react";

import { Button } from "@/components/ui/button";

/** Radial layout, computed rather than force-simulated.
 *
 * A mind map from the generator is a shallow, wide tree (root → 4-6 sub-topics
 * → 2-4 key points each), which a deterministic radial sweep lays out cleanly
 * and, unlike a physics simulation, renders identically every time — so a
 * printed copy matches what the teacher saw on screen. */
const RING_RADIUS = [0, 190, 320];
const VIEWBOX = 760;
const CENTER = VIEWBOX / 2;

interface PlacedNode {
  node: MindMapNode;
  x: number;
  y: number;
  depth: number;
  parent: { x: number; y: number } | null;
}

function layout(root: MindMapNode): PlacedNode[] {
  const placed: PlacedNode[] = [
    { node: root, x: CENTER, y: CENTER, depth: 0, parent: null },
  ];

  const branches = root.children;
  branches.forEach((branch, i) => {
    // Start at -90deg so the first branch sits at the top rather than the right.
    const angle =
      (i / Math.max(branches.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const bx = CENTER + Math.cos(angle) * RING_RADIUS[1];
    const by = CENTER + Math.sin(angle) * RING_RADIUS[1];
    placed.push({
      node: branch,
      x: bx,
      y: by,
      depth: 1,
      parent: { x: CENTER, y: CENTER },
    });

    const leaves = branch.children;
    leaves.forEach((leaf, j) => {
      // Fan the leaves around their own branch's angle so they stay visually
      // attached to it instead of spreading across the whole outer ring.
      const spread = Math.PI / 5;
      const offset =
        leaves.length === 1
          ? 0
          : (j / (leaves.length - 1) - 0.5) * spread * leaves.length;
      const leafAngle = angle + offset;
      placed.push({
        node: leaf,
        x: CENTER + Math.cos(leafAngle) * RING_RADIUS[2],
        y: CENTER + Math.sin(leafAngle) * RING_RADIUS[2],
        depth: 2,
        parent: { x: bx, y: by },
      });
    });
  });

  return placed;
}

const FILL = ["var(--primary)", "var(--accent)", "var(--card)"];
const TEXT = [
  "var(--primary-foreground)",
  "var(--accent-foreground)",
  "var(--card-foreground)",
];
const FONT_SIZE = [17, 14, 12];

/** Wraps a label onto at most two lines so long Hindi topic names don't overrun
 * their pill. SVG has no text wrapping of its own. */
function wrap(label: string, perLine: number): string[] {
  if (label.length <= perLine) return [label];
  const words = label.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    if ((current + " " + word).trim().length > perLine && current) {
      lines.push(current);
      current = word;
    } else {
      current = (current + " " + word).trim();
    }
  }
  if (current) lines.push(current);
  return lines.slice(0, 2);
}

export function MindMapCanvas({ content }: { content: MindMapNode }) {
  const nodes = layout(content);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end print:hidden">
        <Button type="button" variant="outline" onClick={() => window.print()}>
          <Printer />
          Print
        </Button>
      </div>

      <div
        data-print-region="mind-map"
        className="border-border overflow-x-auto rounded-xl border"
      >
        <svg
          viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
          className="h-auto w-full min-w-[520px]"
          role="img"
          aria-label={`Mind map for ${content.label}`}
        >
          {nodes.map(
            (n, i) =>
              n.parent && (
                <line
                  key={`edge-${i}`}
                  x1={n.parent.x}
                  y1={n.parent.y}
                  x2={n.x}
                  y2={n.y}
                  stroke="var(--border)"
                  strokeWidth={n.depth === 1 ? 2.5 : 1.5}
                />
              ),
          )}

          {nodes.map((n, i) => {
            const lines = wrap(n.node.label, n.depth === 0 ? 18 : 16);
            const width =
              Math.max(...lines.map((l) => l.length)) *
                (FONT_SIZE[n.depth] * 0.58) +
              24;
            const height = lines.length * (FONT_SIZE[n.depth] + 6) + 12;
            return (
              <g key={`node-${i}`}>
                <rect
                  x={n.x - width / 2}
                  y={n.y - height / 2}
                  width={width}
                  height={height}
                  rx={height / 2}
                  fill={FILL[n.depth]}
                  stroke="var(--border)"
                  strokeWidth={1}
                />
                <text
                  x={n.x}
                  y={n.y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={FONT_SIZE[n.depth]}
                  fontWeight={n.depth === 0 ? 700 : 500}
                  fill={TEXT[n.depth]}
                >
                  {lines.map((line, li) => (
                    <tspan
                      key={li}
                      x={n.x}
                      dy={
                        li === 0
                          ? -((lines.length - 1) * (FONT_SIZE[n.depth] + 6)) / 2
                          : FONT_SIZE[n.depth] + 6
                      }
                    >
                      {line}
                    </tspan>
                  ))}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
