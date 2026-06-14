# AI Interview Copilot

> Your personal recruiter, interviewer, and mentor — resume analysis, **real ML** candidate-fit prediction, a RAG-powered mentor, and realistic AI interview simulation.

AI Interview Copilot helps students and job seekers prepare for technical
interviews. Upload a resume and a job description, and the system analyzes the
fit using **actual machine-learning models** (scikit-learn / XGBoost with SHAP
explainability), surfaces skill gaps, generates a personalized learning roadmap,
and runs realistic AI interviews with scored feedback.

---

## ✨ Features

| Area | What it does |
|------|--------------|
| **Resume Analysis** | Extracts skills, projects, education, experience, certifications from PDF into a structured profile. |
| **Job Description Analysis** | Extracts required/preferred skills, technologies, responsibilities, and experience. |
| **Candidate Matching** | Match score, missing skills, strength and weak areas. |
| **ML — Candidate Fit Predictor** | XGBoost classifier → fit score, interview probability, hiring recommendation, with SHAP explanations. |
| **ML — Interview Success Predictor** | Predicts interview success probability from resume + match + mock-interview features. |
| **RAG Mentor** | Context-aware Q&A grounded in your resume and the job description (ChromaDB). |
| **Learning Roadmap** | Weekly plan, skills to learn, resources. |
| **AI Interview Simulator** | Dynamic technical interviews with follow-ups across SWE / Full-Stack / AI / Data roles. |
| **Interview Evaluation** | Scores technical accuracy, communication, completeness, confidence. |
| **Analytics Dashboard** | Match score, hiring probability, skill gaps, learning progress. |

---

## 🏗️ Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript (strict), Tailwind CSS, Framer Motion, Recharts, TanStack Query, Zustand
- **Backend:** FastAPI, Pydantic v2, Motor (async MongoDB)
- **ML:** scikit-learn, XGBoost, SHAP
- **Vector DB:** ChromaDB
- **Database:** MongoDB
- **LLM:** OpenAI / Anthropic (with a deterministic local fallback so the app runs offline)
- **Deployment:** Docker + docker-compose

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for the full system design.

---

## 📁 Project Structure

```
AI-Interview-Copilot/
├─ backend/            # FastAPI app, ML pipelines, RAG, services
│  ├─ app/
│  │  ├─ core/         # config, logging, errors, middleware
│  │  ├─ db/           # MongoDB (Motor) client + indexes
│  │  ├─ routers/      # API endpoints
│  │  ├─ services/     # parsing, matching, llm, rag, interview
│  │  └─ ml/           # features, datagen, training, registry
│  ├─ tests/
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/           # Next.js app
│  ├─ app/             # App Router pages
│  ├─ components/      # design system + feature components
│  ├─ lib/             # api client, utils
│  └─ Dockerfile
├─ docker-compose.yml
└─ ARCHITECTURE.md
```

---

## 🚀 Quick Start

### Option A — Docker (recommended)

```bash
cp .env.example .env          # set JWT_SECRET_KEY (and LLM keys, optional)
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend docs → http://localhost:8000/docs
- Health → http://localhost:8000/api/v1/health

### Option B — Local development

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

> **MongoDB** must be running locally (or via Docker) for full functionality.
> The backend boots even without it and reports `degraded` on `/api/v1/ready`.

---

## 🔐 Environment Variables

Backend (`backend/.env`) — see `backend/.env.example` for the full list.
Frontend (`frontend/.env.local`) — `NEXT_PUBLIC_API_BASE_URL`.

LLM keys are optional: when absent, the app uses a deterministic local engine so
every feature remains demonstrable offline.

---

## 🧭 Development Roadmap (Milestones)

1. **Foundation** ✅ — project setup, Docker, folder structure
2. Authentication — JWT, registration, login, protected routes
3. Resume upload + parsing
4. Job description analysis
5. **ML pipeline** — dataset, features, candidate-fit model, evaluation
6. Resume matching engine
7. RAG system (ChromaDB)
8. AI mentor (feedback, roadmap)
9. Interview simulator
10. Interview evaluation
11. Analytics dashboard
12. Production release (v1.0)

---

## 📝 License

Educational / portfolio project.
