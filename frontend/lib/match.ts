"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { MatchDetail, MatchSummary } from "@/lib/types";

const MATCHES_KEY = ["matches"] as const;

export interface MatchRequest {
  resume_id: string;
  job_id: string;
}

/** Run a resume-vs-job match through the ML model. */
export function useCreateMatch() {
  const qc = useQueryClient();
  return useMutation<MatchDetail, ApiError, MatchRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post<MatchDetail>("/match", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: MATCHES_KEY }),
  });
}

/** List the user's match history. */
export function useMatches() {
  return useQuery<MatchSummary[], ApiError>({
    queryKey: MATCHES_KEY,
    queryFn: async () => {
      const { data } = await api.get<MatchSummary[]>("/match");
      return data;
    },
  });
}

/** Fetch a single match result. */
export function useMatch(matchId: string | null) {
  return useQuery<MatchDetail, ApiError>({
    queryKey: ["match", matchId],
    enabled: Boolean(matchId),
    queryFn: async () => {
      const { data } = await api.get<MatchDetail>(`/match/${matchId}`);
      return data;
    },
  });
}
