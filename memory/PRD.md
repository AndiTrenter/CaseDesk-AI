# CaseDesk AI - Product Requirements Document

## Repository
https://github.com/AndiTrenter/CaseDesk-AI

## Deploy-Readiness Checklist (alle erledigt)
- [x] `.env.example` im Root mit allen Variablen (Ports, Keys, Ollama)
- [x] `/api/health` direkt in `server.py` + Docker Healthcheck mit `start_period`
- [x] Frontend-Port variabel: `${FRONTEND_PORT:-9090}:80`
- [x] Ollama optional: Docker Profiles (`--profile ollama` / `--profile gpu`)
- [x] Keine externe Abhängigkeit: `@emergentbase/visual-edits` entfernt, Fonts lokal
- [x] 21 Pytest-Tests auf echtem API-Stand, CI-ready
- [x] GitHub Actions Workflow: Build + Push zu GHCR (backend, frontend, ocr)
- [x] `docker-compose.unraid.yml` mit `/mnt/user/appdata/casedesk/` Pfaden
- [x] Unraid Community App XML Template

## Tech Stack
- **Backend**: FastAPI, Python 3.11, Motor (MongoDB async)
- **Frontend**: React, Tailwind CSS, Shadcn UI, Nginx (production)
- **Database**: MongoDB 7
- **AI**: Ollama (local, optional) / OpenAI (external, optional)
- **OCR**: Tesseract via microservice
- **CI/CD**: GitHub Actions → GHCR
- **Deployment**: Docker Compose, Unraid Template

## Architecture
```
server.py              <- Main app + /api/health
deps.py                <- Shared: db, auth, helpers
background_sync.py     <- Auto email sync every 60s
routers/
  auth.py, cases.py, documents.py, tasks.py, events.py,
  ai.py, emails.py, settings.py, correspondence.py
```

## Docker Images
- `ghcr.io/anditrenter/casedesk-ai/backend:latest`
- `ghcr.io/anditrenter/casedesk-ai/frontend:latest`
- `ghcr.io/anditrenter/casedesk-ai/ocr:latest`

## Installation
```bash
git clone https://github.com/AndiTrenter/CaseDesk-AI.git
cd CaseDesk-AI
cp .env.example .env && nano .env
docker compose up -d                      # Nur OpenAI
docker compose --profile ollama up -d     # Mit lokalem Ollama
docker compose --profile gpu up -d        # Ollama + NVIDIA GPU
```

## Credentials
- Admin: admin@casedesk.app / admin123
