"use client";

import Link from "next/link";
import { useState } from "react";
import { GitCompare, Sparkles } from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { MatchResult } from "@/components/match/match-result";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { formatApiError } from "@/lib/auth";
import { useCreateMatch } from "@/lib/match";
import { useResumes } from "@/lib/resumes";
import { useJobs } from "@/lib/jobs";

function MatchWorkspace() {
  const { data: resumes } = useResumes();
  const { data: jobs } = useJobs();
  const createMatch = useCreateMatch();

  const [resumeId, setResumeId] = useState("");
  const [jobId, setJobId] = useState("");

  const canMatch = Boolean(resumeId && jobId);
  const noData = (resumes?.length ?? 0) === 0 || (jobs?.length ?? 0) === 0;

  const runMatch = () => {
    if (!canMatch) return;
    createMatch.mutate({ resume_id: resumeId, job_id: jobId });
  };

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Candidate Matching</h1>
          <p className="text-sm text-muted">
            Compare a resume against a job description. The ML model predicts your
            fit and explains the score.
          </p>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Run a match</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {noData ? (
              <p className="text-sm text-muted">
                You need at least one{" "}
                <Link href="/resume" className="text-primary hover:underline">
                  resume
                </Link>{" "}
                and one{" "}
                <Link href="/jobs" className="text-primary hover:underline">
                  job
                </Link>{" "}
                to run a match.
              </p>
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <Label htmlFor="resume">Resume</Label>
                    <Select
                      id="resume"
                      value={resumeId}
                      onChange={(e) => setResumeId(e.target.value)}
                    >
                      <option value="">Select a resume…</option>
                      {resumes?.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.filename}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="job">Job</Label>
                    <Select id="job" value={jobId} onChange={(e) => setJobId(e.target.value)}>
                      <option value="">Select a job…</option>
                      {jobs?.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.title ?? "Untitled role"}
                          {j.company ? ` · ${j.company}` : ""}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>

                {createMatch.isError && (
                  <p className="text-sm text-danger">{formatApiError(createMatch.error)}</p>
                )}

                <Button onClick={runMatch} disabled={!canMatch} isLoading={createMatch.isPending}>
                  <Sparkles className="h-4 w-4" />
                  Predict fit
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {createMatch.data ? (
          <MatchResult match={createMatch.data} />
        ) : (
          !noData && (
            <Card>
              <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-2 text-center">
                <GitCompare className="h-8 w-8 text-muted" />
                <p className="font-medium">No match run yet</p>
                <p className="text-sm text-muted">
                  Select a resume and a job, then predict your fit.
                </p>
              </CardContent>
            </Card>
          )
        )}
      </main>
    </div>
  );
}

export default function MatchPage() {
  return (
    <Protected>
      <MatchWorkspace />
    </Protected>
  );
}
