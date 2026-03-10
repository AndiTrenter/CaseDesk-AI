# CaseDesk AI

Eine vollständig self-hosted, datenschutzorientierte Webanwendung für private und geschäftliche Dokumenten-, E-Mail-, Kalender- und Fallverwaltung mit KI-Unterstützung.

## Features

- **Dokumentenverwaltung**: Upload, OCR, Suche und Kategorisierung
- **Fallverwaltung**: Strukturierte Verwaltung von Vorgängen
- **E-Mail-Integration**: IMAP-Abruf und -Verarbeitung
- **Kalender & Aufgaben**: Fristen und Termine im Blick
- **KI-Assistent**: Intelligente Analyse und Entwurfserstellung
- **Mehrbenutzerfähig**: Getrennte Datenbereiche pro Benutzer
- **Datenschutz**: Vollständige Kontrolle über externe Verbindungen

## Schnellstart

### Voraussetzungen

- Docker & Docker Compose
- Mindestens 4GB RAM
- 10GB freier Speicherplatz

### Installation

1. **Repository klonen**
   ```bash
   git clone https://github.com/yourusername/casedesk-ai.git
   cd casedesk-ai
   ```

2. **Umgebungsvariablen konfigurieren**
   ```bash
   cp .env.example .env
   # .env-Datei bearbeiten und SECRET_KEY ändern
   nano .env
   ```

3. **Container starten**
   ```bash
   docker-compose up -d
   ```

4. **Weboberfläche öffnen**
   ```
   http://localhost:3000
   ```

5. **Setup-Assistent durchlaufen**
   - Sprache wählen
   - Admin-Benutzer anlegen
   - KI-Provider konfigurieren (optional)
   - Datenschutz-Einstellungen festlegen

## Konfiguration

### KI-Integration (Optional)

CaseDesk AI kann vollständig lokal ohne externe KI-Dienste betrieben werden.

Für erweiterte KI-Funktionen:
1. OpenAI API-Key in `.env` eintragen
2. Oder im Setup-Assistent konfigurieren

### E-Mail-Integration

IMAP-Konten werden im Web-Interface unter **Einstellungen > E-Mail** konfiguriert.

### Datenschutz

Unter **Einstellungen > Datenschutz** können Sie:
- Internetzugriff vollständig deaktivieren
- Externe KI-Nutzung steuern
- Audit-Logs einsehen

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    CaseDesk AI                          │
├─────────────────────────────────────────────────────────┤
│  Frontend (React)     │  Backend (FastAPI)              │
│  - Dashboard          │  - REST API                     │
│  - Dokumente          │  - Auth & Sessions              │
│  - Fälle              │  - Document Processing          │
│  - E-Mails            │  - AI Abstraction Layer         │
│  - Kalender           │  - IMAP Integration             │
│  - KI-Chat            │                                 │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL   │  Redis       │  OCR Service (Tesseract) │
│  (Datenbank)  │  (Cache/Jobs)│  (Texterkennung)         │
└─────────────────────────────────────────────────────────┘
```

## Entwicklung

### Lokale Entwicklung

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

### Tests

```bash
# Backend Tests
cd backend
pytest

# Frontend Tests
cd frontend
yarn test
```

## API-Dokumentation

Nach dem Start verfügbar unter:
- Swagger UI: `http://localhost:8001/api/docs`
- ReDoc: `http://localhost:8001/api/redoc`

## Lizenz

MIT License - Siehe LICENSE-Datei

## Support

Bei Fragen oder Problemen:
- GitHub Issues öffnen
- Dokumentation unter `/docs` lesen
