"use client";

import { useMutation } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type {
  IngestResponse,
  MentorAnswer,
  Roadmap,
  ResumeFeedback,
} from "@/lib/types";

/** Generate resume feedback (strengths, gaps, suggestions). */
export function useResumeFeedback() {
  return useMutation<ResumeFeedback, ApiError, string>({
    mutationFn: async (resumeId) => {
      const { data } = await api.post<ResumeFeedback>(
        `/mentor/resume-feedback/${resumeId}`,
      );
      return data;
    },
  });
}

/** Generate a weekly learning roadmap from a match. */
export function useGenerateRoadmap() {
  return useMutation<Roadmap, ApiError, string>({
    mutationFn: async (matchId) => {
      const { data } = await api.post<Roadmap>(`/mentor/roadmap/${matchId}`);
      return data;
    },
  });
}

/** Ask the mentor a grounded question. */
export function useAskMentor() {
  return useMutation<MentorAnswer, ApiError, string>({
    mutationFn: async (question) => {
      const { data } = await api.post<MentorAnswer>("/mentor/ask", { question });
      return data;
    },
  });
}

/** Index a resume into the RAG store. */
export function useIngestResume() {
  return useMutation<IngestResponse, ApiError, string>({
    mutationFn: async (resumeId) => {
      const { data } = await api.post<IngestResponse>(
        `/rag/ingest/resume/${resumeId}`,
      );
      return data;
    },
  });
}

/** Index a job into the RAG store. */
export function useIngestJob() {
  return useMutation<IngestResponse, ApiError, string>({
    mutationFn: async (jobId) => {
      const { data } = await api.post<IngestResponse>(`/rag/ingest/job/${jobId}`);
      return data;
    },
  });
}
