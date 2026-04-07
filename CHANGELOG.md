# Changelog

Alle wichtigen Änderungen an CaseDesk AI werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt verwendet [Semantische Versionierung](https://semver.org/lang/de/).

## Versionierung

- **v1.x.x** - Verbesserungen und Bugfixes am bestehenden System
- **v2.x.x** - Grundlegende neue Features (z.B. Kontaktliste, neue Module)
- **v3.x.x** - Major Architekturänderungen

---

## [1.1.3] - 2026-04-07

### Neu hinzugefügt

- 📄 **Unterstützung für Word-Dokumente (.docx, .doc)**
  - Textextraktion aus Microsoft Word Dokumenten
  - Sowohl neue (.docx) als auch alte (.doc) Formate

- 📄 **Unterstützung für OpenDocument (.odt)**
  - LibreOffice/OpenOffice Dokumente werden jetzt unterstützt
  - Vollständige Textextraktion

- 📄 **Unterstützung für weitere Formate**
  - RTF (Rich Text Format)
  - TXT, CSV, MD (Textdateien)
  
### Verbessert

- 🔄 **Reprocess-Funktion erweitert**
  - Neuer `force` Parameter um bereits verarbeitete Dokumente neu zu analysieren
  - Bessere Logging-Ausgabe

### Unterstützte Dokumentformate (komplett)
| Format | Dateiendung | Status |
|--------|-------------|--------|
| PDF | .pdf | ✅ OCR + Textextraktion |
| Word 2007+ | .docx | ✅ Textextraktion |
| Word Legacy | .doc | ✅ Textextraktion |
| OpenDocument | .odt | ✅ Textextraktion |
| Rich Text | .rtf | ✅ Textextraktion |
| Plain Text | .txt, .csv, .md | ✅ Textextraktion |
| Bilder | .png, .jpg, .tiff | ✅ OCR |

### Hinweis
Bereits hochgeladene Dokumente können über den "Neu verarbeiten" Button oder via API mit `?force=true` erneut analysiert werden.

---

## [1.1.2] - 2026-04-07

### 🔴 KRITISCHER BUGFIX

- 🔧 **Task Status Validation Error behoben**
  - Fehler: `"Input should be 'todo', 'in_progress' or 'done'" - input: 'open'`
  - Tasks mit Status `open`, `pending`, `completed` werden jetzt akzeptiert
  - Automatische Normalisierung: `open` → `todo`, `completed` → `done`
  - Task-Modell ist jetzt flexibler (akzeptiert alle String-Werte)

### Behoben
- 🔧 **"Failed to load tasks"** - Verursacht durch Pydantic Validation Error
- 🔧 **26 Validation Errors** in der Response wurden behoben
- 🔧 **Legacy Status-Werte** werden jetzt automatisch gemappt

### Technische Details
- `/app/backend/models.py` - Task-Modelle verwenden jetzt `str` statt Enum
- `/app/backend/routers/tasks.py` - Status-Normalisierung hinzugefügt

---

## [1.1.1] - 2026-04-06

### 🔴 KRITISCHER FIX

- 🔧 **Automatische Backend-URL Erkennung**
  - Frontend erkennt jetzt automatisch ob lokale Installation oder Preview
  - Lokale Installationen (IP-Adressen, localhost) verwenden relative URLs
  - Preview-Umgebung verwendet weiterhin die konfigurierte URL
  - **Behebt definitiv:**
    - "Failed to load tasks"
    - "Authentication required" bei allen API-Aufrufen
    - Kalendereinträge erstellen funktioniert nicht
    - Dokumenten-Download/Preview

### Technische Details
- `api.js` prüft jetzt den aktuellen Hostnamen
- Wenn der Host eine IP-Adresse ist oder "localhost", wird automatisch relative URL verwendet
- Keine manuelle Konfiguration der `.env` Datei mehr nötig

---

## [1.1.0] - 2026-04-06

### 🔴 KRITISCHER FIX

- 🔧 **Backend-URL für lokale Installationen korrigiert**
  - `REACT_APP_BACKEND_URL` ist jetzt standardmäßig leer
  - Frontend verwendet automatisch relative URLs (nginx proxy)
  - Behebt: "Authentication required", "Failed to load tasks"
  - Behebt: Dokument-Download/Preview funktioniert nicht

### Neu hinzugefügt (aus v1.0.8-1.0.9)
- 📦 **ZIP-Download** - Alle Dokumente eines Falls mit einem Klick herunterladen
- 🤖 **KI-Dokumentenvorschläge** - KI schlägt passende Dokumente für Fälle vor
- ✅ **Mehrfachauswahl** - Mehrere Dokumente auf einmal zu Fall hinzufügen
- 🔐 **Token-basierte Downloads** - Sichere temporäre Tokens für Dokument-Zugriff

### Behoben
- 🔧 **"Failed to load tasks"** - Funktioniert jetzt auf lokalen Installationen
- 🔧 **"Authentication required"** bei Downloads - Behoben
- 🔧 **Dokumenten-Vorschau** - Zeigt jetzt PDFs und Bilder korrekt an
- 🔧 **Settings-Persistence** - Einstellungen werden korrekt gespeichert

### Upgrade-Hinweis
Nach dem Update sollte alles automatisch funktionieren. Falls nicht:
1. Container/Dienste neu starten
2. Browser-Cache leeren (Strg+Shift+R)

---

## [1.0.9] - 2026-04-06

### Neu hinzugefügt
- 📦 **ZIP-Download für alle Fall-Dokumente**
  - Neuer Button "Alle als ZIP" bei Falldetails → Dokumente
  - Lädt alle Dokumente eines Falls in einem ZIP-Archiv herunter
  - Perfekt zum schnellen Zusammenstellen von Unterlagen

- 🔐 **Token-basierte Dokumenten-Vorschau**
  - Dokumente werden jetzt mit temporärem Token angezeigt
  - Behebt "Unauthorized" Fehler bei Dokumenten-Preview
  - Funktioniert für Bilder, PDFs und andere Dateitypen

### Verbessert
- 📄 **Dokumenten-Dialog** komplett überarbeitet
  - Ladeanimation während Vorschau geladen wird
  - Bessere Fehlerbehandlung
  - Download-Button mit Fortschrittsanzeige

### Behoben
- 🔧 **Dokumenten-Preview "Unauthorized"** - Jetzt mit Token-Auth
- 🔧 **Download-Funktion** - Verwendet jetzt Token statt direktem Auth-Header

---

## [1.0.8] - 2026-04-06

### Neu hinzugefügt
- 🤖 **KI-Dokumentenvorschläge für Fälle**
  - Neuer Button "KI Vorschläge" bei Falldetails → Dokumente
  - KI analysiert den Fall und schlägt passende unverknüpfte Dokumente vor
  - Zeigt Begründung warum das Dokument relevant sein könnte
  - Neuer API-Endpoint: `GET /api/documents/suggest-for-case/{case_id}`

- ✅ **Verbesserte Mehrfachauswahl bei Dokumenten**
  - Dokumente können nun gesammelt und dann alle auf einmal hinzugefügt werden
  - "Alle auswählen" / "Alle abwählen" Button
  - Anzeige wie viele Dokumente ausgewählt sind
  - Bestätigungsbutton um alle ausgewählten Dokumente hinzuzufügen

### Verbessert
- 📄 Dialog "Vorhandenes verknüpfen" mit echter Mehrfachauswahl
- 🎨 Visuelle Hervorhebung ausgewählter Dokumente

---

## [1.0.7] - 2026-04-06

### 🔴 KRITISCHER BUGFIX

- 🔧 **Settings werden jetzt korrekt gespeichert**
  - OpenAI API-Key wird nicht mehr "vergessen"
  - KI-Provider Einstellungen werden persistent gespeichert
  - Problem: Bei frischer Installation wurden Einstellungen nicht in DB geschrieben
  - Lösung: `upsert=True` zu MongoDB update_one() hinzugefügt

### Behoben
- ⚙️ **PUT /api/settings/system** - Einstellungen werden jetzt mit upsert=True gespeichert
- ⚙️ **PUT /api/settings/storage** - Speicherlimits werden jetzt mit upsert=True gespeichert
- 🤖 **KI-Service Aktivierung** - Nach dem Speichern ist der KI-Service sofort verfügbar

### Was jetzt funktioniert
- ✅ OpenAI API-Key speichern und verwenden
- ✅ KI-Assistent kann Termine und Aufgaben aus dem Chat erstellen
- ✅ Automatische Frist-/Termin-Erkennung aus hochgeladenen Dokumenten
- ✅ Dokumente werden automatisch analysiert

### Upgrade-Hinweis
Nach dem Update müssen Sie Ihre KI-Einstellungen **einmal neu speichern**:
1. Einstellungen → KI-Konfiguration
2. OpenAI auswählen + API-Key eingeben
3. "Speichern" klicken

---

## [1.0.4] - 2025-07-26

### Hinzugefügt
- 🤖 **Ollama als Standard-Service**
  - Ollama Docker-Container wird automatisch mit CaseDesk gestartet
  - **Modell wird automatisch heruntergeladen** (kein manueller Befehl mehr nötig!)
  - ollama-init Container lädt `llama3.2` beim ersten Start
  
- 🔄 **Automatischer KI-Fallback**
  - Bei OpenAI-Fehlern (Rate Limit, ungültiger Key, Verbindungsproblem) automatischer Wechsel zu Ollama
  - Bei Internetausfall weiterhin KI-Funktionen über lokales Ollama
  - Kein manuelles Umschalten nötig

- 📊 **Erweitertes Health-Dashboard**
  - Ollama und OpenAI werden IMMER im Status angezeigt
  - "Aktiv"-Indikator zeigt welcher Provider gerade verwendet wird
  - Hinweis wenn Ollama-Modell noch nicht installiert ist
  - Anzeige ob Fallback verfügbar ist

### Behoben
- 🔑 **OpenAI API-Key Problem behoben**
  - API-Key aus UI-Einstellungen wird jetzt korrekt gespeichert und verwendet
  - Datenbank-Key wird verwendet wenn keine Umgebungsvariable gesetzt ist
  - Bessere Fehlermeldungen bei ungültigem API-Key

- ⚡ **KI-Provider Umschaltung**
  - Wechsel zwischen "Lokal" (Ollama) und "OpenAI" funktioniert jetzt zuverlässig
  - Einstellungen werden sofort wirksam

### Geändert
- Docker Compose: Ollama ist jetzt Pflicht-Service (nicht mehr optional via --profile)
- Neuer `ollama-init` Container für automatischen Modell-Download
- Backend hängt von Ollama ab (depends_on: ollama)
- Verbesserte Fehlerbehandlung für OpenAI (AuthenticationError, RateLimitError, etc.)

### Technisch
- `AIService` Klasse mit `enable_fallback` Parameter
- `get_ai_service()` prüft Umgebungsvariablen UND Datenbank-Einstellungen
- Health-Check zeigt immer beide KI-Provider an
- OLLAMA_URL Standard geändert von localhost auf http://ollama:11434
- Healthcheck für Ollama-Container hinzugefügt

---

## [1.0.3] - 2025-03-26

### Hinzugefügt
- ✉️ **KI E-Mail-Komposition mit Kontext**
- 🎯 **Dynamische Versionierung**
- 📢 **Update-Banner**
- 🔄 **Verbessertes Update-System**

---

## [1.0.2] - 2025-07-25

### Hinzugefügt
- 🔍 **E-Mail Suche**
  - Suchfeld für Stichwort, Absender, Betreff
  - Durchsucht auch KI-Zusammenfassungen
  - Schnelle Filterung der E-Mail-Liste
- 📅 **Kalender Verbesserungen**
  - Einträge werden als farbige Banner angezeigt (wie Outlook)
  - Mehrere Einträge am gleichen Tag haben unterschiedliche Farben
  - Bis zu 3 Einträge sichtbar, "+X mehr" für weitere
- 📄 **Dokumente Kachel-Ansicht**
  - Neues Kachel-Layout wie bei Paperless
  - Neueste Dokumente zuerst
  - Quelle angezeigt (E-Mail oder Upload)
  - Datum des Dokuments sichtbar
  - Klick öffnet Vollansicht im Popup
- ✅ **Aufgaben DONE einklappbar**
  - Erledigte Aufgaben können eingeklappt werden
  - Spart Platz, bessere Übersicht

### Behoben
- 🌐 Standard-Sprache ist jetzt Deutsch (nicht mehr Englisch)
- 🔧 Tasks-Laden funktioniert wieder (AnimatePresence-Bug behoben)

---

## [1.0.1] - 2025-07-25

### Hinzugefügt
- 🔄 **Integriertes Update-System**
  - Automatische Erkennung neuer Versionen
  - Update-Installation direkt im Portal (keine Terminal-Befehle nötig)
  - Changelog-Anzeige im Portal vor Update
  - Healthcheck nach Update zur Verifizierung
  - Rollback-Möglichkeit zur vorherigen Version
- 📋 **Changelog im Portal**
  - Vollständige Versionshistorie einsehbar
  - Detaillierte Release Notes vor jedem Update
- 📖 **Update-Dokumentation**
  - Neue README_UPDATE_SYSTEM.md mit detaillierter Anleitung
- 📧 **Automatische Dokumenten-Verarbeitung**
  - E-Mail-Anhänge werden automatisch als Dokumente importiert
  - PDFs und Bilder werden automatisch OCR-verarbeitet (Tesseract)
  - KI analysiert importierte Dokumente automatisch
  - Erkannte Fristen werden als Aufgaben erstellt
  - Dokument-Inhalte stehen der KI als Wissen zur Verfügung
  - Perfekt für Scanner → E-Mail → CaseDesk Workflow
- ✏️ **E-Mail-Konto bearbeiten**
  - Bestehende E-Mail-Konten können jetzt bearbeitet werden
  - Sync-Intervall einstellbar (1 Min bis stündlich)
  - Passwort-Felder mit Sichtbarkeits-Toggle (Auge-Symbol)
- 🔗 **E-Mail Verbindungstest**
  - IMAP und SMTP Verbindung vor dem Speichern testen
  - Hilfreiche Fehlermeldungen inkl. Gmail App-Passwort Hinweis
- 🐘 **MongoDB 4.4 Kompatibilität**
  - Standard-MongoDB-Version auf 4.4 geändert (für CPUs ohne AVX)
  - Konfigurierbar via MONGO_VERSION in .env

### Technisch
- Neuer Backend-Router `/api/system` für Update-Funktionen
- Background-Sync mit vollständiger Dokumenten-Pipeline
- Tesseract OCR im Docker-Image (deutsch + englisch)
- GitHub Actions erweitert für semantische Versionierung
- Docker Images werden mit Version-Tags gepusht (z.B. `v1.0.1`)

---

## [1.0.0] - 2025-07-25

### Hinzugefügt
- 🤖 **KI-Aktionen im Chat**: Erstellen von Terminen, Aufgaben, Fällen und E-Mails durch natürliche Sprache
  - "Lege einen Termin für Luzias Geburtstag an"
  - "Erstelle eine Aufgabe: Steuererklärung abgeben"
  - "Schreibe eine E-Mail an die Krankenkasse wegen Zahlungsfristverlängerung"
- 🎤 **Spracheingabe im Chat**: Web Speech API für Deutsch (Chrome, Edge, Safari)
- 💾 **Admin-Speichereinstellungen**: Globale und pro-Benutzer Speicherlimits
- 📧 **E-Mail-Nachverfolgung**: Korrespondenz-Suche ("Wurde eine Zahlungsfristverlängerung beantragt?")
- 📝 **Erinnerungsdialog**: KI fragt nach Erinnerung bei Terminerstellung
- 📄 **Dokumentenverwaltung**: Upload, OCR, KI-Analyse, Tags, Suche
- 📁 **Fallverwaltung**: CRUD, Tabs, Dokumenten-Verknüpfung
- 📧 **E-Mail-Integration**: IMAP/SMTP mit automatischer KI-Analyse
- 📅 **Kalender & Aufgaben**: Fristerkennung, automatische Aufgaben
- 🤖 **KI-Assistent**: Chat mit Kontext (Dokument/Fall)
- 📝 **Antwort-Generierung**: PDF/DOCX mit Anlagen
- 👥 **Benutzerverwaltung**: Admin/User Rollen, Einladungen
- 💾 **Datenexport**: ZIP-Archiv
- 🌙 **Dark/Light Theme**
- 🔒 **100% Self-Hosted**: Keine Cloud-Abhängigkeiten

### Geändert
- Docker-Container ohne künstliche Ressourcen-Limits
- AI_PROVIDER standardmäßig auf "openai"
- Konsistente Port-Konfiguration (9090)

---

## Upgrade-Anleitung

### Von v1.0.3 auf v1.0.4

**Option 1: Über das Portal (empfohlen)**
1. Als Admin einloggen
2. Einstellungen → Updates
3. "Update installieren" klicken
4. Das Ollama-Modell wird **automatisch** heruntergeladen

**Option 2: Manuell**
```bash
cd /mnt/user/appdata/casedesk
docker compose -f docker-compose.unraid.yml pull
docker compose -f docker-compose.unraid.yml up -d
# Modell wird automatisch vom ollama-init Container geladen
# Prüfen mit: docker logs casedesk-ollama-init
```

### Von v1.0.0 auf v1.0.1

**Option 1: Über das Portal (empfohlen)**
1. Als Admin einloggen
2. Einstellungen → Updates
3. "Update installieren" klicken

**Option 2: Manuell**
```bash
cd /mnt/user/appdata/casedesk
docker compose -f docker-compose.unraid.yml pull
docker compose -f docker-compose.unraid.yml up -d
```

---

## Support

Bei Problemen:
1. Logs prüfen: `docker logs casedesk-backend`
2. Ollama-Status: `docker logs casedesk-ollama`
3. GitHub Issues: https://github.com/AndiTrenter/CaseDesk-AI/issues
