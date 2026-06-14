# Deployment Guide

This guide covers running AI Interview Copilot locally and deploying it to
production.

---

## 1. Prerequisites

- **Docker** + **Docker Compose** (recommended), or
- **Python 3.11**, **Node.js 22**, and a **MongoDB** instance for local dev.

---

## 2. Configuration

Copy the example env files and fill in values:

```bash
cp .env.example .env                      # root (docker-compose)
cp backend/.env.example backend/.env      # backend (local dev)
cp frontend/.env.local.example frontend/.env.local
```

### Key variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `JWT_SECRET_KEY` | root / backend | **Required.** Use a long random string in production. |
| `MONGODB_URI` | backend | MongoDB connection string. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | backend | Optional. Enables generative LLM features; without them the app uses the deterministic local engine. |
| `EMBEDDING_PROVIDER` | backend | `local` (offline) or `openai`. |
| `LLM_PROVIDER` | backend | `auto` \| `openai` \| `anthropic` \| `local`. |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Base URL of the backend API (includes `/api/v1`). |

> **Generate a strong secret:** `python -c "import secrets; print(secrets.token_urlsafe(48))"`

---

## 3. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

This starts:
- **MongoDB** (with a persistent volume)
- **Backend** (FastAPI) on `:8000` — the ML models are **trained at image build**, so the API serves a ready model immediately.
- **Frontend** (Next.js) on `:3000`

Open:
- App → http://localhost:3000
- API docs → http://localhost:8000/docs
- Health → http://localhost:8000/api/v1/health

Stop & clean: `docker compose down` (add `-v` to remove volumes).

---

## 4. Local development (without Docker)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train          # train both ML models -> backend/models/
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Ensure MongoDB is running (e.g. `docker run -p 27017:27017 mongo:7`).

---

## 5. Machine-learning models

Two models are trained by `python -m app.ml.train`:

1. **Candidate Fit Predictor** (`fit_predictor.*`)
2. **Interview Success Predictor** (`interview_predictor.*`)

- With scikit-learn/XGBoost installed → XGBoost models (`.joblib`) + SHAP.
- Without them → pure-Python logistic regression (`.json`), no external deps.

Artifacts and `*_metadata.json` (metrics, feature importance) are written to
`MODELS_DIR` (default `backend/models/`). Re-run training to refresh.

---

## 6. Production notes

- **Secrets:** never commit real `.env` files. Inject secrets via your platform's secret manager.
- **CORS:** set `CORS_ORIGINS` to your frontend's public origin.
- **MongoDB:** use a managed instance (Atlas) with auth + TLS; set `MONGODB_URI` accordingly.
- **Vector store:** ChromaDB persists under `CHROMA_PERSIST_DIR`; mount a durable volume. For scale, point embeddings/store at a managed vector DB.
- **Scaling:** run the backend under a process manager (e.g. `uvicorn` workers behind gunicorn or a load balancer). The app is stateless apart from Mongo/Chroma.
- **Frontend:** `npm run build && npm start`, or deploy to Vercel and set `NEXT_PUBLIC_API_BASE_URL` to the backend URL.
- **Health checks:** wire your orchestrator to `GET /api/v1/health` (liveness) and `GET /api/v1/ready` (readiness).

---

## 7. CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR:
- **Backend:** compile check + `pytest` (lightweight deps).
- **Frontend:** `tsc` type-check, ESLint, and a production `next build`.
