# 🔄 CaseDesk AI - Update-System

Diese Dokumentation erklärt das integrierte Update-System von CaseDesk AI.

## 📋 Übersicht

Das Update-System ermöglicht:
- ✅ Automatische Erkennung neuer Versionen
- ✅ Updates direkt über das Webinterface
- ✅ Keine Terminal-Befehle notwendig
- ✅ Daten bleiben erhalten (.env, MongoDB, Uploads)
- ✅ Changelog-Anzeige vor jedem Update
- ✅ Rollback zur vorherigen Version

---

## 🏗️ Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ version.json│  │ CHANGELOG.md │  │ GitHub Actions     │  │
│  │ (aktuell)   │  │ (Historie)   │  │ (Build Pipeline)   │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Container Registry                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │ backend:v1.0.1  │ │ frontend:v1.0.1 │ │ ocr:v1.0.1    │  │
│  │ backend:latest  │ │ frontend:latest │ │ ocr:latest    │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CaseDesk AI Portal                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Einstellungen → Updates                                 ││
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ││
│  │ │ Version     │  │ Changelog   │  │ Update-Button   │  ││
│  │ │ Anzeige     │  │ Anzeige     │  │ + Healthcheck   │  ││
│  │ └─────────────┘  └──────────────┘  └─────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Versionierung

| Version | Bedeutung |
|---------|----------|
| v1.x.x  | Verbesserungen/Bugfixes am bestehenden System |
| v2.x.x  | Grundlegende neue Features (z.B. Kontaktliste) |
| v3.x.x  | Major Architekturänderungen |

---

## 🔧 Wie funktioniert ein Update?

### 1. Versions-Check

Das Portal prüft regelmäßig die aktuelle Version:

```
Lokal:  GET /api/system/version
Online: GET https://raw.githubusercontent.com/AndiTrenter/CaseDesk-AI/main/version.json
```

### 2. Update-Erkennung

Wenn die Online-Version neuer ist, erscheint:

```
🔔 Update verfügbar: v1.0.1
```

### 3. Changelog anzeigen

Vor dem Update wird der Changelog geladen und angezeigt:
- Was ist neu?
- Was wurde geändert?
- Was wurde behoben?

### 4. Update ausführen

Bei Klick auf "Update installieren":

```bash
# Intern ausgeführte Befehle:
docker compose -f docker-compose.unraid.yml pull
docker compose -f docker-compose.unraid.yml up -d
```

### 5. Healthcheck

Nach dem Update wird geprüft:

```
GET /api/health → {"status": "healthy"}
```

Erst bei erfolgreichem Healthcheck gilt das Update als abgeschlossen.

---

## 💾 Datenpersistenz

### Diese Daten bleiben IMMER erhalten:

| Daten | Speicherort | Grund |
|-------|-------------|-------|
| `.env` | Host-Dateisystem | Wird nie überschrieben |
| MongoDB | Docker Volume | `mongodb:/data/db` |
| Uploads | Docker Volume | `/app/uploads` |
| Ollama Modelle | Docker Volume | `/root/.ollama` |

### Das passiert beim Update:

1. ✅ Neue Docker Images werden heruntergeladen
2. ✅ Container werden neu gestartet
3. ❌ Volumes werden NICHT verändert
4. ❌ .env wird NICHT überschrieben
5. ❌ Datenbank wird NICHT gelöscht

---

## 🔁 Rollback

Falls ein Update Probleme verursacht:

### Option 1: Über das Portal
1. Einstellungen → Updates
2. "Zurück zur vorherigen Version" klicken

### Option 2: Manuell
```bash
cd /mnt/user/appdata/casedesk

# Bestimmte Version pullen
docker compose -f docker-compose.unraid.yml pull \
  ghcr.io/anditrenter/casedesk-ai/backend:v1.0.0 \
  ghcr.io/anditrenter/casedesk-ai/frontend:v1.0.0 \
  ghcr.io/anditrenter/casedesk-ai/ocr:v1.0.0

# Neu starten
docker compose -f docker-compose.unraid.yml up -d
```

---

## ⚠️ Fehlerbehandlung

### Update schlägt fehl

1. Alte Container laufen weiter
2. Fehlermeldung im Portal
3. Logs prüfen: `docker logs casedesk-backend`

### Healthcheck schlägt fehl

1. Update wird als "fehlgeschlagen" markiert
2. Rollback-Option wird angeboten
3. Container läuft trotzdem (ggf. mit Fehlern)

---

## 🔐 Sicherheit

- `.env` wird NIEMALS überschrieben
- API Keys bleiben lokal
- Keine Credentials werden verändert
- Update nur für Admins möglich

---

## 📡 API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/system/version` | GET | Lokale Version |
| `/api/system/check-update` | GET | Prüft auf Updates |
| `/api/system/changelog` | GET | Lädt Changelog |
| `/api/system/update` | POST | Führt Update aus |
| `/api/system/rollback` | POST | Rollback zur vorherigen Version |

---

## 🧪 Entwickler: Neues Release erstellen

### 1. Code ändern
```bash
git add .
git commit -m "feat: Neue Funktion XY"
```

### 2. version.json aktualisieren
```json
{
  "version": "1.0.2",
  "release_date": "2025-07-26",
  "release_notes": "Neue Funktion XY"
}
```

### 3. CHANGELOG.md aktualisieren
```markdown
## [1.0.2] - 2025-07-26

### Hinzugefügt
- Neue Funktion XY
```

### 4. Release erstellen
```bash
git tag v1.0.2
git push origin main --tags
```

### 5. GitHub Actions baut automatisch:
- `ghcr.io/.../backend:v1.0.2`
- `ghcr.io/.../backend:latest`
- (gleiches für frontend und ocr)

---

## 📞 Support

Bei Problemen:
1. Logs prüfen: `docker logs casedesk-backend`
2. GitHub Issues: https://github.com/AndiTrenter/CaseDesk-AI/issues
