# AI Interview Copilot — System Architecture

This document is the canonical design reference for the project. It is built
incrementally across milestones; sections are marked with the milestone that
delivers them.

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                               │
│  Next.js 14 (App Router) · TypeScript strict · Tailwind · Framer       │
│  State: TanStack Query (server state) + Zustand (UI state)             │
└───────────────▲──────────────────────────────────┬────────────────────┘
                │ HTTPS / JSON (JWT Bearer)         │ SSE (interview stream)
                ▼                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY — FastAPI                            │
│  Routers: /auth /resumes /jobs /match /ml /rag /mentor /interview      │
│  Middleware: JWT auth, CORS, request-id, structured logging, errors    │
│  Validation: Pydantic v2 schemas everywhere                            │
└───┬───────────┬───────────┬────────────┬────────────┬─────────────────┘
    ▼           ▼           ▼            ▼            ▼
 Resume      JD Analysis  ML Engine   RAG Engine   Interview
 Parser      Service      (sklearn /  (Chroma +    Engine +
 (PDF→struct)             XGBoost /   embeddings)  Evaluation
                          SHAP)
    └───────────┴───────────┼────────────┴────────────┘
                            ▼
        MongoDB (Motor) · ChromaDB (vectors) · Model registry (joblib)

        LLM Provider Abstraction: OpenAI | Anthropic | Local Fallback
```

**Principles:** modular services, async-first I/O, ML as a first-class service,
and a provider abstraction that isolates LLM vendor specifics.

> Note: this project is developed in an offline-friendly way. LLM calls fall
> back to a deterministic local engine and embeddings default to a local model,
> so the full product is demonstrable without external API access.

---

## 2. Database Schema (MongoDB)

Collections: `users`, `resumes`, `jobs`, `matches`, `interviews`, `roadmaps`,
`ml_models`, `rag_documents`. Indexes: unique `users.email`; `user_id` on
resumes/jobs/matches/interviews/roadmaps; compound `(resume_id, job_id)` on
matches. (Full field-level schema defined per milestone in `app/models`.)

---

## 3. ML Architecture

- **Model 1 — Candidate Fit Predictor:** XGBoost classifier (RandomForest
  baseline). Features: skill overlap (raw + TF-IDF weighted), experience match,
  education match, project relevance, certification relevance, seniority gap,
  preferred-skill overlap. Outputs: fit score, calibrated interview probability,
  recommendation bucket. SHAP `TreeExplainer` for per-prediction explanations.
- **Model 2 — Interview Success Predictor:** classifier over resume/match
  features + mock-interview scores → success probability.
- **Evaluation:** stratified split + CV; Accuracy, Precision, Recall, F1,
  ROC-AUC, confusion matrix; persisted to the model registry.

---

## 4. Model Training Pipeline

`feature_engineering → train_test_split (stratified) → Pipeline + CV →
evaluate → calibrate → SHAP explainer → persist (.joblib + metadata.json)`.
Reproducible via `python -m app.ml.train` with a fixed seed. Models loaded once
at API startup into an in-memory registry.

---

## 5. Dataset Strategy

Hybrid, documented approach: a **synthetic-but-grounded generator** built from a
curated taxonomy of real tech skills and role archetypes, with labels from a
transparent rule + controlled noise. Features are computed by the **same code**
used at inference (no train/serve skew). A loader interface allows dropping in
real labeled data later for retraining.

---

## 6. RAG Architecture

`Documents (resume, JD, Q-bank, resources) → token-aware chunking → embeddings
(local default / OpenAI optional) → ChromaDB (per-user metadata namespace) →
top-k retrieval → prompt assembly → LLM (or local fallback) → grounded answer`.

---

## 7. API Design

Versioned under `/api/v1`. Routers: `auth`, `resumes`, `jobs`, `match`, `ml`,
`rag`, `mentor`, `interview`, `dashboard`. All bodies/responses are Pydantic
models; consistent error envelope `{error, detail, request_id}`; JWT-protected
routes.

---

## 8. Folder Structure

See [README.md](./README.md#-project-structure).

---

## 9. UI Architecture

Dark-first design system (Button, Card, Badge, …) inspired by Linear / Vercel /
Perplexity. Routes: `/login`, `/register`, `/dashboard`, `/resume`, `/match`,
`/roadmap`, `/interview`, `/mentor`. TanStack Query for server cache; Zustand for
UI state; Recharts for analytics; Framer Motion for transitions.

---

## 10–12. Roadmap, MVP, Stretch Goals

- **Roadmap:** 12 milestones (see README).
- **MVP:** Milestones 1–6 + slim dashboard — auth, resume + JD analysis, real ML
  fit prediction with SHAP, matching engine, and score visualization.
- **Stretch:** real-data retraining loop + drift monitoring, voice interviews,
  org/cohort analytics for placement cells, S3/Redis, CI/CD, observability.

---

## Milestone Status

- [x] **M1 — Foundation:** Next.js + FastAPI + MongoDB wiring + Docker + structure
- [x] **M2 — Authentication:** JWT register/login, protected routes, `/auth/me`
- [x] **M3 — Resume upload + parsing:** PDF upload, deterministic parser, structured profile UI
- [x] **M4 — Job description analysis:** JD parser (required/preferred skills, responsibilities, seniority), structured viewer
- [x] **M5 — ML pipeline:** feature engineering, synthetic dataset, candidate-fit model (XGBoost prod + pure-Python fallback), evaluation, SHAP/explainability, model registry, `/ml` API
- [x] **M6 — Matching engine:** `/match` (ML fit score + interview probability + explanations), skill-gap detection, prioritized recommendations, match UI (score gauge, why-this-score, gaps)
- [x] **M7 — RAG system:** LLM provider abstraction (OpenAI/Anthropic + local fallback), local/OpenAI embeddings, ChromaDB + in-memory store, chunking, grounded retrieval, `/rag` API
- [x] **M8 — AI mentor:** resume feedback, learning roadmap generation (persisted), RAG-grounded mentor chat, mentor UI
- [x] **M9 — Interview simulator:** question bank, mode/category selection, dynamic follow-ups, session state machine, chat-style interview UI
- [ ] M10 — Interview evaluation
- [ ] M5 — ML pipeline
- [ ] M6 — Matching engine
- [ ] M7 — RAG system
- [ ] M8 — AI mentor
- [ ] M9 — Interview simulator
- [ ] M10 — Interview evaluation
- [ ] M11 — Analytics dashboard
- [ ] M12 — Production release
