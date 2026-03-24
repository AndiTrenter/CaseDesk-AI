# CaseDesk AI - Product Requirements Document

## Original Problem Statement
Self-hosted, privacy-focused, modular web application for managing documents, emails, calendars, and cases with AI assistance. Must run entirely via Docker Compose with zero external dependencies.

## User Personas
- **Admin**: Sets up the system, manages users, configures AI providers and email accounts
- **Standard User**: Manages documents, cases, emails, tasks, calendar entries with AI assistance

## Core Requirements
1. **100% Self-Hosted**: Docker Compose, no runtime dependencies on Emergent or external platforms
2. **Setup Wizard**: Admin creation, AI provider config (Ollama local / OpenAI external), language selection
3. **Multi-Tenancy**: Multiple users with strictly separated data, admin-invitable via email links
4. **Document Processing**: Upload (PDF, DOCX, images), OCR, intelligent renaming, semantic search, case association
5. **Email Processing**: IMAP fetch, AI analysis, attachment import, deadline detection, auto-task creation
6. **AI Assistant**: Context-aware, document-aware, multilingual, budget plan creation from real data
7. **Response Generation**: AI-drafted letters in PDF/DOCX, with document attachments as download package
8. **Proactive AI**: Daily briefing, document suggestions, case analysis
9. **Calendar & Tasks**: Task management with priorities and deadlines, calendar events
10. **Data Export**: Full ZIP export with all documents and metadata
11. **No Branding**: No Emergent watermarks

## Tech Stack
- **Backend**: FastAPI, Python 3.11
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Database**: MongoDB
- **AI**: Ollama (local) / OpenAI (external)
- **OCR**: Tesseract via separate microservice
- **Deployment**: Docker Compose (MongoDB, Backend, Frontend/Nginx, OCR, Ollama)

## What's Been Implemented

### Completed Features
- [x] Setup Wizard with admin creation
- [x] JWT authentication with multi-user support
- [x] User invitation system (email links)
- [x] Document upload with OCR processing
- [x] Intelligent document renaming
- [x] Document semantic/full-text search
- [x] Multi-select documents -> assign to case
- [x] Upload/link documents from case view
- [x] Case management with detail tabs
- [x] AI abstraction layer (Ollama + OpenAI)
- [x] AI Chat with full document knowledge and German language support
- [x] AI Chat with document download links (referenced documents)
- [x] Proactive AI: Daily briefing, document suggestions, case analysis
- [x] Response generation in PDF/DOCX format with attachments
- [x] IMAP email fetch with auto AI processing and deadline task creation
- [x] SMTP configuration UI
- [x] Data export as ZIP with all documents
- [x] Light/Dark theme toggle
- [x] Docker Compose self-hosted setup (MongoDB, Nginx, OCR, Ollama)
- [x] AI language fix (reads from user_settings, syncs to user doc)

### P2 Backlog
- [ ] Calendar/Task Automation: Auto-create calendar events from AI-detected deadlines
- [ ] Refine User Role Model: Admin vs Standard User permissions
- [ ] Backend API refactoring: Split monolithic server.py into domain routers

## Key Architecture
```
docker-compose.yml
├── mongodb (Port 27017) - Document DB
├── backend (Port 8001) - FastAPI REST API
├── frontend (Port 80) - React + Nginx (proxies /api to backend)
├── ocr (Port 8002) - Tesseract OCR microservice
└── ollama (Port 11434) - Local LLM server
```

## Credentials
- Admin: admin@casedesk.app / admin123
