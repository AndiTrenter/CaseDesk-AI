# CaseDesk AI

Selbstgehostete, datenschutzkonforme Dokumenten- und Fallverwaltung mit KI-Unterstuetzung.

## Features

- Dokumentenverwaltung mit OCR und intelligentem Umbenennen
- Fallverwaltung mit KI-gestuetzter Analyse
- E-Mail-Verarbeitung via IMAP mit automatischer KI-Analyse
- KI-Assistent mit vollstaendiger Dokumentenkenntnis (OpenAI oder Ollama)
- Antwort-Generierung als PDF/DOCX mit Anlagen
- Automatische Frist-Erkennung mit Aufgaben- und Kalender-Erstellung
- Hintergrund-E-Mail-Sync (konfigurierbar pro Konto)
- Mehrbenutzersystem mit Rollen (Admin/Benutzer) und Einladungssystem
- Datenexport als ZIP mit allen Dokumenten
- Dark/Light Theme
- 100% Self-Hosted, keine Cloud-Abhaengigkeiten

---

## Installation auf Unraid

### Voraussetzungen

- Unraid mit Docker-Unterstuetzung
- OpenAI API-Key (von https://platform.openai.com/api-keys)

### Schritt fuer Schritt

```bash
# 1. Repository klonen
cd /mnt/user/appdata
git clone https://github.com/AndiTrenter/CaseDesk-AI.git casedesk
cd casedesk

# 2. Konfiguration erstellen
cp .env.example .env
nano .env
```

In der `.env` diese Werte anpassen:

| Variable | Was eintragen |
|----------|--------------|
| `MONGO_PASSWORD` | Sicheres Passwort waehlen |
| `SECRET_KEY` | `openssl rand -hex 32` ausfuehren, Ergebnis eintragen |
| `OPENAI_API_KEY` | Deinen OpenAI API-Key eintragen |

```bash
# 3. Images laden und starten
docker compose -f docker-compose.unraid.yml pull
docker compose -f docker-compose.unraid.yml up -d
```

Die App ist erreichbar unter **http://[DEINE-IP]:9090**

### Erster Start

1. Browser oeffnen: `http://[DEINE-IP]:9090`
2. Der Setup-Assistent fuehrt durch:
   - Admin-Konto erstellen
   - KI-Anbieter waehlen
   - Sprache einstellen
3. Fertig!

### Optional: Lokale KI mit Ollama

Wenn du statt OpenAI eine lokale KI nutzen moechtest:

```bash
# In .env aendern:
# AI_PROVIDER=ollama
# OPENAI_API_KEY=  (leer lassen)

docker compose -f docker-compose.unraid.yml --profile ollama up -d
```

---

## Konfiguration (.env)

| Variable | Pflicht | Beschreibung | Standard |
|----------|---------|-------------|---------|
| `MONGO_USER` | Ja | MongoDB Benutzername | `casedesk` |
| `MONGO_PASSWORD` | Ja | MongoDB Passwort | **AENDERN!** |
| `DB_NAME` | Ja | Datenbankname | `casedesk` |
| `SECRET_KEY` | Ja | JWT-Signaturschluessel | **AENDERN!** |
| `FRONTEND_PORT` | Ja | Web-Oberflaeche Port | `9090` |
| `AI_PROVIDER` | Ja | `openai` oder `ollama` | `openai` |
| `OPENAI_API_KEY` | Wenn OpenAI | OpenAI API-Key | - |
| `OLLAMA_URL` | Wenn Ollama | Ollama Server URL | `http://ollama:11434` |
| `OLLAMA_MODEL` | Wenn Ollama | Ollama Modell | `llama3.2` |

---

## Services

| Service | Beschreibung |
|---------|-------------|
| Frontend (Nginx) | Web-Oberflaeche, Port 9090 |
| Backend (FastAPI) | REST API (intern) |
| MongoDB | Datenbank (intern, nicht exponiert) |
| OCR | Tesseract OCR-Service (intern) |
| Ollama | Lokaler KI-Server (optional) |

---

## Docker Images (GHCR)

```
ghcr.io/anditrenter/casedesk-ai/backend:latest
ghcr.io/anditrenter/casedesk-ai/frontend:latest
ghcr.io/anditrenter/casedesk-ai/ocr:latest
```

---

## Daten-Pfade auf Unraid

| Pfad | Beschreibung |
|------|-------------|
| `/mnt/user/appdata/casedesk/mongodb` | MongoDB-Datenbank |
| `/mnt/user/appdata/casedesk/uploads` | Hochgeladene Dokumente |
| `/mnt/user/appdata/casedesk/ollama` | KI-Modelle (nur bei Ollama) |

---

## Backup

```bash
# MongoDB
docker exec casedesk-mongodb mongodump --out /dump \
  -u casedesk -p DEIN_PASSWORT --authenticationDatabase admin
docker cp casedesk-mongodb:/dump ./backup

# Uploads
cp -r /mnt/user/appdata/casedesk/uploads ./backup/uploads
```

## Update

```bash
cd /mnt/user/appdata/casedesk
git pull
docker compose -f docker-compose.unraid.yml pull
docker compose -f docker-compose.unraid.yml up -d
```

---

## Fuer Entwickler

Lokale Entwicklung mit Build:

```bash
# docker-compose.yml = lokaler Build
docker compose up -d

# Tests
cd backend && python -m pytest tests/ -v
```

---

## Architektur

```
backend/
  server.py             # FastAPI App + /api/health
  deps.py               # DB, Auth, Helpers
  ai_service.py         # KI-Abstraktionsschicht (OpenAI/Ollama)
  email_service.py      # IMAP/SMTP
  response_service.py   # PDF/DOCX-Generierung
  background_sync.py    # Automatischer E-Mail-Sync
  routers/              # API-Router (auth, cases, documents, ...)
frontend/               # React + Tailwind + Shadcn UI
ocr/                    # Tesseract OCR Microservice
```

## Lizenz

Private Nutzung. Alle Rechte vorbehalten.
