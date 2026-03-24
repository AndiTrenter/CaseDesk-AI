# CaseDesk AI - Product Requirements Document

## Original Problem Statement
Self-hosted, privacy-focused, modular web application for managing documents, emails, calendars, and cases with AI assistance. Must run entirely via Docker Compose with zero external dependencies. Installable on Unraid via Docker/Community Applications.

## Repository
https://github.com/AndiTrenter/CaseDesk-AI

## Tech Stack
- **Backend**: FastAPI, Python 3.11, Motor (MongoDB async)
- **Frontend**: React, Tailwind CSS, Shadcn UI, Nginx (production)
- **Database**: MongoDB 7
- **AI**: Ollama (local, optional) / OpenAI (external, optional)
- **OCR**: Tesseract via microservice
- **CI/CD**: GitHub Actions → GHCR (ghcr.io/anditrenter/casedesk-ai/*)
- **Deployment**: Docker Compose, Unraid Template

## Architecture (Refactored)
```
server.py              <- Slim main app (~100 lines)
deps.py                <- Shared: db, auth, helpers
background_sync.py     <- Auto email sync every 60s
routers/
  auth.py, cases.py, documents.py, tasks.py, events.py,
  ai.py, emails.py, settings.py, correspondence.py
```

## All Completed Features
- [x] Setup Wizard, JWT auth, multi-user with roles (Admin/User)
- [x] User invitation system via email links
- [x] Document upload + OCR + intelligent renaming + semantic search
- [x] Multi-select documents → assign to case
- [x] Case management with tabs (docs, correspondence, history)
- [x] AI Chat with FULL document knowledge + referenced doc downloads
- [x] AI language fix (de/en/fr/es from user_settings)
- [x] Proactive AI: Daily briefing, document suggestions, case analysis
- [x] Response generation in PDF/DOCX with attachments
- [x] Calendar/Task automation from AI-detected deadlines
- [x] IMAP email fetch + auto AI processing + task/event creation
- [x] Background email sync (configurable per account)
- [x] SMTP config for sending
- [x] Data export as ZIP with all documents
- [x] Light/Dark theme
- [x] Docker self-hosted: MongoDB, Nginx proxy, OCR, Ollama (optional)
- [x] Ollama optional via Docker profiles (--profile ollama/gpu)
- [x] Frontend port variable (FRONTEND_PORT, default 9090)
- [x] Google Fonts localized (no external CDN)
- [x] Backend tests (21 pytest tests, CI-ready)
- [x] GitHub Actions: build + push to GHCR (backend, frontend, ocr)
- [x] docker-compose.unraid.yml with /mnt/user/appdata paths
- [x] Unraid Community App XML template
- [x] README.md in German with full install guide
- [x] .env.example with all variables documented
- [x] Backend refactored from 2300-line monolith into 10 domain routers
- [x] No Emergent branding, no external dependencies

## Credentials
- Admin: admin@casedesk.app / admin123
