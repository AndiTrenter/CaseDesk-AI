# CaseDesk AI - Product Requirements Document

## Original Problem Statement
Self-hosted, privacy-focused, modular web application for managing documents, emails, calendars, and cases with AI assistance. Must run entirely independently via Docker Compose on an Unraid server.

## Architecture
- **Backend**: FastAPI + Motor (async MongoDB)
- **Frontend**: React + Tailwind + Shadcn UI
- **Database**: MongoDB
- **AI**: OpenAI gpt-4o (default) / Ollama (optional)
- **OCR**: Tesseract + PyPDF2 fallback (built-in) + external OCR service (Docker)
- **Deployment**: Docker Compose (dev/prod), GitHub Actions CI/CD, GHCR, Unraid template

## What's Been Implemented

### Core Features (Complete)
- Setup Wizard, Auth (JWT), Admin/User roles, Invite Registration
- Document Management (upload, OCR, AI analysis, tags, search)
- Case Management (CRUD, tabs, document linking)
- Email (IMAP/SMTP integration, background sync)
- Calendar & Tasks
- AI Chat (general + contextual)
- PDF/DOCX response generation
- Data Export (ZIP archive)
- Settings (AI provider, language, theme)

### P0 Features (Complete)
- **Contextual AI Chat**: "KI fragen" on documents/cases, full content injection
- **Persistent AI Memory**: Auto fact extraction, profile injection, memory panel
- **Fallback OCR**: Tesseract + PyPDF2 for when external OCR unavailable

### New Features (March 25, 2026)
- **Healthcheck Dashboard**: System-Status page showing MongoDB, OCR, OpenAI, email, storage, tesseract status
- **KI-Wissen Page**: Dedicated page showing all AI knowledge (base profile, learned facts, analyzed docs, cases)
- **Document Upload Suggestions**: After upload, AI suggests tags and matching cases with checkbox selection
- **Calendar → Task**: "Auch als Aufgabe anlegen" checkbox when creating events
- **User Onboarding Wizard**: Step-by-step profile collection after registration (name, address, family, work)
- **Password-Protected Memory Deletion**: Deleting AI memory requires password + clear warnings about what gets deleted
- **Nightly Optimization (2 AM)**: Automated duplicate fact cleanup for all user profiles
- **AI Knowledge Completeness**: Onboarding profile data injected into AI context for comprehensive personalization

### Deployment & DevOps (Complete)
- Docker Compose (dev + Unraid production)
- GitHub Actions → GHCR image publishing
- Unraid XML template
- **NO external/emergent dependencies** - clean requirements.txt, all self-hosted

## Credentials
- Email: andi.trenter@gmail.com
- Password: Speedy@181279

## Prioritized Backlog
### P2 - Future
- Multilingual UI (i18n)

## Key API Endpoints
- `POST /api/ai/chat` - AI chat with document_id, case_id context
- `GET /api/ai/knowledge` - Everything AI knows about user
- `POST /api/ai/onboarding` - Save onboarding profile
- `POST /api/ai/profile/clear` - Password-protected memory deletion
- `GET /api/admin/health` - System health check
- `POST /api/documents/suggest-metadata` - AI tag/case suggestions
- `POST /api/events` - Create event with optional task creation (create_task=true)
- `POST /api/documents/batch-reprocess` - Reprocess all unprocessed documents

## DB Collections
- users, user_settings, system_settings
- documents, cases, tasks, events
- chat_messages, emails, mail_accounts
- ai_profiles, user_onboarding, system_logs
- audit_log
