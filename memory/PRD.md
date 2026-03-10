# CaseDesk AI - Product Requirements Document

## Project Overview
**Name:** CaseDesk AI  
**Version:** 1.0.0  
**Type:** Self-hosted Document & Case Management with AI Support  
**Last Updated:** 2026-03-10

## Original Problem Statement
Eine vollständig self-hosted, datenschutzorientierte, modulare Webanwendung für private und geschäftliche Dokumenten-, E-Mail-, Kalender- und Fallverwaltung mit KI-Unterstützung. Die Anwendung muss komplett unabhängig von externen Diensten funktionieren und per Docker Compose installierbar sein.

## User Personas

### Primary: Privacy-Conscious Professional
- Manages personal and business documents
- Needs offline-capable document management
- Values data sovereignty and privacy
- German-speaking, deals with authorities (Behörden)

### Secondary: Small Business Owner
- Multiple users with separate data areas
- Case-based workflow (clients, projects)
- Email integration needs
- Requires audit logs

## Core Requirements (Static)

### Must Have (P0)
- [x] Multi-user support with data separation
- [x] Document upload (PDF, PNG, JPG, DOCX)
- [x] OCR processing (Tesseract)
- [x] Case management with status tracking
- [x] Task management with priorities
- [x] Calendar with events
- [x] AI Chat interface
- [x] Setup wizard for first-time installation
- [x] Configurable AI provider (disabled/OpenAI)
- [x] Internet access toggle
- [x] Multilingual support (DE/EN)
- [x] Dark/Light theme
- [x] Docker Compose ready
- [x] No external platform dependencies

### Should Have (P1)
- [ ] IMAP email integration (structure ready)
- [ ] Draft generation with AI
- [ ] Document semantic search
- [ ] Deadline detection from documents
- [ ] Document attachment suggestions

### Nice to Have (P2)
- [ ] SMTP email sending
- [ ] Local LLM support (Ollama)
- [ ] Team roles and permissions
- [ ] Calendar sync (CalDAV)
- [ ] Mobile responsive optimization

## What's Been Implemented

### 2026-03-10 - MVP Release
- **Backend (FastAPI + MongoDB)**
  - User authentication with JWT
  - Setup wizard API
  - Cases CRUD
  - Documents CRUD with file upload
  - Tasks CRUD
  - Events CRUD
  - Drafts CRUD
  - AI Chat endpoint
  - System & User settings
  - Mail accounts structure
  - Audit logging

- **Frontend (React + Tailwind + Shadcn)**
  - Setup Wizard (5 steps)
  - Login page
  - Dashboard with stats
  - Documents page with upload
  - Cases management
  - Tasks board (Kanban-style)
  - Calendar (month view)
  - AI Chat interface
  - Settings (User, AI, Privacy)
  - Responsive sidebar navigation

- **Docker Infrastructure**
  - docker-compose.yml with all services
  - PostgreSQL, Redis, OCR service
  - Tesseract OCR service
  - Environment configuration

- **Design**
  - Dark theme ("Secure Vault")
  - Manrope + Inter fonts
  - German language support
  - Privacy-first UX

## Architecture

```
Frontend (React 19)
├── Pages: SetupWizard, Login, Dashboard, Documents, Cases, Tasks, Calendar, AI, Settings
├── Components: Layout, Sidebar, Cards
├── State: AuthContext
└── API: Axios client

Backend (FastAPI)
├── Routes: /api/auth, /api/setup, /api/cases, /api/documents, /api/tasks, /api/events, /api/ai, /api/settings
├── Models: User, Case, Document, Task, Event, Draft, Settings
├── Services: Auth (JWT), File Storage, AI Abstraction
└── Database: MongoDB (dev) / PostgreSQL (prod)

OCR Service (FastAPI + Tesseract)
├── Endpoints: /ocr, /languages, /health
└── Supports: PDF, PNG, JPG, TIFF
```

## Prioritized Backlog

### P0 (Critical - Next Sprint)
1. IMAP email fetching implementation
2. Email-to-case linking
3. Attachment import from emails
4. Document OCR auto-processing

### P1 (High - Following Sprint)
1. AI-powered draft generation
2. Document content analysis
3. Deadline extraction from OCR text
4. Full-text search implementation

### P2 (Medium)
1. Local LLM integration (Ollama)
2. Team collaboration features
3. Export/Import functionality
4. API documentation (Swagger UI)

### P3 (Low)
1. Mobile app (React Native)
2. Browser extensions
3. Third-party integrations

## Technical Decisions

1. **MongoDB for Development** - Quick iteration, flexible schema
2. **PostgreSQL for Production** - ACID compliance, better for Docker
3. **Tesseract OCR** - Open source, no API costs, German support
4. **OpenAI Integration** - Optional, configurable per installation
5. **No Emergent Dependencies** - Fully self-contained

## Next Tasks

1. Test IMAP email fetching with real mail server
2. Implement background job processing for OCR
3. Add document preview in browser
4. Implement search across all entities
5. Add data export functionality
