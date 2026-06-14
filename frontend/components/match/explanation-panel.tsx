"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Contribution } from "@/lib/types";

/**
 * "Why this score" panel. Renders each feature's contribution as a diverging
 * bar (green = pushes the score up, red = pulls it down) — a human-readable
 * view of the model's SHAP / linear contributions.
 */
export function ExplanationPanel({
  contributions,
  title = "Why this score",
}: {
  contributions: Contribution[];
  title?: string;
}) {
  const top = contributions.slice(0, 8);
  const max = Math.max(0.0001, ...top.map((c) => Math.abs(c.contribution)));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {top.map((c) => {
          const pct = (Math.abs(c.contribution) / max) * 100;
          const positive = c.contribution >= 0;
          return (
            <div key={c.feature} className="flex items-center gap-3">
              <span className="w-40 shrink-0 text-right text-xs text-muted">{c.label}</span>
              <div className="relative h-3 flex-1 rounded-full bg-surface-2">
                <div
                  className="absolute top-0 h-3 rounded-full"
                  style={{
                    width: `${pct}%`,
                    left: positive ? "50%" : undefined,
                    right: positive ? undefined : "50%",
                    backgroundColor: positive ? "hsl(var(--success))" : "hsl(var(--danger))",
                  }}
                />
                <div className="absolute left-1/2 top-0 h-3 w-px bg-border" />
              </div>
              <span
                className="w-12 shrink-0 text-xs"
                style={{ color: positive ? "hsl(var(--success))" : "hsl(var(--danger))" }}
              >
                {positive ? "+" : ""}
                {c.contribution.toFixed(2)}
              </span>
            </div>
          );
        })}
        <p className="pt-1 text-xs text-muted">
          Green factors raise your predicted fit; red factors lower it.
        </p>
      </CardContent>
    </Card>
  );
}
