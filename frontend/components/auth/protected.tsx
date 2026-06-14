"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { getToken } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth";
import { useAuthStore } from "@/store/auth";

/**
 * Guards a subtree behind authentication. Verifies the token against
 * `/auth/me`; redirects to /login when there is no token or the token is
 * invalid. Shows a lightweight loading state while verifying.
 */
export function Protected({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isLoading, isError } = useCurrentUser();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasToken = typeof window !== "undefined" && Boolean(getToken());

  useEffect(() => {
    if (!hasToken || isError) {
      router.replace("/login");
    }
  }, [hasToken, isError, router]);

  if (!hasToken) return null;

  if (isLoading && !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
