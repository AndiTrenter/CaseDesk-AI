# CaseDesk AI - Product Requirements Document

## Original Problem Statement
Self-hosted, privacy-focused, modular web application for managing documents, emails, calendars, and cases with AI assistance. Must run entirely via Docker Compose with zero external dependencies.

## User Personas
- **Admin**: Sets up the system, manages users, configures AI providers and email accounts
- **Standard User**: Manages own documents, cases, emails, tasks, calendar entries with AI assistance. Cannot access system settings or user management.

## Tech Stack
- **Backend**: FastAPI, Python 3.11, Motor (MongoDB async)
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Database**: MongoDB
- **AI**: Ollama (local) / OpenAI (external)
- **OCR**: Tesseract via microservice
- **Deployment**: Docker Compose (MongoDB, Backend, Frontend/Nginx, OCR, Ollama)

## Architecture
```
server.py              <- Slim main app (~100 lines), lifespan, router inclusion
deps.py                <- Shared: db, auth, helpers
background_sync.py     <- Automatic email sync every 60s
routers/
  auth.py              <- Login, register, users, invitations
  cases.py             <- Cases CRUD
  documents.py         <- Documents CRUD, upload, OCR, auto-deadlines
  tasks.py             <- Tasks CRUD
  events.py            <- Events CRUD, auto calendar from deadlines
  ai.py                <- AI Chat, proactive AI, daily briefing
  emails.py            <- Emails, IMAP fetch, auto processing
  settings.py          <- Settings (admin/user), dashboard, export
  correspondence.py    <- Response generation, drafts, correspondence
```

## Completed Features (as of 2026-03-24)
- [x] Setup Wizard with admin creation
- [x] JWT authentication with multi-user support
- [x] Role-based access control (Admin vs Standard User)
- [x] User invitation system (email links)
- [x] Document upload with OCR processing
- [x] Intelligent document renaming (Date-Sender-Type-Ref-Topic)
- [x] Document full-text + semantic search
- [x] Multi-select documents -> assign to case
- [x] Upload/link documents from case view
- [x] Case management with detail tabs (docs, correspondence, history)
- [x] AI abstraction layer (Ollama + OpenAI)
- [x] AI Chat with FULL document knowledge (reads entire OCR content)
- [x] AI Chat with referenced document download links
- [x] AI language fix (reads from user_settings, syncs both collections)
- [x] Proactive AI: Daily briefing, document suggestions, case analysis
- [x] Response generation in PDF/DOCX format with attachments
- [x] Calendar/Task automation: Deadlines auto-create tasks AND calendar events
- [x] IMAP email fetch with auto AI processing, task/event creation
- [x] Background email sync every 60 seconds (configurable per account)
- [x] SMTP configuration for sending emails
- [x] Data export as ZIP with all documents and metadata
- [x] Light/Dark theme toggle
- [x] Docker Compose self-hosted (MongoDB, Nginx proxy, OCR, Ollama)
- [x] Backend refactored from monolithic 2300-line server.py into 10 domain routers
- [x] No Emergent branding

## Credentials
- Admin: admin@casedesk.app / admin123
