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


// ── Match types (Milestone 6) ─────────────────────────────────

export interface Contribution {
  feature: string;
  label: string;
  value: number;
  contribution: number;
}

export interface MatchPrediction {
  fit_score: number;
  interview_probability: number;
  recommendation: string;
  backend: string;
  explanation: Contribution[];
}

export interface SkillGap {
  missing_required: string[];
  missing_preferred: string[];
  strengths: string[];
  weak_areas: string[];
}

export interface RecommendationItem {
  skill: string;
  priority: string;
  reason: string;
}

export interface MatchSummary {
  id: string;
  resume_filename: string;
  job_title: string | null;
  fit_score: number;
  recommendation: string;
  created_at: string;
}

export interface MatchDetail {
  id: string;
  resume_id: string;
  job_id: string;
  resume_filename: string;
  job_title: string | null;
  features: Record<string, number>;
  prediction: MatchPrediction;
  skill_gap: SkillGap;
  recommendations: RecommendationItem[];
  created_at: string;
}


// ── Mentor types (Milestone 8) ────────────────────────────────

export interface Citation {
  source_type: string;
  source_id: string;
  title: string | null;
  snippet: string;
  score: number;
}

export interface MentorAnswer {
  answer: string;
  provider: string;
  citations: Citation[];
}

export interface ResumeFeedback {
  overall_summary: string;
  strengths: string[];
  missing_sections: string[];
  suggestions: string[];
  provider: string;
}

export interface RoadmapResource {
  title: string;
  url: string;
}

export interface RoadmapWeek {
  week: number;
  focus: string;
  skills: string[];
  resources: RoadmapResource[];
}

export interface Roadmap {
  id: string;
  match_id: string;
  job_title: string | null;
  target_fit_score: number | null;
  weeks: RoadmapWeek[];
  created_at: string;
}

export interface IngestResponse {
  source_type: string;
  source_id: string;
  title: string | null;
  indexed_chunks: number;
}


// ── Interview types (Milestone 9) ─────────────────────────────

export interface QuestionPublic {
  index: number;
  category: string;
  difficulty: string | null;
  text: string;
  type: string; // "base" | "followup"
}

export interface QuestionFull extends QuestionPublic {
  answer: string | null;
}

export interface InterviewState {
  id: string;
  mode: string;
  mode_label: string;
  status: string;
  total: number;
  answered: number;
  current_index: number;
  current_question: QuestionPublic | null;
  finished: boolean;
}

export interface InterviewSummary {
  id: string;
  mode: string;
  mode_label: string;
  status: string;
  total: number;
  answered: number;
  created_at: string;
}

export interface InterviewDetail {
  id: string;
  mode: string;
  mode_label: string;
  status: string;
  questions: QuestionFull[];
  created_at: string;
  completed_at: string | null;
}

export interface InterviewStartPayload {
  mode: string;
  categories?: string[] | null;
  num_questions?: number;
  resume_id?: string | null;
  job_id?: string | null;
}
