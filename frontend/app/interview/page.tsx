"use client";

import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, MessagesSquare, Send } from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { formatApiError } from "@/lib/auth";
import {
  INTERVIEW_MODES,
  useAnswerInterview,
  useFinishInterview,
  useStartInterview,
} from "@/lib/interview";
import { useResumes } from "@/lib/resumes";
import type { InterviewState } from "@/lib/types";

function InterviewWorkspace() {
  const { data: resumes } = useResumes();
  const start = useStartInterview();
  const answerMut = useAnswerInterview();
  const finishMut = useFinishInterview();

  const [mode, setMode] = useState("software_engineer");
  const [resumeId, setResumeId] = useState("");
  const [numQuestions, setNumQuestions] = useState(6);
  const [state, setState] = useState<InterviewState | null>(null);
  const [answer, setAnswer] = useState("");

  const beginInterview = () => {
    start.mutate(
      { mode, num_questions: numQuestions, resume_id: resumeId || null },
      { onSuccess: (s) => setState(s) },
    );
  };

  const submitAnswer = (e: FormEvent) => {
    e.preventDefault();
    if (!state || !answer.trim()) return;
    answerMut.mutate(
      { id: state.id, answer },
      {
        onSuccess: (s) => {
          setState(s);
          setAnswer("");
        },
      },
    );
  };

  const endInterview = () => {
    if (!state) return;
    finishMut.mutate(state.id, { onSuccess: (s) => setState(s) });
  };

  // ── Setup screen ──
  if (!state) {
    return (
      <SetupCard
        mode={mode}
        setMode={setMode}
        resumeId={resumeId}
        setResumeId={setResumeId}
        numQuestions={numQuestions}
        setNumQuestions={setNumQuestions}
        resumes={resumes ?? []}
        onStart={beginInterview}
        loading={start.isPending}
        error={start.isError ? formatApiError(start.error) : null}
      />
    );
  }

  // ── Completion screen ──
  if (state.finished) {
    return (
      <Card>
        <CardContent className="flex min-h-[260px] flex-col items-center justify-center gap-3 text-center">
          <CheckCircle2 className="h-10 w-10 text-success" />
          <h2 className="text-xl font-semibold">Interview complete</h2>
          <p className="max-w-md text-sm text-muted">
            You answered {state.answered} of {state.total} questions in the{" "}
            {state.mode_label} track. Detailed scoring and a performance report
            arrive in Milestone 10.
          </p>
          <Button onClick={() => setState(null)}>Start another interview</Button>
        </CardContent>
      </Card>
    );
  }

  // ── Active interview ──
  const q = state.current_question;
  const progress = state.total ? Math.round((state.answered / state.total) * 100) : 0;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge tone="primary">{state.mode_label}</Badge>
          {q && <Badge>{q.category}</Badge>}
          {q?.type === "followup" && <Badge tone="warning">Follow-up</Badge>}
        </div>
        <Button variant="ghost" size="sm" onClick={endInterview} isLoading={finishMut.isPending}>
          End interview
        </Button>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className="h-2 rounded-full bg-primary"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4 }}
        />
      </div>

      <motion.div key={q?.index} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Question {state.answered + 1} of {state.total}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-lg leading-relaxed">{q?.text}</p>
            <form onSubmit={submitAnswer} className="flex flex-col gap-3">
              <Textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer…"
                required
              />
              <div className="flex justify-end">
                <Button type="submit" disabled={!answer.trim()} isLoading={answerMut.isPending}>
                  <Send className="h-4 w-4" />
                  Submit answer
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

function SetupCard(props: {
  mode: string;
  setMode: (v: string) => void;
  resumeId: string;
  setResumeId: (v: string) => void;
  numQuestions: number;
  setNumQuestions: (v: number) => void;
  resumes: { id: string; filename: string }[];
  onStart: () => void;
  loading: boolean;
  error: string | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MessagesSquare className="h-4 w-4 text-primary" /> Configure your interview
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <Label htmlFor="mode">Role track</Label>
            <Select id="mode" value={props.mode} onChange={(e) => props.setMode(e.target.value)}>
              {INTERVIEW_MODES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="num">Questions</Label>
            <Select
              id="num"
              value={String(props.numQuestions)}
              onChange={(e) => props.setNumQuestions(Number(e.target.value))}
            >
              {[4, 6, 8, 10].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="resume">Resume (optional)</Label>
            <Select
              id="resume"
              value={props.resumeId}
              onChange={(e) => props.setResumeId(e.target.value)}
            >
              <option value="">None</option>
              {props.resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <p className="text-xs text-muted">
          Linking a resume personalizes the Projects questions. Follow-up
          questions adapt to your answers.
        </p>
        {props.error && <p className="text-sm text-danger">{props.error}</p>}
        <div>
          <Button onClick={props.onStart} isLoading={props.loading}>
            Start interview
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function InterviewPage() {
  return (
    <Protected>
      <div className="min-h-screen">
        <TopBar />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold tracking-tight">AI Interview Simulator</h1>
            <p className="text-sm text-muted">
              Practice realistic technical interviews with dynamic follow-up questions.
            </p>
          </div>
          <InterviewWorkspace />
        </main>
      </div>
    </Protected>
  );
}
