"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, ExternalLink, GraduationCap, Lightbulb } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreGauge } from "@/components/match/score-gauge";
import { ExplanationPanel } from "@/components/match/explanation-panel";
import type { AggregateScores, InterviewReport } from "@/lib/types";

const DIMENSIONS: { key: keyof AggregateScores; label: string }[] = [
  { key: "technical", label: "Technical Accuracy" },
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
      {/* Dual gauges: overall score + success probability */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-6">
            <ScoreGauge score={report.aggregate.overall} label="Overall Score" />
            <p className="text-xs text-muted">
              {report.answered}/{report.total} answered · {report.mode_label}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-6">
            <ScoreGauge score={successPct} label="Success Probability" />
            <Badge tone={successPct >= 70 ? "success" : successPct >= 45 ? "warning" : "danger"}>
              {report.success_label}
            </Badge>
            <p className="text-xs text-muted">
              Confidence {Math.round(report.prediction_confidence * 100)}% · model{" "}
              {report.model_version ?? "?"} ({report.model_backend})
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Dimension breakdown with explanations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Category scores</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {DIMENSIONS.map((d) => {
            const v = report.aggregate[d.key];
            return (
              <div key={d.key} className="flex items-center gap-3">
                <span className="w-40 shrink-0 text-sm text-muted">{d.label}</span>
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
          {Object.keys(report.category_scores).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2 border-t border-border pt-3">
              {Object.entries(report.category_scores).map(([cat, score]) => (
                <Badge key={cat} tone={score >= 70 ? "success" : score >= 50 ? "warning" : "danger"}>
                  {cat}: {score}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Why this prediction (Model 2 feature contributions) */}
      {report.success_explanation.length > 0 && (
        <ExplanationPanel
          title="Why this prediction"
          contributions={report.success_explanation}
        />
      )}

      {/* Strengths / weaknesses / suggestions */}
      <div className="grid gap-4 md:grid-cols-3">
        <FeedbackList icon={<CheckCircle2 className="h-4 w-4 text-success" />} title="Strength areas" items={report.strengths} />
        <FeedbackList icon={<AlertTriangle className="h-4 w-4 text-warning" />} title="Weak areas" items={report.weaknesses} />
        <FeedbackList icon={<Lightbulb className="h-4 w-4 text-primary" />} title="Improvement suggestions" items={report.suggestions} />
      </div>

      {/* Recommended learning plan */}
      {report.recommended_learning.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GraduationCap className="h-4 w-4 text-primary" /> Recommended learning plan
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {report.recommended_learning.map((item) => (
              <a
                key={item.topic}
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-3 rounded-lg border border-border bg-surface-2/40 px-3 py-2 hover:border-primary/40"
              >
                <div>
                  <p className="text-sm font-medium capitalize">{item.topic}</p>
                  <p className="text-xs text-muted">{item.title}</p>
                </div>
                <ExternalLink className="h-4 w-4 text-primary" />
              </a>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Per-question feedback with reasons */}
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
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                <ScoreLine label="Technical" value={q.evaluation!.technical} reasons={q.evaluation!.explanations.technical} />
                <ScoreLine label="Communication" value={q.evaluation!.communication} reasons={q.evaluation!.explanations.communication} />
                <ScoreLine label="Completeness" value={q.evaluation!.completeness} reasons={q.evaluation!.explanations.completeness} />
                <ScoreLine label="Confidence" value={q.evaluation!.confidence} reasons={q.evaluation!.explanations.confidence} />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function ScoreLine({ label, value, reasons }: { label: string; value: number; reasons?: string[] }) {
  return (
    <div className="rounded-md bg-background/40 p-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted">{label}</span>
        <span className="text-xs font-semibold" style={{ color: barColor(value) }}>
          {value}
        </span>
      </div>
      {reasons && reasons.length > 0 && (
        <ul className="mt-1 space-y-0.5">
          {reasons.slice(0, 4).map((r, i) => (
            <li key={i} className="text-[11px] leading-snug text-muted">
              {r.startsWith("Missed") ? "✗ " : r.startsWith("Mentioned") ? "✓ " : "• "}
              {r}
            </li>
          ))}
        </ul>
      )}
    </div>
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
