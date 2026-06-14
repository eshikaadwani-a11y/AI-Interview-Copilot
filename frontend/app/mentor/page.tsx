"use client";

import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { Bot, Database, Send, User } from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useAskMentor, useIngestJob, useIngestResume } from "@/lib/mentor";
import { useResumes } from "@/lib/resumes";
import { useJobs } from "@/lib/jobs";
import type { Citation } from "@/lib/types";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  provider?: string;
}

function MentorWorkspace() {
  const { data: resumes } = useResumes();
  const { data: jobs } = useJobs();
  const ingestResume = useIngestResume();
  const ingestJob = useIngestJob();
  const ask = useAskMentor();

  const [resumeId, setResumeId] = useState("");
  const [jobId, setJobId] = useState("");
  const [indexed, setIndexed] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");

  const indexDocuments = () => {
    const tasks: Promise<unknown>[] = [];
    if (resumeId) tasks.push(ingestResume.mutateAsync(resumeId));
    if (jobId) tasks.push(ingestJob.mutateAsync(jobId));
    if (tasks.length === 0) return;
    Promise.all(tasks).then(() => setIndexed(true));
  };

  const onAsk = (e: FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    ask.mutate(q, {
      onSuccess: (res) =>
        setMessages((m) => [
          ...m,
          { role: "assistant", text: res.answer, citations: res.citations, provider: res.provider },
        ]),
      onError: () =>
        setMessages((m) => [
          ...m,
          { role: "assistant", text: "Sorry, I couldn't answer that right now." },
        ]),
    });
  };

  const indexing = ingestResume.isPending || ingestJob.isPending;

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">AI Mentor</h1>
          <p className="text-sm text-muted">
            Ask questions grounded in your resume and the job description.
          </p>
        </div>

        {/* Setup */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="h-4 w-4 text-primary" /> Index your documents
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Select value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
                <option value="">Select a resume…</option>
                {resumes?.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.filename}
                  </option>
                ))}
              </Select>
              <Select value={jobId} onChange={(e) => setJobId(e.target.value)}>
                <option value="">Select a job…</option>
                {jobs?.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title ?? "Untitled role"}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={indexDocuments} isLoading={indexing} disabled={!resumeId && !jobId}>
                Index for mentor
              </Button>
              {indexed && <Badge tone="success">Indexed ✓</Badge>}
            </div>
          </CardContent>
        </Card>

        {/* Chat */}
        <Card>
          <CardContent className="flex flex-col gap-4 pt-6">
            <div className="flex max-h-[420px] flex-col gap-4 overflow-y-auto">
              {messages.length === 0 && (
                <p className="py-8 text-center text-sm text-muted">
                  Try: “What skills am I missing for this role?” or “How can I improve my resume?”
                </p>
              )}
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}
                >
                  {m.role === "assistant" && (
                    <span className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                      <Bot className="h-4 w-4" />
                    </span>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-surface-2 text-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 border-t border-border/50 pt-2">
                        {m.citations.map((c, j) => (
                          <Badge key={j} tone="default">
                            {c.source_type}: {c.title ?? c.source_id}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  {m.role === "user" && (
                    <span className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-2">
                      <User className="h-4 w-4" />
                    </span>
                  )}
                </motion.div>
              ))}
              {ask.isPending && (
                <div className="flex items-center gap-2 text-sm text-muted">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  Thinking…
                </div>
              )}
            </div>

            <form onSubmit={onAsk} className="flex items-center gap-2 border-t border-border pt-4">
              <Input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask your AI mentor…"
              />
              <Button type="submit" disabled={!question.trim()} isLoading={ask.isPending}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function MentorPage() {
  return (
    <Protected>
      <MentorWorkspace />
    </Protected>
  );
}
