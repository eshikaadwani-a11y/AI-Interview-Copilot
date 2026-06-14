"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { api, getToken, type ApiError } from "@/lib/api";
import type {
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  UserPublic,
} from "@/lib/types";
import { useAuthStore } from "@/store/auth";

/** Register a new account. */
export function useRegister() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation<TokenResponse, ApiError, RegisterPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<TokenResponse>("/auth/register", payload);
      return data;
    },
    onSuccess: (data) => setSession(data.access_token, data.user),
  });
}

/** Authenticate an existing account. */
export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation<TokenResponse, ApiError, LoginPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<TokenResponse>("/auth/login", payload);
      return data;
    },
    onSuccess: (data) => setSession(data.access_token, data.user),
  });
}

/** Fetch and sync the current user; used to guard protected pages. */
export function useCurrentUser() {
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery<UserPublic, ApiError>({
    queryKey: ["currentUser"],
    enabled: typeof window !== "undefined" && Boolean(getToken()),
    queryFn: async () => {
      const { data } = await api.get<UserPublic>("/auth/me");
      setUser(data);
      return data;
    },
  });
}

/** Convert an ApiError detail into a human-friendly message. */
export function formatApiError(error: ApiError | null): string | null {
  if (!error) return null;
  if (typeof error.detail === "string") return error.detail;
  if (Array.isArray(error.detail) && error.detail.length > 0) {
    const first = error.detail[0] as { msg?: string };
    return first?.msg ?? "Validation error";
  }
  return "Something went wrong. Please try again.";
}
