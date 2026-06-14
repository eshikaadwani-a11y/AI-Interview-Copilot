"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { JobCreatePayload, JobDetail, JobSummary } from "@/lib/types";

const JOBS_KEY = ["jobs"] as const;

/** List the current user's job descriptions. */
export function useJobs() {
  return useQuery<JobSummary[], ApiError>({
    queryKey: JOBS_KEY,
    queryFn: async () => {
      const { data } = await api.get<JobSummary[]>("/jobs");
      return data;
    },
  });
}

/** Fetch a single job's full profile. */
export function useJob(jobId: string | null) {
  return useQuery<JobDetail, ApiError>({
    queryKey: ["job", jobId],
    enabled: Boolean(jobId),
    queryFn: async () => {
      const { data } = await api.get<JobDetail>(`/jobs/${jobId}`);
      return data;
    },
  });
}

/** Submit a job description as text. */
export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation<JobDetail, ApiError, JobCreatePayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<JobDetail>("/jobs", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: JOBS_KEY }),
  });
}

/** Delete a job description. */
export function useDeleteJob() {
  const qc = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: async (jobId) => {
      await api.delete(`/jobs/${jobId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: JOBS_KEY }),
  });
}
