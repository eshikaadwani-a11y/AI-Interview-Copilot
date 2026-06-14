"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { ResumeDetail, ResumeSummary } from "@/lib/types";

const RESUMES_KEY = ["resumes"] as const;

/** List the current user's resumes. */
export function useResumes() {
  return useQuery<ResumeSummary[], ApiError>({
    queryKey: RESUMES_KEY,
    queryFn: async () => {
      const { data } = await api.get<ResumeSummary[]>("/resumes");
      return data;
    },
  });
}

/** Fetch a single resume's full profile. */
export function useResume(resumeId: string | null) {
  return useQuery<ResumeDetail, ApiError>({
    queryKey: ["resume", resumeId],
    enabled: Boolean(resumeId),
    queryFn: async () => {
      const { data } = await api.get<ResumeDetail>(`/resumes/${resumeId}`);
      return data;
    },
  });
}

/** Upload a PDF resume (multipart). */
export function useUploadResume() {
  const qc = useQueryClient();
  return useMutation<ResumeDetail, ApiError, File>({
    mutationFn: async (file) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<ResumeDetail>("/resumes", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: RESUMES_KEY }),
  });
}

/** Delete a resume. */
export function useDeleteResume() {
  const qc = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: async (resumeId) => {
      await api.delete(`/resumes/${resumeId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: RESUMES_KEY }),
  });
}
