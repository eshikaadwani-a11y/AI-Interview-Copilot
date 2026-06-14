"use client";

import { Briefcase, FolderGit2, GraduationCap, Mail, Phone } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ResumeProfile } from "@/lib/types";

function formatMonths(total: number): string {
  const years = Math.floor(total / 12);
  const months = total % 12;
  if (years === 0) return `${months} mo`;
  if (months === 0) return `${years} yr`;
  return `${years} yr ${months} mo`;
}

/** Renders a fully structured view of a parsed resume profile. */
export function ResumeProfileView({ profile }: { profile: ResumeProfile }) {
  const { contact } = profile;

  return (
    <div className="flex flex-col gap-5">
      {/* Header / contact */}
      <Card>
        <CardContent className="flex flex-col gap-2 pt-6">
          <h2 className="text-xl font-semibold">{contact.name ?? "Candidate"}</h2>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
            {contact.email && (
              <span className="inline-flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5" /> {contact.email}
              </span>
            )}
            {contact.phone && (
              <span className="inline-flex items-center gap-1.5">
                <Phone className="h-3.5 w-3.5" /> {contact.phone}
              </span>
            )}
          </div>
          {contact.links.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {contact.links.map((link) => (
                <a
                  key={link}
                  href={link.startsWith("http") ? link : `https://${link}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-primary hover:underline"
                >
                  {link}
                </a>
              ))}
            </div>
          )}
          {profile.summary && (
            <p className="pt-2 text-sm leading-relaxed text-muted">{profile.summary}</p>
          )}
        </CardContent>
      </Card>

      {/* Stat strip */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Skills" value={String(profile.skills.length)} />
        <StatCard label="Experience" value={formatMonths(profile.total_experience_months)} />
        <StatCard label="Projects" value={String(profile.projects.length)} />
      </div>

      {/* Skills */}
      {profile.skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Skills</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {profile.skills.map((skill) => (
              <Badge key={skill} tone="primary">
                {skill}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Experience */}
      {profile.experience.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-4 w-4 text-primary" /> Experience
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            {profile.experience.map((exp, i) => (
              <div key={i} className="border-l-2 border-border pl-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium">{exp.title ?? "Role"}</p>
                  <span className="text-xs text-muted">
                    {[exp.start, exp.end].filter(Boolean).join(" – ")}
                  </span>
                </div>
                {exp.company && <p className="text-sm text-muted">{exp.company}</p>}
                {exp.bullets.length > 0 && (
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-muted">
                    {exp.bullets.map((b, j) => (
                      <li key={j}>{b}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Projects */}
      {profile.projects.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FolderGit2 className="h-4 w-4 text-primary" /> Projects
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {profile.projects.map((proj, i) => (
              <div key={i}>
                <p className="font-medium">{proj.name}</p>
                {proj.description && (
                  <p className="text-sm text-muted">{proj.description}</p>
                )}
                {proj.tech.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {proj.tech.map((t) => (
                      <Badge key={t}>{t}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Education + Certifications */}
      <div className="grid gap-4 md:grid-cols-2">
        {profile.education.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <GraduationCap className="h-4 w-4 text-primary" /> Education
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {profile.education.map((edu, i) => (
                <div key={i}>
                  <p className="font-medium">{edu.degree ?? "Degree"}</p>
                  <p className="text-sm text-muted">
                    {[edu.institution, edu.year].filter(Boolean).join(" · ")}
                    {edu.gpa ? ` · GPA ${edu.gpa}` : ""}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {profile.certifications.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Certifications</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-4 text-sm text-muted">
                {profile.certifications.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-5">
        <span className="text-2xl font-semibold">{value}</span>
        <span className="text-xs text-muted">{label}</span>
      </CardContent>
    </Card>
  );
}
