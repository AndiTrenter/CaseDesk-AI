# Changelog

Alle wichtigen Änderungen an CaseDesk AI werden hier dokumentiert.

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

### Geändert
- Docker-Container ohne künstliche Ressourcen-Limits (nutzt verfügbaren Host-Speicher)
- AI_PROVIDER standardmäßig auf "openai" statt "disabled"
- Konsistente Port-Konfiguration (9090) in allen Dateien

### Entfernt
- Externe Abhängigkeiten von Emergent-Services

---

## Installation

```bash
cd /mnt/user/appdata
git clone https://github.com/AndiTrenter/CaseDesk-AI.git casedesk
cd casedesk
cp .env.example .env
nano .env  # OPENAI_API_KEY eintragen
docker compose -f docker-compose.unraid.yml up -d
```

Zugriff: **http://[DEINE-IP]:9090**
