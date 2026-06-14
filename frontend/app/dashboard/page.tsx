"use client";

import Link from "next/link";
import {
  Bot,
  Briefcase,
  FileSearch,
  GitCompare,
  GraduationCap,
  MessagesSquare,
} from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { ScoreGauge } from "@/components/match/score-gauge";
import { CategoryRadar, SkillGapChart, TrendChart } from "@/components/dashboard/charts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth";
import { useDashboardSummary } from "@/lib/dashboard";

const features = [
  { icon: FileSearch, title: "Resume Analysis", description: "Upload your resume to extract a structured profile + AI feedback.", href: "/resume" },
  { icon: Briefcase, title: "Job Description Analysis", description: "Extract required vs preferred skills from a JD.", href: "/jobs" },
  { icon: GitCompare, title: "Candidate Matching", description: "Compare your resume to a job with real ML scoring.", href: "/match" },
  { icon: Bot, title: "AI Interview Simulator", description: "Practice interviews with dynamic follow-ups + scoring.", href: "/interview" },
  { icon: MessagesSquare, title: "AI Mentor", description: "Ask questions grounded in your resume and the JD.", href: "/mentor" },
  { icon: GraduationCap, title: "Learning Roadmap", description: "Generate a weekly plan to close your skill gaps.", href: "/match" },
];

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center py-4">
        <span className="text-2xl font-semibold">{value}</span>
        <span className="text-xs text-muted">{label}</span>
      </CardContent>
    </Card>
  );
}

function DashboardContent() {
  const user = useAuthStore((s) => s.user);
  const { data: summary, isLoading } = useDashboardSummary();

  const hasActivity = summary && (summary.counts.matches > 0 || summary.counts.interviews > 0);
  const radarData = summary
    ? Object.entries(summary.category_scores).map(([category, score]) => ({ category, score }))
    : [];

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user ? `, ${user.full_name.split(" ")[0]}` : ""} 👋
          </h1>
          <p className="text-sm text-muted">Your interview-readiness analytics at a glance.</p>
        </div>

        {/* Stat tiles */}
        {summary && (
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatTile label="Resumes" value={summary.counts.resumes} />
            <StatTile label="Jobs" value={summary.counts.jobs} />
            <StatTile label="Matches" value={summary.counts.matches} />
            <StatTile label="Interviews" value={summary.counts.interviews} />
          </div>
        )}

        {/* Readiness gauges */}
        {hasActivity && (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <GaugeCard title="Hiring Probability" value={summary?.hiring_probability ?? null} />
            <GaugeCard title="Interview Readiness" value={summary?.interview_readiness ?? null} />
            <GaugeCard title="Success Probability" value={summary?.success_probability ?? null} />
          </div>
        )}

        {/* Charts */}
        {hasActivity && (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {summary!.match_trend.length > 0 && (
              <TrendChart title="Match score over time" data={summary!.match_trend} />
            )}
            {radarData.length > 0 && <CategoryRadar data={radarData} />}
            {summary!.top_missing_skills.length > 0 && (
              <SkillGapChart data={summary!.top_missing_skills} />
            )}
            {summary!.interview_trend.length > 0 && (
              <TrendChart title="Interview score over time" data={summary!.interview_trend} />
            )}
          </div>
        )}

        {/* Recommended focus */}
        {summary && summary.recommended_focus.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-base">Recommended focus areas</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {summary.recommended_focus.map((s) => (
                <Badge key={s} tone="warning">
                  {s}
                </Badge>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Empty state */}
        {!isLoading && !hasActivity && (
          <Card className="mt-6">
            <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
              <p className="font-medium">No analytics yet</p>
              <p className="text-sm text-muted">
                Upload a resume, analyze a job, and run a match to see your readiness analytics here.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Feature navigation */}
        <h2 className="mb-3 mt-10 text-sm font-medium uppercase tracking-wide text-muted">
          Tools
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((item) => (
            <Link key={item.title} href={item.href}>
              <Card className="h-full cursor-pointer transition-colors hover:border-primary/40">
                <CardHeader className="flex flex-row items-center gap-3">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
                    <item.icon className="h-5 w-5" />
                  </span>
                  <CardTitle className="text-base">{item.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{item.description}</CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}

function GaugeCard({ title, value }: { title: string; value: number | null }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center py-6">
        {value != null ? (
          <ScoreGauge score={value} label={title} />
        ) : (
          <div className="flex h-[160px] flex-col items-center justify-center text-center">
            <span className="text-sm text-muted">{title}</span>
            <span className="mt-1 text-xs text-muted">Not available yet</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  return (
    <Protected>
      <DashboardContent />
    </Protected>
  );
}
