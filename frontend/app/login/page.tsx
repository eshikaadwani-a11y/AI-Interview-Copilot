"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatApiError, useLogin } from "@/lib/auth";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate(
      { email, password },
      { onSuccess: () => router.replace("/dashboard") },
    );
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to continue preparing for your interviews."
      footer={
        <span>
          New here?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Create an account
          </Link>
        </span>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        {login.isError && (
          <p className="text-sm text-danger">{formatApiError(login.error)}</p>
        )}

        <Button type="submit" size="lg" isLoading={login.isPending}>
          Sign in
        </Button>
      </form>
    </AuthShell>
  );
}
