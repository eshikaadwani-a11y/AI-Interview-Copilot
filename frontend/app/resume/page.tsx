"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, Sparkles, Trash2 } from "lucide-react";
import { Protected } from "@/components/auth/protected";
import { TopBar } from "@/components/layout/top-bar";
import { UploadDropzone } from "@/components/resume/upload-dropzone";
import { ResumeProfileView } from "@/components/resume/resume-profile-view";
import { FeedbackPanel } from "@/components/mentor/feedback-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useDeleteResume, useResume, useResumes } from "@/lib/resumes";
import { useResumeFeedback } from "@/lib/mentor";

function ResumeWorkspace() {
  const { data: resumes, isLoading } = useResumes();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: detail } = useResume(selectedId);
  const deleteResume = useDeleteResume();
  const feedback = useResumeFeedback();

  // Auto-select the most recent resume once the list loads.
  useEffect(() => {
    if (!selectedId && resumes && resumes.length > 0) {
      setSelectedId(resumes[0].id);
    }
  }, [resumes, selectedId]);

  return (
    <div className="min-h-screen">
      <TopBar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Resume Analysis</h1>
          <p className="text-sm text-muted">
            Upload a PDF and we extract a structured profile — skills, experience,
            projects, education, and certifications.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          {/* Sidebar: upload + list */}
          <div className="flex flex-col gap-4">
            <UploadDropzone onUploaded={(r) => setSelectedId(r.id)} />

            <div className="flex flex-col gap-2">
              <p className="px-1 text-xs font-medium uppercase tracking-wide text-muted">
                Your resumes
              </p>
              {isLoading && <p className="px-1 text-sm text-muted">Loading…</p>}
              {resumes?.length === 0 && (
                <p className="px-1 text-sm text-muted">No resumes yet.</p>
              )}
              {resumes?.map((r) => (
                <Card
                  key={r.id}
                  onClick={() => setSelectedId(r.id)}
                  className={`cursor-pointer transition-colors ${
                    r.id === selectedId ? "border-primary/60" : "hover:border-primary/30"
                  }`}
                >
                  <CardContent className="flex items-center justify-between gap-2 py-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-primary" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{r.filename}</p>
                        <p className="text-xs text-muted">{r.skill_count} skills</p>
                      </div>
                    </div>
                    <button
                      aria-label="Delete resume"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteResume.mutate(r.id, {
                          onSuccess: () => {
                            if (selectedId === r.id) setSelectedId(null);
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

          {/* Main: profile view */}
          <div>
            {detail ? (
              <motion.div
                key={detail.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="flex flex-col gap-5"
              >
                <div className="flex justify-end">
                  <Button
                    variant="secondary"
                    onClick={() => feedback.mutate(detail.id)}
                    isLoading={feedback.isPending}
                  >
                    <Sparkles className="h-4 w-4" />
                    Get AI feedback
                  </Button>
                </div>
                {feedback.data && <FeedbackPanel feedback={feedback.data} />}
                <ResumeProfileView profile={detail.profile} />
              </motion.div>
            ) : (
              <Card>
                <CardContent className="flex min-h-[300px] flex-col items-center justify-center gap-2 text-center">
                  <FileText className="h-8 w-8 text-muted" />
                  <p className="font-medium">No resume selected</p>
                  <p className="text-sm text-muted">
                    Upload a resume to see its structured profile here.
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

export default function ResumePage() {
  return (
    <Protected>
      <ResumeWorkspace />
    </Protected>
  );
}
