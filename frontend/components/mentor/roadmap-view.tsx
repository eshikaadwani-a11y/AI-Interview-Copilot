"use client";

import { motion } from "framer-motion";
import { CalendarDays, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Roadmap } from "@/lib/types";

export function RoadmapView({ roadmap }: { roadmap: Roadmap }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <CalendarDays className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">
          {roadmap.weeks.length}-week learning roadmap
        </h3>
        {roadmap.job_title && (
          <span className="text-sm text-muted">· {roadmap.job_title}</span>
        )}
      </div>

      <div className="flex flex-col gap-4">
        {roadmap.weeks.map((week, i) => (
          <motion.div
            key={week.week}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary">
                  {week.week}
                </span>
                <CardTitle className="text-base">{week.focus}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div className="flex flex-wrap gap-1.5">
                  {week.skills.map((s) => (
                    <Badge key={s} tone="primary">
                      {s}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-col gap-1.5">
                  {week.resources.map((r) => (
                    <a
                      key={r.url}
                      href={r.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      {r.title}
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
