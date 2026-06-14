"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type ApiError } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

/** Fetch aggregated dashboard analytics. */
export function useDashboardSummary() {
  return useQuery<DashboardSummary, ApiError>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => {
      const { data } = await api.get<DashboardSummary>("/dashboard/summary");
      return data;
    },
  });
}
