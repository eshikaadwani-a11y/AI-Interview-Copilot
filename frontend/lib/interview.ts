"use client";

import { useMutation } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { InterviewReport, InterviewState, InterviewStartPayload } from "@/lib/types";

/** Start a new interview session. */
export function useStartInterview() {
  return useMutation<InterviewState, ApiError, InterviewStartPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<InterviewState>("/interview/start", payload);
      return data;
    },
  });
}

/** Submit an answer to the current question. */
export function useAnswerInterview() {
  return useMutation<InterviewState, ApiError, { id: string; answer: string }>({
    mutationFn: async ({ id, answer }) => {
      const { data } = await api.post<InterviewState>(`/interview/${id}/answer`, { answer });
      return data;
    },
  });
}

/** End the interview early. */
export function useFinishInterview() {
  return useMutation<InterviewState, ApiError, string>({
    mutationFn: async (id) => {
      const { data } = await api.post<InterviewState>(`/interview/${id}/finish`);
      return data;
    },
  });
}

/** Evaluate a completed interview and return the performance report. */
export function useEvaluateInterview() {
  return useMutation<InterviewReport, ApiError, string>({
    mutationFn: async (id) => {
      const { data } = await api.post<InterviewReport>(`/interview/${id}/evaluate`);
      return data;
    },
  });
}

export const INTERVIEW_MODES = [
  { value: "software_engineer", label: "Software Engineer" },
  { value: "full_stack", label: "Full Stack Developer" },
  { value: "ai_engineer", label: "AI Engineer" },
  { value: "data_scientist", label: "Data Scientist" },
] as const;
