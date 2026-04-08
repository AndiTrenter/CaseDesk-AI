# Changelog

Alle wichtigen Änderungen an CaseDesk AI werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt verwendet [Semantische Versionierung](https://semver.org/lang/de/).

## Versionierung

- **v1.x.x** - Verbesserungen und Bugfixes am bestehenden System
- **v2.x.x** - Grundlegende neue Features (z.B. Kontaktliste, neue Module)
- **v3.x.x** - Major Architekturänderungen

---

## [1.3.0] - 2026-04-08

### 🎉 PRODUCTION-READY RELEASE

#### 🔧 Fixes für lokale Installationen (Unraid)
- ✅ **Kalender:** Events laden korrekt (keine "Failed to load events")
- ✅ **Tasks:** Funktionieren vollständig
- ✅ **Dokument-Vorschau:** window.location.origin für korrekte URLs
- ✅ **E-Mail-Integration:** KI hat Zugriff auf E-Mail-Inhalte
- ✅ **Testing:** 100% Backend-Tests bestanden (17/17)

#### 📦 Deployment
- ✅ **Lokales Bauen:** docker-compose.yml mit build-Kontext
- ✅ **Update-Script:** Automatisches Update-Script für Unraid
- ✅ **Dokumentation:** Gmail-Einrichtung, KI-Assistent-Anleitung, Ollama-Installation

#### 🐛 Bug-Fixes
- Fixed Document model field mismatch (filename vs original_filename)
- Fixed Calendar.js robust error handling
- Fixed API URL generation für lokale IPs

---

## [1.2.0] - 2026-04-08

### 🔧 BUGFIX - Kalender-Events laden

#### Kalender-Fix (`Calendar.js`)
- ✅ **FIXED:** "Failed to load events" - Besseres Error-Handling
- ✅ **Robustheit:** Unterstützt jetzt beide Response-Formate (Array direkt oder `{data: array}`)
- ✅ **Logging:** Detaillierte Console-Logs für Debugging
- ✅ **Fallback:** Leeres Array bei Fehler, statt Absturz

#### KI-Assistent: Event-Erstellung
- ✅ **Backend:** `/ai/execute-action` mit `action_type='create_event'` funktioniert
- ✅ **Automatisch:** KI kann Termine aus natürlicher Sprache erstellen
  - Beispiel: "Erstelle einen Termin am 15. April um 14 Uhr für Zahnarzt"
- ✅ **Erinnerungen:** Optional Reminder-Tasks erstellen
- ✅ **Aus Dokumenten:** Automatische Termin-Extraktion aus E-Mails/Dokumenten

#### Bekannte Events-Features
- 📅 Termine manuell erstellen
- 🔔 Erinnerungen (5 Min bis 2 Wochen vorher)
- 📍 Orte hinzufügen
- 🔗 Mit Fällen verknüpfen
- 🤖 KI-gestützte Erstellung via Chat

---

## [1.1.9] - 2026-04-08

### 🔧 BUGFIX - Dokument-Vorschau & E-Mail-Integration

#### Dokument-Vorschau-Fix (`api.js`)
- ✅ **FIXED:** `viewUrl` und `downloadUrl` verwenden jetzt `window.location.origin`
- ✅ **Behebt:** Relative URLs funktionieren nicht in `<iframe>` und `<img>` src-Attributen
- ✅ **Ergebnis:** Dokument-Vorschau funktioniert jetzt korrekt auf lokalen Installationen

#### KI-Assistent: E-Mail-Inhalte-Integration (`ai.py`, `ai_service.py`)
- 📧 **Neu:** KI-Assistent hat jetzt vollständigen Zugriff auf E-Mail-Inhalte (nicht nur Anhänge)
- 📧 **E-Mail-Body:** `body_text` wird in den KI-Kontext geladen
- 📧 **Fähigkeiten erweitert:**
  - E-Mail-Inhalte durchsuchen
  - Informationen aus E-Mails extrahieren
  - Termine/Aufgaben aus E-Mails identifizieren
  - Verbindungen zwischen E-Mails und Fällen herstellen
- 🇩🇪🇬🇧🇫🇷🇪🇸 **Mehrsprachig:** System-Prompts für DE/EN/FR/ES aktualisiert

#### Technische Details
- **Frontend:** `documentUpdateAPI.viewUrl()` nutzt absolute URLs
- **Backend:** `all_emails` Collection wird in Chat-Kontext geladen
- **AI Service:** E-Mail-Wissen in System-Prompt dokumentiert

---

## [1.1.8] - 2026-04-08

### 🔄 ARCHITEKTUR-ÄNDERUNG - Ollama-Entkopplung

#### Ollama aus CaseDesk entfernt
- ❌ **Entfernt:** `ollama` und `ollama-init` Services aus `docker-compose.unraid.yml`
- ✅ **Neu:** Externe Ollama-Installation via Unraid Community Apps
- 🔗 **Backend:** Unterstützt jetzt externe Ollama-URLs (z.B. `http://192.168.1.140:11434`)
- 📝 **Dokumentation:** Neue Anleitung `UNRAID_OLLAMA_INSTALLATION.md`

#### Vorteile
- ✅ Ollama läuft unabhängig von CaseDesk
- ✅ Modelle bleiben bei CaseDesk-Updates erhalten
- ✅ Open WebUI kann parallel genutzt werden
- ✅ Einfachere Verwaltung über Unraid WebUI
- ✅ Kann von mehreren Apps gleichzeitig genutzt werden

#### Migration
Siehe `UNRAID_OLLAMA_INSTALLATION.md` für Schritt-für-Schritt Anleitung.

---

## [1.1.7] - 2026-04-08

### 🔧 BUGFIX - OpenAI API-Key Eingabe und Speicherung

#### Backend-Verbesserungen (`settings.py`)
- ✅ **Verbessertes API-Key Handling:**
  - API-Key wird automatisch getrimmt (Leerzeichen entfernt)
  - Besseres Logging beim Speichern des Keys
  - Erster/Letzter Zeichenbereich wird zur Verifikation angezeigt
  - Neuer DELETE-Endpunkt zum Zurücksetzen des API-Keys

#### Frontend-Verbesserungen (`Settings.js`)
- 👁️ **Show/Hide Button** für API-Key Eingabefeld (Passwort-Feld mit Auge-Symbol)
- 🗑️ **"Löschen"-Button** zum Entfernen des alten API-Keys
- ℹ️ **Besseres Feedback:**
  - Anzeige der ersten/letzten Zeichen des gespeicherten Keys (z.B. "sk-proj-...X1Y2")
  - Klarere Platzhalter-Texte
  - Hinweis zum Key-Format ("beginnt mit sk-proj- oder sk-")
- 🎨 **Verbesserte UX:** Eye/EyeOff Icons für bessere Sichtbarkeit

#### Behebt:
- ❌ API-Key wurde nicht korrekt gespeichert
- ❌ Benutzer konnte nicht sehen, ob Key korrekt eingegeben wurde
- ❌ Keine Möglichkeit, alten ungültigen Key zu löschen

---

## [1.1.5] - 2026-04-07

### 🔴 KRITISCHER FIX - Tasks & Kalender für lokale Installationen

- 🔧 **API-URL Erkennung komplett überarbeitet**
  - Lokale Installationen (IP-Adressen wie 192.168.x.x, 10.x.x.x, localhost) verwenden IMMER relative URLs
  - Preview-Umgebungen verwenden IMMER die konfigurierte URL
  - **Behebt endgültig:**
    - "Failed to load tasks"
    - Kalendereinträge nicht sichtbar
    - Alle API-Fehler auf lokalen Installationen

### Technische Details
```javascript
// Neue robuste Erkennung in api.js:
const isLocalInstallation = 
  currentHostname === 'localhost' ||
  currentHostname.startsWith('192.168.') ||
  currentHostname.startsWith('10.') ||
  /^\d+\.\d+\.\d+\.\d+$/.test(currentHostname);

if (isLocalInstallation) {
  return '';  // Relative URLs -> nginx proxy
}
```

### ⚠️ WICHTIG für Updates
Nach dem Update müssen Sie die **Docker-Images neu bauen**:
```bash
# Auf Ihrem Unraid/Server:
cd /path/to/casedesk
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

Oder über Portainer: Container stoppen → Image löschen → Neu erstellen

---

## [1.1.4] - 2026-04-07

### Neu hinzugefügt

- 📊 **Excel-Formate lesen**
  - `.xlsx` (Excel 2007+) - Vollständige Textextraktion mit Tabellen
  - `.xls` (Excel 97-2003) - Legacy Excel-Dateien
  - `.ods` (OpenDocument Spreadsheet) - LibreOffice Calc

- 📝 **Word-Dokumente erstellen**
  - Neuer API-Endpoint: `POST /api/documents/generate-word`
  - **Brief-Vorlage**: Formeller Brief mit Absender, Empfänger, Datum, Betreff
  - **Bericht-Vorlage**: Einfaches Dokument mit Titel und Inhalt
  - **Vertrag-Vorlage**: Dokument mit Parteien und Unterschriftsbereich
  - Generierte Dokumente werden automatisch in der Dokumentenbibliothek gespeichert

### Unterstützte Dokumentformate (komplett)

| Kategorie | Format | Dateiendung | Lesen | Erstellen |
|-----------|--------|-------------|-------|-----------|
| **Text** | Word 2007+ | .docx | ✅ | ✅ |
| | Word Legacy | .doc | ✅ | ❌ |
| | OpenDocument | .odt | ✅ | ❌ |
| | Rich Text | .rtf | ✅ | ❌ |
| | Plain Text | .txt, .md | ✅ | ❌ |
| **Tabellen** | Excel 2007+ | .xlsx | ✅ | ❌ |
| | Excel Legacy | .xls | ✅ | ❌ |
| | OpenDocument | .ods | ✅ | ❌ |
| **Bilder** | PNG/JPG/TIFF | .png, .jpg | ✅ (OCR) | ❌ |
| **PDF** | PDF | .pdf | ✅ (OCR) | ❌ |

### Neue Python-Abhängigkeiten
- `openpyxl` - Excel 2007+ Unterstützung
- `xlrd` - Excel 97-2003 Unterstützung
- `odfpy` - OpenDocument Unterstützung

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
