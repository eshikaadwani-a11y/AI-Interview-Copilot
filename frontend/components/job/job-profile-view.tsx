"use client";

import { Briefcase, GraduationCap, ListChecks } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { JobDetail } from "@/lib/types";

/** Renders a structured view of a parsed job profile. */
export function JobProfileView({ job }: { job: JobDetail }) {
  const { profile } = job;

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardContent className="flex flex-col gap-2 pt-6">
          <h2 className="text-xl font-semibold">
            {job.title ?? profile.title ?? "Job description"}
          </h2>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted">
            {job.company && <span>{job.company}</span>}
            {profile.seniority && <Badge tone="primary">{profile.seniority}</Badge>}
            {profile.min_experience_years != null && (
              <Badge>{profile.min_experience_years}+ yrs</Badge>
            )}
            {profile.education_required && (
              <span className="inline-flex items-center gap-1.5">
                <GraduationCap className="h-3.5 w-3.5" /> {profile.education_required}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <SkillCard
          title="Required skills"
          tone="primary"
          skills={profile.required_skills}
          empty="No required skills detected."
        />
        <SkillCard
          title="Preferred skills"
          tone="success"
          skills={profile.preferred_skills}
          empty="No preferred skills detected."
        />
      </div>

      {profile.responsibilities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ListChecks className="h-4 w-4 text-primary" /> Responsibilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1.5 pl-4 text-sm text-muted">
              {profile.responsibilities.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {profile.technologies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-4 w-4 text-primary" /> Technologies mentioned
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {profile.technologies.map((t) => (
              <Badge key={t}>{t}</Badge>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SkillCard({
  title,
  tone,
  skills,
  empty,
}: {
  title: string;
  tone: "primary" | "success";
  skills: string[];
  empty: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {skills.length > 0 ? (
          skills.map((s) => (
            <Badge key={s} tone={tone}>
              {s}
            </Badge>
          ))
        ) : (
          <p className="text-sm text-muted">{empty}</p>
        )}
      </CardContent>
    </Card>
  );
}
