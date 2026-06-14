"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Briefcase, Trash2 } from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { JobForm } from "@/components/job/job-form";
import { JobProfileView } from "@/components/job/job-profile-view";
import { Card, CardContent } from "@/components/ui/card";
import { useDeleteJob, useJob, useJobs } from "@/lib/jobs";

function JobsWorkspace() {
  const { data: jobs, isLoading } = useJobs();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: detail } = useJob(selectedId);
  const deleteJob = useDeleteJob();

  useEffect(() => {
    if (!selectedId && jobs && jobs.length > 0) {
      setSelectedId(jobs[0].id);
    }
  }, [jobs, selectedId]);

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Job Description Analysis</h1>
          <p className="text-sm text-muted">
            Paste a job description to extract required vs preferred skills,
            responsibilities, and experience requirements.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="flex flex-col gap-4">
            <JobForm onCreated={(j) => setSelectedId(j.id)} />

            <div className="flex flex-col gap-2">
              <p className="px-1 text-xs font-medium uppercase tracking-wide text-muted">
                Your jobs
              </p>
              {isLoading && <p className="px-1 text-sm text-muted">Loading…</p>}
              {jobs?.length === 0 && (
                <p className="px-1 text-sm text-muted">No jobs analyzed yet.</p>
              )}
              {jobs?.map((j) => (
                <Card
                  key={j.id}
                  onClick={() => setSelectedId(j.id)}
                  className={`cursor-pointer transition-colors ${
                    j.id === selectedId ? "border-primary/60" : "hover:border-primary/30"
                  }`}
                >
                  <CardContent className="flex items-center justify-between gap-2 py-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <Briefcase className="h-4 w-4 shrink-0 text-primary" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">
                          {j.title ?? "Untitled role"}
                        </p>
                        <p className="text-xs text-muted">
                          {j.company ?? "—"} · {j.required_skill_count} required skills
                        </p>
                      </div>
                    </div>
                    <button
                      aria-label="Delete job"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteJob.mutate(j.id, {
                          onSuccess: () => {
                            if (selectedId === j.id) setSelectedId(null);
                          },
                        });
                      }}
                      className="text-muted transition-colors hover:text-danger"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div>
            {detail ? (
              <motion.div
                key={detail.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <JobProfileView job={detail} />
              </motion.div>
            ) : (
              <Card>
                <CardContent className="flex min-h-[300px] flex-col items-center justify-center gap-2 text-center">
                  <Briefcase className="h-8 w-8 text-muted" />
                  <p className="font-medium">No job selected</p>
                  <p className="text-sm text-muted">
                    Analyze a job description to see its structured profile here.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function JobsPage() {
  return (
    <Protected>
      <JobsWorkspace />
    </Protected>
  );
}
