.PHONY: help up down build test train backend frontend lint typecheck

help:
	@echo "AI Interview Copilot — common commands"
	@echo "  make up         # docker compose up --build"
	@echo "  make down       # docker compose down"
	@echo "  make train      # train both ML models (backend/models)"
	@echo "  make test       # run backend tests"
	@echo "  make backend    # run backend dev server"
	@echo "  make frontend   # run frontend dev server"
	@echo "  make typecheck  # frontend type check"
	@echo "  make lint       # frontend lint"

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

train:
	cd backend && python -m app.ml.train

test:
	cd backend && pytest -q

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

typecheck:
	cd frontend && npm run typecheck

lint:
	cd frontend && npm run lint
