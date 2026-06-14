"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { type ReactNode } from "react";

interface AuthShellProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

/** Centered card layout shared by the login and register pages. */
export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <main className="bg-mesh flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </span>
        <span className="font-semibold tracking-tight">Interview Copilot</span>
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-md rounded-2xl border border-border bg-surface/70 p-8 backdrop-blur-sm"
      >
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </motion.div>

      <div className="mt-6 text-sm text-muted">{footer}</div>
    </main>
  );
}
