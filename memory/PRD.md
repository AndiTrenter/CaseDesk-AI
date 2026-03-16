# CaseDesk AI - Product Requirements Document

## Project Overview
**Name:** CaseDesk AI  
**Version:** 1.3.0  
**Type:** Self-hosted Document & Case Management with AI Support  
**Last Updated:** 2026-03-16

## Aktueller Status: FEATURE-COMPLETE ✅

### Neueste Features (2026-03-16)

#### ✅ KI-Assistent mit Sprachunterstützung
- KI antwortet **ausschließlich** in der eingestellten Benutzersprache (DE, EN, FR, ES)
- Versteht und beantwortet Anfragen in der jeweiligen Sprache
- Alle Kontext-Labels werden in der Benutzersprache angezeigt

#### ✅ Dokumente zu Fällen zuweisen
- **In Fällen**: Dokumente hochladen oder vorhandene verknüpfen
- **In Dokumenten**: Mehrfachauswahl-Modus zum Zuweisen zu Fällen
- Dokumente können aus Fällen entfernt werden
- "Im Fall" Badge zeigt verknüpfte Dokumente

#### ✅ Proaktiver KI-Assistent
- **Tägliches KI-Briefing** auf dem Dashboard mit Prioritäten, Fristen, Empfehlungen
- **KI-Assistent-Tab** in der Fall-Detailansicht (als erster Tab!)
- **Proaktive Fallanalyse** mit dringenden Aktionen, erkannten Fristen, nächsten Schritten
- **Automatische Dokumentenvorschläge** beim Erstellen eines Falls
- **Automatische Dokumentenverknüpfung** nach Fall-Erstellung

#### ✅ KI mit vollem Dokumentenwissen
- Der KI-Chat hat Zugriff auf ALLE Dokumente, Fälle, Aufgaben und Termine
- Kann Querverweise zwischen Dokumenten herstellen
- Findet zusammengehörige Dokumente automatisch

#### ✅ Theme-Umschalter (Hell/Dunkel)
- Sonnen/Mond-Icon in der Sidebar zum Umschalten
- Theme-Auswahl auch in User Preferences

#### ✅ Benutzereinladungssystem
- Admin kann neue Benutzer per E-Mail einladen
- Einladungslink mit Token (7 Tage gültig)
- Registrierungsseite für eingeladene Benutzer

#### ✅ Response-Paket-Generierung
- KI analysiert Fall und schlägt Antworttyp vor
- Generiert komplettes Antwortschreiben (PDF/DOCX/TXT)
- Dokumente als Anlagen auswählbar
- Download als ZIP-Paket oder Versand per E-Mail

### Mit OpenAI funktioniert alles sofort!
Bei Freigabe von Internetzugriff + OpenAI API-Key sind alle KI-Features voll funktionsfähig.

## Implementierte Features (Komplett)

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
- **URL:** https://case-response-pkg.preview.emergentagent.com
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

## Verbleibende optionale Features (P2)

### P2 (Nice-to-Have)
- Team-Rollen und Berechtigungen (Feinabstimmung)
- CalDAV-Kalendersync
- Mobile Optimierung
- Webhook-Integrationen
- Browser-basierte PDF-Vorschau mit Annotation

## Erledigte Features (Vollständig)

### ✅ SMTP E-Mail-Versand
- SMTP-Einstellungen in E-Mail-Konto-Konfiguration
- Versand von Korrespondenz per E-Mail

### ✅ KI-gestützte Entwurfserstellung
- Response-Generierung für Fälle
- Verschiedene Antworttypen (Widerspruch, Antrag, etc.)

### ✅ Dokumenten-Viewer
- PDF-Anzeige im Browser
- Bild-Vorschau
- OCR-Text-Anzeige

### ✅ Benutzereinladungssystem
- Admin kann Benutzer einladen
- Registrierung über Einladungslink

### ✅ Theme-Umschalter
- Hell/Dunkel-Modus

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
