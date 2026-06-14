"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserPublic } from "@/lib/types";
import { clearToken, setToken } from "@/lib/api";

/**
 * Client-side auth state. The JWT itself lives in localStorage (managed by the
 * api client); this store keeps the decoded user profile and hydration flag so
 * the UI can react synchronously.
 */
interface AuthState {
  user: UserPublic | null;
  isAuthenticated: boolean;
  setSession: (token: string, user: UserPublic) => void;
  setUser: (user: UserPublic | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setSession: (token, user) => {
        setToken(token);
        set({ user, isAuthenticated: true });
      },
      setUser: (user) => set({ user, isAuthenticated: Boolean(user) }),
      logout: () => {
        clearToken();
        set({ user: null, isAuthenticated: false });
      },
    }),
    { name: "aic_auth", partialize: (state) => ({ user: state.user }) },
  ),
);
