"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brain,
  FileSearch,
  GitCompare,
  GraduationCap,
  MessagesSquare,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FeatureCard } from "@/components/marketing/feature-card";

const features = [
  {
    icon: FileSearch,
    title: "Resume Analysis",
    description:
      "Upload a PDF and we extract skills, projects, education, and experience into a structured profile.",
  },
  {
    icon: GitCompare,
    title: "Candidate Matching",
    description:
      "Compare your resume against any job description to reveal overlap, strengths, and gaps.",
  },
  {
    icon: Brain,
    title: "Real ML Fit Prediction",
    description:
      "An XGBoost model predicts candidate-job fit and interview probability — with SHAP explanations.",
  },
  {
    icon: GraduationCap,
    title: "Learning Roadmap",
    description:
      "Get a personalized weekly plan with the exact skills to learn and resources to use.",
  },
  {
    icon: MessagesSquare,
    title: "AI Interview Simulator",
    description:
      "Realistic technical interviews with dynamic follow-up questions across SWE, AI, and Data roles.",
  },
  {
    icon: TrendingUp,
    title: "Readiness Analytics",
    description:
      "Track match score, hiring probability, skill gaps, and interview readiness on one dashboard.",
  },
];

export default function LandingPage() {
  return (
    <main className="relative">
      <div className="bg-mesh pointer-events-none absolute inset-0 -z-10" />

      {/* Nav */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="font-semibold tracking-tight">Interview Copilot</span>
        </div>
        <nav className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Sign in
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm">Get started</Button>
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center gap-6"
        >
          <Badge tone="primary" className="gap-1.5">
            <Target className="h-3.5 w-3.5" /> ML-powered interview prep
          </Badge>
          <h1 className="max-w-3xl text-balance text-4xl font-semibold tracking-tight sm:text-6xl">
            Your personal recruiter, interviewer, and mentor
          </h1>
          <p className="max-w-2xl text-pretty text-lg text-muted">
            Upload your resume and a job description. Get a real machine-learning
            fit score, a tailored learning roadmap, and realistic AI interviews —
            all in one place.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="/register">
              <Button size="lg">Start preparing free</Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                I already have an account
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} index={index} {...feature} />
          ))}
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-8 text-sm text-muted">
          AI Interview Copilot — built with FastAPI, Next.js, MongoDB, ChromaDB,
          and real scikit-learn / XGBoost models.
        </div>
      </footer>
    </main>
  );
}
