# CaseDesk AI - Changelog

## Version 1.5.1 (2026-04-16) - BUGFIX: KI-Vorschläge bei E-Mail-Anhängen

### 🚨 Kritische Fixes
- **BEHOBEN**: `KI-Vorschläge fehlgeschlagen` bei E-Mail-Anhängen
  - **Root Cause**: `ocr_text` wurde als `None` initialisiert. Der `suggest-metadata` Endpoint crashte mit `TypeError: 'NoneType' object is not subscriptable` bei `None[:3000]`
  - `ocr_text` wird jetzt als `""` statt `None` initialisiert (email_service.py, documents.py)
  - Sicheres None-Handling mit `(doc.get("ocr_text") or "")` Pattern überall

### ✨ Verbesserungen
- **Automatische Text-Extraktion**: Wenn ein Dokument keinen Text hat, versucht der `suggest-metadata` Endpoint automatisch Text zu extrahieren (On-the-fly OCR)
- **Bessere Fehlermeldungen**: Statt generischem "fehlgeschlagen" zeigt die App jetzt "Kein Text im Dokument gefunden" an

### 📦 Dateien geändert
- `backend/routers/ai.py` (None-Handling + On-the-fly Text-Extraktion)
- `backend/email_service.py` (ocr_text: None → "")
- `backend/routers/documents.py` (ocr_text: None → "" + sicheres Reprocess)
- `backend/background_sync.py` (None-Handling bei AI-Analyse)
- `frontend/src/pages/Documents.js` (bessere Fehlermeldungen)
- `version.json` (Release-Notes aktualisiert)

## Version 1.4.0 (2026-04-08) - KRITISCHER BUGFIX RELEASE

### 🚨 Kritische Fixes
- **BEHOBEN**: `calendarload.error` - Robustes Date-Parsing für Legacy-Datenbank
  - MongoDB mit malformed date-strings (`'2026-04-09T'`, `'2026-04-09T:00'`) wird jetzt korrekt behandelt
  - Neue `safe_parse_datetime()` Funktion in `/backend/routers/date_utils.py`
  - Alle date fields werden robust geparst und korrigiert
  - Fehlerhafte Events/Tasks werden übersprungen statt die gesamte App zu crashen

- **BEHOBEN**: E-Mail-Versand Black Screen
  - `finally`-Block in handleSendEmail() stellt sicher, dass UI-State immer zurückgesetzt wird
  - Kein Black Screen mehr nach E-Mail-Versand

### ✨ Verbesserungen
- **Dokumenten-Icons mit Farben**: 
  - PDF = Rot, Word = Blau, Excel = Grün, Bilder = Blau
  - Dateityp-Labels ("PDF", "Word", "Excel", "Bild")
  - Icons skalieren bei Hover für bessere UX

### 🔧 Technische Änderungen
- Verbesserte Error-Handling in `/backend/routers/events.py`
- Verbesserte Error-Handling in `/backend/routers/tasks.py`
- Logger zu Events- und Tasks-Routern hinzugefügt
- Try-catch Blöcke für robustere API-Antworten
- Leere Arrays statt Crashes bei DB-Fehlern

### 📦 Dateien geändert
- `backend/routers/date_utils.py` (NEU)
- `backend/routers/events.py`
- `backend/routers/tasks.py`
- `backend/server.py` (Version auf 1.4.0)
- `backend/routers/auth.py` (Version auf 1.4.0)
- `frontend/src/pages/Emails.js`
- `frontend/src/pages/Documents.js`

### 🧪 Testing
- 13/13 Backend-Tests bestanden
- Alle Frontend-Seiten laden korrekt
- Date-Parsing testet alle malformed Formate

---

## Upgrade-Anleitung

Siehe [UNRAID_UPDATE_BEFEHLE.md](./UNRAID_UPDATE_BEFEHLE.md) für detaillierte Anweisungen.

**Kurzversion**:
```bash
cd /mnt/user/appdata/casedesk
git pull
docker-compose -f docker-compose.unraid.yml down
docker-compose -f docker-compose.unraid.yml build --no-cache backend frontend
docker-compose -f docker-compose.unraid.yml up -d
```
