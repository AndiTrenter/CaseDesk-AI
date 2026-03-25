# CaseDesk AI

Selbstgehostete, datenschutzkonforme Dokumenten- und Fallverwaltung mit KI-Unterstützung.

## Features

- 📄 Dokumentenverwaltung mit OCR und intelligentem Umbenennen
- 📁 Fallverwaltung mit KI-gestützter Analyse
- 📧 E-Mail-Verarbeitung via IMAP mit automatischer KI-Analyse
- 🤖 KI-Assistent mit Spracheingabe (OpenAI oder lokales Ollama)
- 📝 Antwort-Generierung als PDF/DOCX mit Anlagen
- ⏰ Automatische Frist-Erkennung mit Aufgaben- und Kalender-Erstellung
- 👥 Mehrbenutzersystem mit Rollen (Admin/Benutzer)
- 💾 Datenexport als ZIP mit allen Dokumenten
- 🌙 Dark/Light Theme
- 🔒 100% Self-Hosted, keine Cloud-Abhängigkeiten

---

## Installation auf Unraid

### Voraussetzungen

- Unraid mit Docker-Unterstützung
- OpenAI API-Key (von https://platform.openai.com/api-keys) ODER Ollama für lokale KI

### Schritt für Schritt

```bash
# 1. Repository klonen
cd /mnt/user/appdata
git clone https://github.com/AndiTrenter/CaseDesk-AI.git casedesk
cd casedesk

# 2. Konfiguration erstellen
cp .env.example .env
nano .env
```

**In der `.env` diese Werte anpassen:**

| Variable | Was eintragen |
|----------|--------------|
| `SECRET_KEY` | `openssl rand -hex 32` ausführen, Ergebnis eintragen |
| `OPENAI_API_KEY` | Deinen OpenAI API-Key eintragen |

```bash
# 3. Starten
docker compose -f docker-compose.unraid.yml up -d
```

**🌐 Die App ist erreichbar unter: http://[DEINE-IP]:9090**

### Erster Start

1. Browser öffnen: `http://[DEINE-IP]:9090`
2. Der Setup-Assistent führt durch:
   - Admin-Konto erstellen
   - KI-Anbieter wählen
   - Sprache einstellen
3. Fertig!

---

## Lokale KI mit Ollama (Optional)

Wenn du statt OpenAI eine lokale KI nutzen möchtest:

```bash
# In .env ändern:
AI_PROVIDER=ollama
OPENAI_API_KEY=  # leer lassen

# Mit Ollama starten:
docker compose -f docker-compose.unraid.yml --profile ollama up -d

# Nach dem Start das Modell laden:
docker exec casedesk-ollama ollama pull llama3.2
```

---

## Konfiguration (.env)

| Variable | Beschreibung | Standard |
|----------|-------------|---------|
| `DB_NAME` | Datenbankname | `casedesk` |
| `SECRET_KEY` | JWT-Signaturschlüssel | **ÄNDERN!** |
| `FRONTEND_PORT` | Web-Oberfläche Port | `9090` |
| `AI_PROVIDER` | `openai` oder `ollama` | `openai` |
| `OPENAI_API_KEY` | OpenAI API-Key | - |
| `OLLAMA_URL` | Ollama Server URL | `http://ollama:11434` |
| `OLLAMA_MODEL` | Ollama Modell | `llama3.2` |

---

## Services

| Service | Container | Beschreibung |
|---------|-----------|-------------|
| Frontend | casedesk-frontend | Web-Oberfläche (Port 9090) |
| Backend | casedesk-backend | REST API (intern) |
| MongoDB | casedesk-mongodb | Datenbank (intern) |
| OCR | casedesk-ocr | Tesseract OCR-Service (intern) |
| Ollama | casedesk-ollama | Lokaler KI-Server (optional) |

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
# MongoDB Backup
docker exec casedesk-mongodb mongodump --archive=/data/db/backup.archive
docker cp casedesk-mongodb:/data/db/backup.archive ./backup/

# Uploads sichern
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

## Fehlerbehebung

### Container-Logs anzeigen
```bash
docker logs casedesk-backend
docker logs casedesk-frontend
docker logs casedesk-mongodb
```

### Alle Container neu starten
```bash
docker compose -f docker-compose.unraid.yml restart
```

### Komplett neu starten
```bash
docker compose -f docker-compose.unraid.yml down
docker compose -f docker-compose.unraid.yml up -d
```

---

## Architektur

```
backend/
  server.py             # FastAPI App
  deps.py               # DB, Auth, Helpers
  ai_service.py         # KI-Abstraktionsschicht (OpenAI/Ollama)
  email_service.py      # IMAP/SMTP
  response_service.py   # PDF/DOCX-Generierung
  background_sync.py    # Automatischer E-Mail-Sync
  routers/              # API-Router

frontend/               # React + Tailwind + Shadcn UI

ocr/                    # Tesseract OCR Microservice
```

---

## Lizenz

Private Nutzung. Alle Rechte vorbehalten.
