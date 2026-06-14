"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Lightbulb } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreGauge } from "@/components/match/score-gauge";
import type { AggregateScores, InterviewReport } from "@/lib/types";

const DIMENSIONS: { key: keyof AggregateScores; label: string }[] = [
  { key: "technical", label: "Technical" },
  { key: "communication", label: "Communication" },
  { key: "completeness", label: "Completeness" },
  { key: "confidence", label: "Confidence" },
];

function barColor(v: number): string {
  if (v >= 70) return "hsl(var(--success))";
  if (v >= 50) return "hsl(var(--warning))";
  return "hsl(var(--danger))";
}

export function ReportView({ report }: { report: InterviewReport }) {
  const successPct = Math.round(report.success_probability * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-5"
    >
      {/* Headline: success probability + overall */}
      <Card>
        <CardContent className="flex flex-col items-center gap-6 py-6 sm:flex-row sm:justify-around">
          <ScoreGauge score={successPct} label="Success likelihood" />
          <div className="flex flex-col items-center gap-2 sm:items-start">
            <Badge tone={successPct >= 70 ? "success" : successPct >= 45 ? "warning" : "danger"}>
              {report.success_label}
            </Badge>
            <p className="text-sm text-muted">
              Overall score:{" "}
              <span className="font-medium text-foreground">{report.aggregate.overall}</span>/100
            </p>
            <p className="text-xs text-muted">
              {report.answered}/{report.total} answered · {report.mode_label} · model:{" "}
              {report.model_backend}
            </p>
            <p className="max-w-xs text-xs text-muted">
              Predicted by the Interview Success model from your answer scores and resume fit.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Dimension breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Score breakdown</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {DIMENSIONS.map((d) => {
            const v = report.aggregate[d.key];
            return (
              <div key={d.key} className="flex items-center gap-3">
                <span className="w-32 shrink-0 text-sm text-muted">{d.label}</span>
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-2">
                  <motion.div
                    className="h-2.5 rounded-full"
                    style={{ backgroundColor: barColor(v) }}
                    initial={{ width: 0 }}
                    animate={{ width: `${v}%` }}
                    transition={{ duration: 0.6 }}
                  />
                </div>
                <span className="w-10 text-right text-sm font-medium">{v}</span>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Strengths / weaknesses / suggestions */}
      <div className="grid gap-4 md:grid-cols-3">
        <FeedbackList icon={<CheckCircle2 className="h-4 w-4 text-success" />} title="Strengths" items={report.strengths} />
        <FeedbackList icon={<AlertTriangle className="h-4 w-4 text-warning" />} title="Weaknesses" items={report.weaknesses} />
        <FeedbackList icon={<Lightbulb className="h-4 w-4 text-primary" />} title="Suggestions" items={report.suggestions} />
      </div>

      {/* Per-question */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Per-question feedback</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {report.per_question.filter((q) => q.evaluation).map((q) => (
            <div key={q.index} className="rounded-lg border border-border bg-surface-2/40 p-4">
              <div className="mb-1 flex items-center gap-2">
                <Badge>{q.category}</Badge>
                {q.type === "followup" && <Badge tone="warning">Follow-up</Badge>}
                <span className="ml-auto text-sm font-semibold">{q.evaluation!.score}/100</span>
              </div>
              <p className="text-sm font-medium">{q.question}</p>
              {q.answer && <p className="mt-1 text-xs text-muted line-clamp-3">{q.answer}</p>}
              {q.evaluation!.suggestions.length > 0 && (
                <p className="mt-2 text-xs text-primary">💡 {q.evaluation!.suggestions[0]}</p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function FeedbackList({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          {icon} {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1.5 text-sm text-muted">
        {items.length ? items.map((s, i) => <span key={i}>• {s}</span>) : <span>—</span>}
      </CardContent>
    </Card>
  );
}
