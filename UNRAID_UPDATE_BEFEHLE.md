# CaseDesk AI - Unraid Update Anleitung

## ✅ Funktionierende Update-Befehle

Führen Sie diese Befehle **nacheinander** auf Ihrem Unraid-Server aus:

```bash
# 1. Zum CaseDesk-Verzeichnis wechseln
cd /mnt/user/appdata/casedesk

# 2. Neueste Änderungen von GitHub holen
git pull

# 3. Container stoppen (wichtig!)
docker-compose -f docker-compose.unraid.yml down

# 4. Alte Images entfernen (für sauberen Build)
docker-compose -f docker-compose.unraid.yml rm -f backend frontend

# 5. Container neu bauen (mit --no-cache)
docker-compose -f docker-compose.unraid.yml build --no-cache backend frontend

# 6. Container starten
docker-compose -f docker-compose.unraid.yml up -d

# 7. Status prüfen (alle Container sollten "Up" sein)
docker-compose -f docker-compose.unraid.yml ps

# 8. Backend-Logs prüfen (sollte KEINE datetime-Errors mehr zeigen)
docker logs casedesk-backend --tail 50
```

## 🔍 Erfolgreiche Updates erkennen

Nach dem Update sollten Sie sehen:

✅ **In den Logs**:
- KEINE `datetime_from_date_parsing` Errors
- Backend startet ohne Import-Fehler
- `Background email sync started` erscheint

✅ **Im Browser**:
- Kalender lädt ohne `calendarload.error`
- Aufgaben laden korrekt
- Dokumente zeigen farbige Icons

## ❌ Falls es immer noch nicht funktioniert

```bash
# Kompletter Neustart aller Container:
cd /mnt/user/appdata/casedesk
docker-compose -f docker-compose.unraid.yml down
docker-compose -f docker-compose.unraid.yml up -d --build --force-recreate
```

## 📝 Was wurde geändert

- `backend/routers/date_utils.py` - Neue robuste Date-Parsing-Funktion
- `backend/routers/events.py` - Verwendet jetzt safe_parse_datetime()
- `backend/routers/tasks.py` - Verwendet jetzt safe_parse_datetime()
- `frontend/src/pages/Emails.js` - finally-Block gegen Black Screen
- `frontend/src/pages/Documents.js` - Farbige Icons mit Dateityp-Labels
