# CaseDesk AI

Eine vollständig self-hosted, datenschutzorientierte Webanwendung für private und geschäftliche Dokumenten-, E-Mail-, Kalender- und Fallverwaltung mit KI-Unterstützung.

## Features

- **Intelligente Dokumentenverarbeitung**
  - Automatische OCR bei Upload (Tesseract)
  - KI-basierte Metadatenextraktion (Absender, Datum, Typ, Referenz)
  - Automatische Umbenennung: `Datum – Absender – Dokumenttyp – Referenz – Kurzthema`
  - Automatische Tag-Generierung
  - Fristenerkennung und Aufgabenerstellung

- **Volltextsuche**
  - Durchsucht Dokumenteninhalt, nicht nur Namen
  - Relevanz-basiertes Ranking
  - Deutsche Sprachunterstützung

- **Lokale KI mit Ollama**
  - Llama 3.2 wird automatisch installiert
  - Funktioniert komplett offline
  - Keine API-Kosten

- **Fallverwaltung**: Strukturierte Verwaltung von Vorgängen
- **E-Mail-Integration**: IMAP-Abruf und -Verarbeitung
- **Kalender & Aufgaben**: Fristen und Termine im Blick
- **KI-Assistent**: Intelligente Analyse und Entwurfserstellung
- **Mehrbenutzerfähig**: Getrennte Datenbereiche pro Benutzer
- **Datenschutz**: Vollständige Kontrolle über externe Verbindungen

## Schnellstart

### Voraussetzungen

- Docker & Docker Compose
- Mindestens 8GB RAM (für Ollama LLM)
- 20GB freier Speicherplatz
- Optional: NVIDIA GPU für schnellere KI-Verarbeitung

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
   
   > Beim ersten Start wird Ollama das Llama 3.2 Modell herunterladen (~2GB).
   > Dies kann einige Minuten dauern.

4. **Weboberfläche öffnen**
   ```
   http://localhost:3000
   ```

5. **Setup-Assistent durchlaufen**
   - Sprache wählen (Deutsch/English)
   - Admin-Benutzer anlegen
   - KI-Provider wählen (Ollama empfohlen)
   - Datenschutz-Einstellungen festlegen

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      CaseDesk AI                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)      │  Backend (FastAPI)                 │
│  - Dashboard           │  - REST API                        │
│  - Dokumente           │  - Auth & Sessions                 │
│  - Fälle               │  - Document Processing             │
│  - E-Mails             │  - AI Abstraction Layer            │
│  - Kalender            │  - IMAP Integration                │
│  - KI-Chat             │                                    │
├─────────────────────────────────────────────────────────────┤
│  Ollama       │ PostgreSQL │  Redis    │ OCR Service       │
│  (Llama 3.2) │ (Datenbank)│ (Cache)   │ (Tesseract)       │
└─────────────────────────────────────────────────────────────┘
```

## Dokumentenverarbeitung

Wenn Sie ein Dokument hochladen, passiert folgendes automatisch:

1. **OCR** - Text wird aus PDF/Bild extrahiert (Tesseract)
2. **KI-Analyse** - Ollama analysiert den Inhalt:
   - Datum erkennen
   - Absender identifizieren
   - Dokumenttyp klassifizieren
   - Referenznummer/Aktenzeichen finden
   - Kurzthema erstellen
   - Relevante Tags generieren
   - Fristen erkennen
3. **Umbenennung** - Dokument wird nach Schema umbenannt:
   `2024-03-15 – Finanzamt München – Steuerbescheid – 123/456/789 – Einkommensteuer 2023.pdf`
4. **Aufgaben** - Erkannte Fristen werden als Aufgaben angelegt

## Volltextsuche

Die Suche durchsucht:
- Dokumenteninhalt (OCR-Text)
- Dokumentennamen
- Tags
- KI-Zusammenfassungen

Beispiel: Suche nach "Steuern 24" findet alle Dokumente die mit Steuern 2024 zu tun haben, auch wenn der Dateiname anders lautet.

## GPU-Unterstützung (Optional)

Für schnellere KI-Verarbeitung mit NVIDIA GPU:

```yaml
# In docker-compose.yml ist GPU-Support bereits konfiguriert
# Stellen Sie sicher, dass nvidia-container-toolkit installiert ist:
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker
```

Ohne GPU funktioniert alles auf CPU, aber langsamer.

## Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `POSTGRES_PASSWORD` | Datenbank-Passwort | `casedesk_secret` |
| `SECRET_KEY` | JWT-Verschlüsselung | Muss geändert werden! |
| `OPENAI_API_KEY` | Optional für OpenAI | - |

### KI-Provider

Im Web-Interface unter **Einstellungen > KI**:

- **Ollama (Empfohlen)**: Läuft lokal, kostenlos, kein Internet nötig
- **OpenAI**: Benötigt API-Key und Internetzugriff
- **Deaktiviert**: Keine KI-Funktionen

### Datenschutz

Unter **Einstellungen > Datenschutz**:

- **Internetzugriff blockieren**: Kompletter Offline-Betrieb
- **Internetzugriff erlauben**: Für OpenAI oder Recherche

## API-Dokumentation

Nach dem Start verfügbar unter:
- Swagger UI: `http://localhost:8001/api/docs`
- ReDoc: `http://localhost:8001/api/redoc`

## Entwicklung

### Lokale Entwicklung ohne Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start

# Ollama separat installieren
# https://ollama.ai/download
ollama serve
ollama pull llama3.2
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

## Troubleshooting

### Ollama startet nicht
```bash
# Logs prüfen
docker-compose logs ollama

# Manuell Modell laden
docker-compose exec ollama ollama pull llama3.2
```

### OCR funktioniert nicht
```bash
# OCR Service Status
docker-compose logs ocr

# Tesseract Sprachen prüfen
docker-compose exec ocr tesseract --list-langs
```

### Dokumentenverarbeitung langsam
- GPU aktivieren für schnellere KI
- RAM auf 8GB+ erhöhen
- SSD statt HDD verwenden

## Lizenz

MIT License - Siehe LICENSE-Datei
