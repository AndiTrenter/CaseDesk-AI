# CaseDesk AI - Product Requirements Document

## Repository
https://github.com/AndiTrenter/CaseDesk-AI

## Deploy-Architektur
- `docker-compose.yml` = Entwicklung (lokaler Build)
- `docker-compose.unraid.yml` = Produktion/Unraid (GHCR Images only)
- `.env.example` = Vollstaendige Konfiguration, OpenAI als Standard

## GHCR Images
- `ghcr.io/anditrenter/casedesk-ai/backend:latest`
- `ghcr.io/anditrenter/casedesk-ai/frontend:latest`
- `ghcr.io/anditrenter/casedesk-ai/ocr:latest`

## Nach Push manuell:
- GitHub > Packages > backend/frontend/ocr > Settings > Visibility = Public

## Alle Features implementiert
- Setup Wizard, JWT Auth, Rollen (Admin/User)
- Dokumente: Upload, OCR, intelligentes Umbenennen, Suche
- Faelle: CRUD, Tabs, KI-Analyse
- KI-Chat mit vollem Dokumentenwissen + Download-Links
- Antwort-Generierung PDF/DOCX
- E-Mail: IMAP-Fetch, KI-Analyse, Auto-Sync
- Kalender/Aufgaben-Automatisierung aus Fristen
- Datenexport als ZIP
- OpenAI-only oder Ollama (optional via Profile)
- /api/health fuer Docker Healthcheck
- MongoDB intern (kein externer Port in Prod)
