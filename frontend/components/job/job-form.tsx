"use client";

import { useState, type FormEvent } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatApiError } from "@/lib/auth";
import { useCreateJob } from "@/lib/jobs";
import type { JobDetail } from "@/lib/types";

interface JobFormProps {
  onCreated?: (job: JobDetail) => void;
}

/** Form for submitting a job description (paste text + optional title/company). */
export function JobForm({ onCreated }: JobFormProps) {
  const createJob = useCreateJob();
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    createJob.mutate(
      {
        title: title.trim() || null,
        company: company.trim() || null,
        description,
      },
      {
        onSuccess: (job) => {
          setDescription("");
          onCreated?.(job);
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Analyze a job description</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="title">Title (optional)</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Senior ML Engineer"
              />
            </div>
            <div>
              <Label htmlFor="company">Company (optional)</Label>
              <Input
                id="company"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="Acme AI"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="description">Job description</Label>
            <Textarea
              id="description"
              required
              minLength={30}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste the full job description here…"
            />
          </div>

          {createJob.isError && (
            <p className="text-sm text-danger">{formatApiError(createJob.error)}</p>
          )}

          <Button type="submit" isLoading={createJob.isPending}>
            <Sparkles className="h-4 w-4" />
            Analyze job
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
