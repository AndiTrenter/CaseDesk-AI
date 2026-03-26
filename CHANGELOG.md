# Changelog

Alle wichtigen Änderungen an CaseDesk AI werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt verwendet [Semantische Versionierung](https://semver.org/lang/de/).

## Versionierung

- **v1.x.x** - Verbesserungen und Bugfixes am bestehenden System
- **v2.x.x** - Grundlegende neue Features (z.B. Kontaktliste, neue Module)
- **v3.x.x** - Major Architekturänderungen

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

### Technisch
- Neuer Backend-Router `/api/system` für Update-Funktionen
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
2. GitHub Issues: https://github.com/AndiTrenter/CaseDesk-AI/issues
