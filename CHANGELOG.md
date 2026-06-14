# Changelog

All notable changes to AI Interview Copilot.

## v1.0.0 — Initial release

A production-grade AI interview-preparation platform with real machine learning
at its core.

### Features
- **Authentication** — JWT register/login, protected routes, profile.
- **Resume analysis** — PDF upload + deterministic parser (skills, experience,
  projects, education, certifications) + AI feedback.
- **Job description analysis** — required vs preferred skills, responsibilities,
  seniority, experience, education.
- **Candidate matching** — ML candidate-fit prediction with skill-gap detection,
  recommendations, and SHAP-style explanations.
- **Machine learning (2 models)**
  - *Candidate Fit Predictor* — XGBoost (+ RandomForest baseline) with a
    pure-Python logistic-regression fallback; calibrated probabilities + SHAP.
  - *Interview Success Predictor* — uses interview scores + match score +
    resume features; persists version, confidence, and feature importance.
- **RAG system** — chunking, local/OpenAI embeddings, ChromaDB / in-memory
  store, grounded retrieval with citations.
- **AI mentor** — resume feedback, learning roadmap generation, grounded chat.
- **Interview simulator** — dynamic, categorised questions across roles with
  adaptive follow-ups.
- **Interview evaluation** — per-answer rubric scoring with concept-level
  explanations, performance report, and success prediction.
- **Analytics dashboard** — readiness gauges, score trends, skill-gap and
  category-score charts.

### Engineering
- FastAPI + Pydantic v2 + async MongoDB (Motor).
- Next.js 14 (TypeScript strict) + Tailwind + Framer Motion + Recharts.
- Offline-capable: deterministic local LLM/embeddings fallbacks so the full
  product runs without external API keys.
- Dockerised (frontend + backend + MongoDB); models trained at image build.
- GitHub Actions CI (backend pytest, frontend type-check/lint/build).
- Test suites for parsing, ML, RAG, mentor, interview, and evaluation logic.
