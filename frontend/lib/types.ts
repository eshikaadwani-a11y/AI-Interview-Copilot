/** Shared API types mirrored from the backend Pydantic models. */

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}


// ── Resume types (Milestone 3) ────────────────────────────────

export interface Contact {
  name: string | null;
  email: string | null;
  phone: string | null;
  links: string[];
}

export interface ExperienceItem {
  title: string | null;
  company: string | null;
  start: string | null;
  end: string | null;
  months: number;
  bullets: string[];
}

export interface EducationItem {
  degree: string | null;
  institution: string | null;
  year: number | null;
  gpa: string | null;
}

export interface ProjectItem {
  name: string;
  description: string | null;
  tech: string[];
  bullets: string[];
}

export interface ResumeProfile {
  contact: Contact;
  summary: string | null;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
  certifications: string[];
  total_experience_months: number;
}

export interface ResumeSummary {
  id: string;
  filename: string;
  skill_count: number;
  total_experience_months: number;
  created_at: string;
}

export interface ResumeDetail {
  id: string;
  filename: string;
  profile: ResumeProfile;
  created_at: string;
}


// ── Job types (Milestone 4) ───────────────────────────────────

export interface JobProfile {
  title: string | null;
  required_skills: string[];
  preferred_skills: string[];
  technologies: string[];
  responsibilities: string[];
  min_experience_years: number | null;
  education_required: string | null;
  seniority: string | null;
}

export interface JobSummary {
  id: string;
  title: string | null;
  company: string | null;
  required_skill_count: number;
  created_at: string;
}

export interface JobDetail {
  id: string;
  title: string | null;
  company: string | null;
  profile: JobProfile;
  created_at: string;
}

export interface JobCreatePayload {
  title?: string | null;
  company?: string | null;
  description: string;
}
