"use client";

import Link from "next/link";
import {
  Briefcase,
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
    description: "Upload your resume to extract a structured profile + AI feedback.",
    milestone: "Available",
    href: "/resume",
  },
  {
    icon: Briefcase,
    title: "Job Description Analysis",
    description: "Extract required vs preferred skills and responsibilities from a JD.",
    milestone: "Available",
    href: "/jobs",
  },
  {
    icon: GitCompare,
    title: "Candidate Matching",
    description: "Compare your resume to a job description with real ML scoring.",
    milestone: "Available",
    href: "/match",
  },
  {
    icon: MessagesSquare,
    title: "AI Mentor",
    description: "Ask questions grounded in your resume and the job description.",
    milestone: "Available",
    href: "/mentor",
  },
  {
    icon: GraduationCap,
    title: "Learning Roadmap",
    description: "Generate a weekly plan to close your skill gaps from a match.",
    milestone: "Available",
    href: "/match",
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
          {upcoming.map((item) => {
            const card = (
              <Card
                className={item.href ? "h-full cursor-pointer transition-colors hover:border-primary/40" : "h-full"}
              >
                <CardHeader className="flex flex-row items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
                      <item.icon className="h-5 w-5" />
                    </span>
                    <CardTitle className="text-base">{item.title}</CardTitle>
                  </div>
                  <Badge tone={item.href ? "success" : "default"}>{item.milestone}</Badge>
                </CardHeader>
                <CardContent>
                  <CardDescription>{item.description}</CardDescription>
                </CardContent>
              </Card>
            );
            return item.href ? (
              <Link key={item.title} href={item.href}>
                {card}
              </Link>
            ) : (
              <div key={item.title}>{card}</div>
            );
          })}
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
