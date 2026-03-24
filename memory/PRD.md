# CaseDesk AI - Product Requirements Document

## Original Problem Statement
Self-hosted, privacy-focused, modular web application for managing documents, emails, calendars, and cases with AI assistance. Must run entirely independently via Docker Compose on an Unraid server.

## Core Requirements
- 100% Self-Hosted & Deployable (Docker Compose / Unraid)
- Contextual & Personalized AI
- Multi-tenancy with admin/user roles
- Document processing (upload, OCR, AI analysis, search)
- Email processing (IMAP/SMTP)
- AI-powered response generation (PDF/DOCX)

## Architecture
- **Backend**: FastAPI + Motor (async MongoDB)
- **Frontend**: React + Tailwind + Shadcn UI
- **Database**: MongoDB
- **AI**: OpenAI (default) / Ollama (optional)
- **OCR**: Tesseract + PyPDF2 fallback (built-in) + external OCR service (Docker)
- **Deployment**: Docker Compose (dev/prod), GitHub Actions CI/CD, GHCR, Unraid template

## What's Been Implemented

### Core Features (Complete)
- Setup Wizard, Auth (JWT), Admin/User roles
- Document Management (upload, OCR, AI analysis, tags, search)
- Case Management (CRUD, tabs, document linking)
- Email (IMAP/SMTP integration, background sync)
- Calendar & Tasks
- AI Chat (general assistant)
- PDF/DOCX response generation
- Data Export (ZIP archive)
- Settings (AI provider, language, theme)

### P0 Features (Completed - March 2024)
- **Contextual AI Chat**: Users can ask AI about specific documents/cases from their views
  - "KI fragen" dropdown option on Documents page
  - "KI fragen" button on Case Detail page
  - Context banner showing document/case name in AI Chat
  - Full document content injected into AI context
- **Persistent AI Memory (User Profile)**:
  - AI extracts personal facts from conversations automatically
  - Facts stored in `ai_profiles` MongoDB collection
  - Profile injected into system prompt for personalized responses
  - Memory panel in AI Chat UI showing learned facts
  - CRUD for managing individual facts
- **Fallback OCR (Tesseract)**:
  - Built-in OCR for when external OCR service is unavailable
  - PyPDF2 for text-embedded PDFs + Tesseract for scanned PDFs
  - Batch reprocess endpoint for existing documents
  - German + English language support

### Deployment & DevOps (Complete)
- Docker Compose (dev + Unraid production)
- GitHub Actions → GHCR image publishing
- Unraid XML template
- No external dependencies (emergentintegrations removed)
- Localized fonts

## Credentials
- Email: andi.trenter@gmail.com
- Password: Speedy@181279

## Prioritized Backlog

### P2 - Future Tasks
- Multilingual UI (i18n translation)
- Healthcheck Dashboard (service status monitoring)

## Key API Endpoints
- `POST /api/ai/chat` - AI chat (supports document_id, case_id params)
- `GET /api/ai/profile` - Get user's AI memory profile
- `DELETE /api/ai/profile/facts/{index}` - Delete specific fact
- `DELETE /api/ai/profile` - Clear entire memory
- `POST /api/documents/batch-reprocess` - Reprocess all unprocessed documents
- `POST /api/documents/upload` - Upload with auto OCR + AI analysis
- `GET /api/documents/{id}` - Get document details
- `POST /api/documents/{id}/reprocess` - Reprocess single document

## DB Collections
- `users`, `user_settings`, `system_settings`
- `documents`, `cases`, `tasks`, `events`
- `chat_messages`, `emails`, `mail_accounts`
- `ai_profiles` (NEW - user fact storage)
- `audit_log`
