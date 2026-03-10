# CaseDesk AI - Product Requirements Document

## Project Overview
**Name:** CaseDesk AI  
**Version:** 1.0.0  
**Type:** Self-hosted Document & Case Management with AI Support  
**Last Updated:** 2026-03-10

## Original Problem Statement
Eine vollständig self-hosted, datenschutzorientierte, modulare Webanwendung für private und geschäftliche Dokumenten-, E-Mail-, Kalender- und Fallverwaltung mit KI-Unterstützung. Komplett standalone per Docker Compose installierbar.

## User Choices
- **KI:** Ollama (Llama 3.2) als Standard, OpenAI optional
- **OCR:** Tesseract (lokal)
- **Datenbank:** MongoDB (Dev) / PostgreSQL (Produktion)
- **Theme:** Dunkel als Standard mit Hell-Toggle
- **Sprache:** Mehrsprachig (DE/EN)

## What's Been Implemented (2026-03-10)

### Backend (FastAPI + MongoDB)
- ✅ User authentication with JWT
- ✅ Setup wizard API mit Ollama-Unterstützung
- ✅ Cases CRUD mit Status-Tracking
- ✅ Documents CRUD mit Auto-Processing
- ✅ Tasks CRUD mit Prioritäten
- ✅ Events CRUD für Kalender
- ✅ Drafts CRUD
- ✅ AI Chat mit Ollama/OpenAI-Abstraktion
- ✅ System & User Settings
- ✅ Mail Accounts Struktur
- ✅ Audit Logging

### Intelligente Dokumentenverarbeitung
- ✅ Auto-OCR bei Upload (Tesseract)
- ✅ KI-basierte Metadatenextraktion (Ollama)
- ✅ Auto-Umbenennung: `Datum – Absender – Dokumenttyp – Referenz – Kurzthema`
- ✅ Auto-Tag-Generierung
- ✅ Fristenerkennung mit Aufgabenerstellung
- ✅ Wichtigkeits-Bewertung (hoch/mittel/niedrig)

### Volltextsuche
- ✅ MongoDB Text-Index für deutsche Sprache
- ✅ Suche in Dokumenteninhalt (OCR-Text)
- ✅ Suche in Namen, Tags, Zusammenfassungen
- ✅ Relevanz-basiertes Ranking

### Frontend (React + Tailwind + Shadcn)
- ✅ Setup Wizard (5 Schritte) mit Ollama als Standard
- ✅ Login-Seite
- ✅ Dashboard mit Statistiken
- ✅ Dokumentenseite mit Upload, Suche, Reprocessing
- ✅ Fallverwaltung
- ✅ Aufgaben-Board (Kanban-Stil)
- ✅ Kalender (Monatsansicht)
- ✅ KI-Chat-Interface
- ✅ Einstellungen (User, KI, Datenschutz)

### Docker-Infrastruktur
- ✅ docker-compose.yml mit allen Services
- ✅ Ollama mit Llama 3.2 (Auto-Download)
- ✅ PostgreSQL, Redis
- ✅ Tesseract OCR Service
- ✅ GPU-Unterstützung (optional)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CaseDesk AI                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)      │  Backend (FastAPI)                 │
│  - Dashboard           │  - REST API                        │
│  - Dokumente           │  - AI Abstraction Layer            │
│  - Fälle               │  - Document Processor              │
│  - Aufgaben            │  - Search Engine                   │
│  - Kalender            │  - Auth & Sessions                 │
│  - KI-Chat             │                                    │
├─────────────────────────────────────────────────────────────┤
│  Ollama       │ PostgreSQL │  Redis    │ OCR Service       │
│  (Llama 3.2) │ (Datenbank)│ (Cache)   │ (Tesseract)       │
└─────────────────────────────────────────────────────────────┘
```

## Prioritized Backlog

### P0 (Nächster Sprint)
1. IMAP E-Mail-Abruf implementieren
2. E-Mail-zu-Fall-Verknüpfung
3. Anhänge aus E-Mails importieren
4. E-Mails nach Verarbeitung als gelesen markieren

### P1 (Folgender Sprint)
1. KI-gestützte Entwurfserstellung
2. Dokumenten-Vorschau im Browser
3. Export/Import-Funktionalität
4. SMTP E-Mail-Versand (mit Freigabe)

### P2 (Mittel)
1. Team-Rollen und Berechtigungen
2. CalDAV-Kalendersync
3. Mobile Optimierung
4. Webhook-Integrationen

## Technical Decisions

1. **Ollama als Standard-KI** - Läuft lokal, kostenlos, datenschutzkonform
2. **MongoDB für Entwicklung** - Schnelle Iteration, flexible Schemas
3. **PostgreSQL für Produktion** - ACID-Compliance, robuster
4. **Tesseract OCR** - Open Source, deutsche Sprachunterstützung
5. **Keine Emergent-Abhängigkeiten** - Vollständig self-contained

## Next Action Items

1. ✅ Ollama Integration abgeschlossen
2. ✅ Intelligente Dokumentenverarbeitung implementiert
3. ✅ Volltextsuche implementiert
4. ⏳ IMAP E-Mail-Integration
5. ⏳ Dokumenten-Vorschau
6. ⏳ Datenexport-Funktion
