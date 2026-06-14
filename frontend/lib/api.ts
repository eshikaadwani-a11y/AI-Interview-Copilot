import axios, { AxiosError, type AxiosInstance } from "axios";

/**
 * Centralised Axios client for the FastAPI backend.
 *
 * - Injects the JWT bearer token (when present) on every request.
 * - Normalises the backend error envelope into a consistent `ApiError`.
 * - Redirects to /login on 401 in the browser.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "aic_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export interface ApiError {
  error: string;
  detail: unknown;
  requestId?: string;
  status: number;
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: string; detail?: unknown; request_id?: string }>) => {
    const status = error.response?.status ?? 0;

    if (status === 401 && typeof window !== "undefined") {
      clearToken();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.assign("/login");
      }
    }

    const apiError: ApiError = {
      error: error.response?.data?.error ?? "network_error",
      detail: error.response?.data?.detail ?? error.message,
      requestId: error.response?.data?.request_id,
      status,
    };
    return Promise.reject(apiError);
  },
);
