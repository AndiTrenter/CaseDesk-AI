# CaseDesk AI - Product Requirements Document

## Project Overview
**Name:** CaseDesk AI  
**Version:** 1.0.0  
**Type:** Self-hosted Document & Case Management with AI Support  
**Last Updated:** 2026-03-10

## Aktueller Status: MVP COMPLETE ✅

### Ja, mit OpenAI funktioniert alles sofort!
Bei Freigabe von Internetzugriff + OpenAI API-Key sind alle KI-Features voll funktionsfähig:
- Dokumentenanalyse & Auto-Tagging
- Intelligente Umbenennung
- KI-Chat
- E-Mail-Analyse
- Fristenerkennung

## Implementierte Features (2026-03-10)

### ✅ Backend (FastAPI + MongoDB)
- User Authentication mit JWT
- Setup-Wizard mit Ollama/OpenAI-Auswahl
- Cases CRUD mit Status-Tracking
- Documents CRUD mit Auto-Processing
- Tasks CRUD mit Prioritäten
- Events CRUD für Kalender
- Drafts CRUD
- AI Chat mit Ollama/OpenAI-Abstraktion
- System & User Settings
- Audit Logging

### ✅ Intelligente Dokumentenverarbeitung
- Auto-OCR bei Upload (Tesseract)
- KI-basierte Metadatenextraktion
- Auto-Umbenennung: `Datum – Absender – Dokumenttyp – Referenz – Kurzthema`
- Auto-Tag-Generierung
- Fristenerkennung mit Aufgabenerstellung
- Wichtigkeits-Bewertung

### ✅ Volltextsuche
- MongoDB Text-Index für deutsche Sprache
- Suche in Dokumenteninhalt (OCR-Text)
- Suche in Namen, Tags, Zusammenfassungen
- Relevanz-basiertes Ranking

### ✅ E-Mail-Integration (NEU)
- IMAP E-Mail-Abruf
- E-Mail-Verarbeitung mit KI
- Anhänge als Dokumente importieren
- E-Mail-zu-Fall-Verknüpfung
- E-Mails als gelesen markieren

### ✅ Dokumenten-Vorschau (NEU)
- Vorschau-Endpoint mit Metadaten
- Download-Endpoint
- OCR-Text-Anzeige

### ✅ Datenexport (NEU)
- Vollständiger JSON-Export aller Daten
- Fall-spezifischer Export
- Download als Datei

### ✅ Frontend (React + Tailwind)
- Setup-Wizard (5 Schritte)
- Login-Seite
- Dashboard mit Statistiken
- Dokumentenseite mit Upload, Suche, Reprocessing
- Fallverwaltung
- E-Mail-Seite mit Abruf und Verknüpfung
- Aufgaben-Board
- Kalender
- KI-Chat-Interface
- Einstellungen (User, E-Mail, KI, Datenschutz, Export)

### ✅ Docker-Infrastruktur
- docker-compose.yml mit allen Services
- Ollama mit Llama 3.2 (Auto-Download)
- PostgreSQL, Redis
- Tesseract OCR Service
- GPU-Unterstützung (optional)

## Login für Preview
- **URL:** https://privacy-case-hub.preview.emergentagent.com
- **Email:** admin@casedesk.app
- **Passwort:** admin123

## Konfiguration für volle KI-Funktion

1. **Settings → Privacy:** Internetzugriff auf "Erlaubt" setzen
2. **Settings → AI Configuration:** OpenAI auswählen
3. **OpenAI API-Key eingeben**

Danach funktionieren:
- Dokumentenanalyse bei Upload
- KI-Chat
- E-Mail-Zusammenfassungen
- Fristenerkennung

## Verbleibende optionale Features (P1/P2)

### P1 (Nicht kritisch)
- SMTP E-Mail-Versand (mit Freigabe)
- KI-gestützte Entwurfserstellung
- Dokumenten-Vorschau im Browser (PDF-Viewer)

### P2 (Nice-to-Have)
- Team-Rollen und Berechtigungen
- CalDAV-Kalendersync
- Mobile Optimierung
- Webhook-Integrationen
- Browser-basierte PDF-Vorschau

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      CaseDesk AI                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)      │  Backend (FastAPI)                 │
│  - Dashboard           │  - REST API                        │
│  - Dokumente           │  - AI Abstraction Layer            │
│  - Fälle               │  - Document Processor              │
│  - E-Mails             │  - Email Service                   │
│  - Aufgaben            │  - Search Engine                   │
│  - Kalender            │  - Export Service                  │
│  - KI-Chat             │  - Auth & Sessions                 │
├─────────────────────────────────────────────────────────────┤
│  Ollama       │ PostgreSQL │  Redis    │ OCR Service       │
│  (Llama 3.2) │ (Datenbank)│ (Cache)   │ (Tesseract)       │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/yourusername/casedesk-ai.git
cd casedesk-ai
cp .env.example .env
# .env anpassen (SECRET_KEY!)
docker-compose up -d
# Browser: http://localhost:3000
```
