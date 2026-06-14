"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, GraduationCap, Target, TrendingUp } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreGauge } from "@/components/match/score-gauge";
import { ExplanationPanel } from "@/components/match/explanation-panel";
import { RoadmapView } from "@/components/mentor/roadmap-view";
import { useGenerateRoadmap } from "@/lib/mentor";
import type { MatchDetail } from "@/lib/types";

function recommendationTone(rec: string): "success" | "warning" | "danger" {
  if (rec.toLowerCase().includes("strong")) return "success";
  if (rec.toLowerCase().includes("consider")) return "warning";
  return "danger";
}

export function MatchResult({ match }: { match: MatchDetail }) {
  const { prediction, skill_gap, recommendations } = match;
  const roadmap = useGenerateRoadmap();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col gap-5"
    >
      {/* Score summary */}
      <Card>
        <CardContent className="flex flex-col items-center gap-6 py-6 sm:flex-row sm:items-center sm:justify-around">
          <ScoreGauge score={prediction.fit_score} />
          <div className="flex flex-col items-center gap-2 sm:items-start">
            <Badge tone={recommendationTone(prediction.recommendation)} className="text-sm">
              {prediction.recommendation}
            </Badge>
            <div className="flex items-center gap-2 text-sm text-muted">
              <TrendingUp className="h-4 w-4" />
              Interview probability:{" "}
              <span className="font-medium text-foreground">
                {Math.round(prediction.interview_probability * 100)}%
              </span>
            </div>
            <p className="max-w-xs text-center text-xs text-muted sm:text-left">
              {match.resume_filename} → {match.job_title ?? "job"} · model:{" "}
              {prediction.backend}
            </p>
          </div>
        </CardContent>
      </Card>

      <ExplanationPanel contributions={prediction.explanation} />

      {/* Skill gap */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="h-4 w-4 text-success" /> Strength areas
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {skill_gap.strengths.length > 0 ? (
              skill_gap.strengths.map((s) => (
                <Badge key={s} tone="success">
                  {s}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted">No matched skills yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4 text-warning" /> Gaps &amp; weak areas
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {skill_gap.weak_areas.length > 0 ? (
              skill_gap.weak_areas.map((s) => (
                <Badge key={s} tone="danger">
                  {s}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted">No major gaps detected. 🎉</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-4 w-4 text-primary" /> Recommended skills to learn
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {recommendations.map((r) => (
              <div
                key={r.skill}
                className="flex items-center justify-between gap-3 rounded-lg border border-border bg-surface-2/40 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-medium">{r.skill}</p>
                  <p className="text-xs text-muted">{r.reason}</p>
                </div>
                <Badge tone={r.priority === "High" ? "danger" : "warning"}>{r.priority}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {/* Learning roadmap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <GraduationCap className="h-4 w-4 text-primary" /> Learning roadmap
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {!roadmap.data ? (
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-muted">
                Generate a personalized weekly plan to close your skill gaps.
              </p>
              <Button
                onClick={() => roadmap.mutate(match.id)}
                isLoading={roadmap.isPending}
              >
                Generate roadmap
              </Button>
            </div>
          ) : (
            <RoadmapView roadmap={roadmap.data} />
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
