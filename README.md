# CaseDesk AI

Selbstgehostete, datenschutzkonforme Dokumenten- und Fallverwaltung mit KI-Unterstützung.

## Features

- **Dokumentenverwaltung** mit OCR und intelligentem Umbenennen
- **Fallverwaltung** mit KI-gestützter Analyse
- **E-Mail-Verarbeitung** via IMAP mit automatischer KI-Analyse
- **KI-Assistent** mit vollständiger Dokumentenkenntnis (Ollama lokal oder OpenAI)
- **Antwort-Generierung** als PDF/DOCX mit Anlagen
- **Automatische Frist-Erkennung** mit Aufgaben- und Kalender-Erstellung
- **Hintergrund-E-Mail-Sync** (konfigurierbar pro Konto)
- **Mehrbenutzersystem** mit Rollen (Admin/Benutzer) und Einladungssystem
- **Datenexport** als ZIP mit allen Dokumenten
- **Dark/Light Theme**
- **Mehrsprachig** (DE, EN, FR, ES)
- **100% Self-Hosted** — keine Cloud-Abhängigkeiten

---

## Quick Start (Docker)

### Voraussetzungen

- Docker & Docker Compose v2+
- (Optional) NVIDIA GPU für schnellere lokale KI

### Installation

```bash
git clone https://github.com/AndiTrenter/CaseDesk-AI.git
cd CaseDesk-AI

cp .env.example .env
nano .env   # Passwörter und SECRET_KEY ändern!

# Nur mit OpenAI (kein Ollama):
docker compose up -d

# Mit Ollama (lokale KI, CPU):
docker compose --profile ollama up -d

# Mit Ollama + NVIDIA GPU:
docker compose --profile gpu up -d
```

Die App ist erreichbar unter **http://localhost:9090** (oder dem Port aus `.env`).

### Erster Start

1. Browser öffnen: `http://localhost:9090`
2. Der Setup-Assistent führt durch:
   - Admin-Konto erstellen
   - KI-Anbieter wählen (Ollama lokal oder OpenAI)
   - Sprache einstellen
3. Fertig! Dokumente hochladen und loslegen.

---

## Quick Start (Unraid)

### Option A: Docker Compose auf Unraid

```bash
# Im Unraid Terminal:
cd /mnt/user/appdata
git clone https://github.com/AndiTrenter/CaseDesk-AI.git casedesk
cd casedesk

cp .env.example .env
nano .env   # Passwörter ändern!

# Ohne Ollama (nur OpenAI):
docker compose -f docker-compose.unraid.yml up -d

# Mit Ollama (CPU):
docker compose -f docker-compose.unraid.yml --profile ollama up -d

# Mit Ollama (NVIDIA GPU):
docker compose -f docker-compose.unraid.yml --profile gpu up -d
```

### Option B: Unraid Community Applications

1. Lade die Template-XML von `unraid-template/casedesk-ai.xml`
2. In Unraid: **Docker** → **Add Container** → **Template** → XML-URL einfügen
3. Konfiguriere Passwörter und Ports
4. Starten

### Daten-Pfade auf Unraid

| Pfad | Beschreibung |
|------|-------------|
| `/mnt/user/appdata/casedesk/mongodb` | MongoDB-Datenbank |
| `/mnt/user/appdata/casedesk/uploads` | Hochgeladene Dokumente |
| `/mnt/user/appdata/casedesk/ollama` | KI-Modelle (Ollama) |

---

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|-------------|---------|
| `MONGO_USER` | MongoDB Benutzername | `casedesk` |
| `MONGO_PASSWORD` | MongoDB Passwort | **ÄNDERN!** |
| `DB_NAME` | Datenbankname | `casedesk` |
| `SECRET_KEY` | JWT-Signaturschlüssel | **ÄNDERN!** |
| `FRONTEND_PORT` | Web-Oberfläche Port | `9090` |
| `BACKEND_PORT` | API Port | `8001` |
| `MONGO_PORT` | MongoDB Port | `27017` |
| `ENABLE_OLLAMA` | Ollama aktivieren | `true` |
| `OPENAI_API_KEY` | OpenAI API Key (optional) | leer |
| `OLLAMA_MODEL` | Ollama Modell | `llama3.2` |

---

## Services

| Service | Port | Beschreibung |
|---------|------|-------------|
| Frontend (Nginx) | 9090 | Web-Oberfläche + API-Proxy |
| Backend (FastAPI) | 8001 | REST API |
| MongoDB | 27017 | Dokumentendatenbank |
| OCR | 8002 | Tesseract OCR-Service |
| Ollama | 11434 | Lokaler KI-Server (optional) |

---

## Docker Images (GHCR)

```bash
# Images direkt von GitHub Container Registry:
docker pull ghcr.io/anditrenter/casedesk-ai/backend:latest
docker pull ghcr.io/anditrenter/casedesk-ai/frontend:latest
docker pull ghcr.io/anditrenter/casedesk-ai/ocr:latest
```

---

## Backup

```bash
# MongoDB Backup
docker exec casedesk-mongodb mongodump --out /dump \
  -u casedesk -p <PASSWORT> --authenticationDatabase admin
docker cp casedesk-mongodb:/dump ./backup

# Uploads Backup
docker cp casedesk-backend:/app/uploads ./backup/uploads
```

---

## Update

```bash
git pull
docker compose build
docker compose up -d
```

---

## Entwicklung

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
yarn install
yarn start

# Tests
cd backend
python -m pytest tests/ -v
```

---

## Architektur

```
CaseDesk-AI/
├── backend/
│   ├── server.py           # FastAPI Hauptapp
│   ├── deps.py             # Shared: DB, Auth, Helpers
│   ├── ai_service.py       # KI-Abstraktionsschicht
│   ├── email_service.py    # IMAP/SMTP Service
│   ├── response_service.py # Antwort-Generierung (PDF/DOCX)
│   ├── background_sync.py  # Automatische E-Mail-Synchronisation
│   └── routers/            # Domain-spezifische API-Router
│       ├── auth.py         # Login, Registrierung, Benutzer
│       ├── cases.py        # Fallverwaltung
│       ├── documents.py    # Dokumentenverwaltung + OCR
│       ├── tasks.py        # Aufgabenverwaltung
│       ├── events.py       # Kalender + Frist-Automatisierung
│       ├── ai.py           # KI-Chat + Proaktive KI
│       ├── emails.py       # E-Mail-Verarbeitung
│       ├── settings.py     # Einstellungen + Dashboard + Export
│       └── correspondence.py # Antwort-Generierung + Korrespondenz
├── frontend/               # React + Tailwind + Shadcn UI
├── ocr/                    # Tesseract OCR Microservice
├── docker-compose.yml      # Standard Docker Compose
├── docker-compose.unraid.yml # Unraid-optimiert
├── .env.example            # Umgebungsvariablen Template
├── .github/workflows/      # CI/CD: Build + Push zu GHCR
└── unraid-template/        # Unraid Community App Template
```

## Lizenz

Private Nutzung. Alle Rechte vorbehalten.
