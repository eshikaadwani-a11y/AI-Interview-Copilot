"use client";

import {
  FileSearch,
  GitCompare,
  GraduationCap,
  MessagesSquare,
} from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/store/auth";

const upcoming = [
  {
    icon: FileSearch,
    title: "Resume Analysis",
    description: "Upload your resume to extract a structured profile.",
    milestone: "Milestone 3",
  },
  {
    icon: GitCompare,
    title: "Candidate Matching",
    description: "Compare your resume to a job description with real ML scoring.",
    milestone: "Milestone 5–6",
  },
  {
    icon: GraduationCap,
    title: "Learning Roadmap",
    description: "Get a personalized plan to close your skill gaps.",
    milestone: "Milestone 8",
  },
  {
    icon: MessagesSquare,
    title: "AI Interview Simulator",
    description: "Practice realistic interviews with dynamic follow-ups.",
    milestone: "Milestone 9",
  },
];

function DashboardContent() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome{user ? `, ${user.full_name.split(" ")[0]}` : ""} 👋
          </h1>
          <p className="text-sm text-muted">
            Your workspace is ready. Features unlock as the product is built out.
          </p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {upcoming.map((item) => (
            <Card key={item.title}>
              <CardHeader className="flex flex-row items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
                    <item.icon className="h-5 w-5" />
                  </span>
                  <CardTitle className="text-base">{item.title}</CardTitle>
                </div>
                <Badge>{item.milestone}</Badge>
              </CardHeader>
              <CardContent>
                <CardDescription>{item.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Protected>
      <DashboardContent />
    </Protected>
  );
}
