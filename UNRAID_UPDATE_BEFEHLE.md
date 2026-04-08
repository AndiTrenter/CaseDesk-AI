# CaseDesk AI - Unraid Update Anleitung v1.4.0

## ✅ Was wurde in v1.4.0 behoben:
1. 🚨 **Calendar/Tasks `calendarload.error`** - Robustes Date-Parsing für malformed DB-Daten
2. ⚠️ **E-Mail-Versand Black Screen** - finally-Block verhindert UI-Freeze
3. ⚠️ **Dokumenten-Icons** - Farbige Icons (PDF=rot, Word=blau) mit Dateityp-Labels

## 📦 KOMPLETTE Update-Befehle

Führen Sie diese Befehle **nacheinander** auf Ihrem Unraid-Server aus:

```bash
# 1. Zum Verzeichnis wechseln
cd /mnt/user/appdata/casedesk

# 2. Änderungen von GitHub holen
git pull

# 3. Container STOPPEN (wichtig!)
docker-compose -f docker-compose.unraid.yml down

# 4. Alte Images entfernen
docker-compose -f docker-compose.unraid.yml rm -f backend frontend

# 5. Container NEU BAUEN (mit --no-cache für sauberen Build)
docker-compose -f docker-compose.unraid.yml build --no-cache backend frontend

# 6. Container STARTEN
docker-compose -f docker-compose.unraid.yml up -d

# 7. Status überprüfen (alle sollten "Up" sein)
docker-compose -f docker-compose.unraid.yml ps

# 8. Backend-Logs prüfen (sollte Version 1.4.0 zeigen)
docker logs casedesk-backend --tail 50 | grep -E "version|ERROR|datetime"
```

## 🔍 Erfolg überprüfen:

**In den Backend-Logs sollten Sie sehen**:
```
✅ "version": "1.4.0"
✅ KEINE "datetime_from_date_parsing" Errors
✅ "Background email sync started"
```

**Im Browser sollte funktionieren**:
```
✅ Kalender lädt ohne "calendarload.error"
✅ Aufgaben laden korrekt
✅ Dokumente zeigen farbige Icons mit Labels
✅ E-Mail-Versand kein Black Screen
```

## ❌ Falls es IMMER NOCH nicht funktioniert:

### Option 1: Kompletter Neustart mit force-recreate
```bash
cd /mnt/user/appdata/casedesk
docker-compose -f docker-compose.unraid.yml down
docker-compose -f docker-compose.unraid.yml up -d --build --force-recreate
```

### Option 2: Prüfen Sie die Logs im Detail
```bash
# Backend-Logs (schauen Sie nach Import-Errors)
docker logs casedesk-backend --tail 100

# Frontend-Logs
docker logs casedesk-frontend --tail 50
```

### Option 3: Alte Images komplett entfernen
```bash
cd /mnt/user/appdata/casedesk
docker-compose -f docker-compose.unraid.yml down
docker rmi casedesk-backend casedesk-frontend
docker-compose -f docker-compose.unraid.yml build --no-cache
docker-compose -f docker-compose.unraid.yml up -d
```

## 📝 Wichtige Hinweise

1. **`down` ist essentiell**: Ohne `down` können alte Container-Prozesse die neuen Änderungen blockieren
2. **`--no-cache`**: Stellt sicher, dass Docker die neuesten Änderungen verwendet
3. **Geduld**: Der Build-Prozess kann 2-5 Minuten dauern
4. **Browser-Cache**: Leeren Sie Ihren Browser-Cache (`Ctrl+Shift+R`) nach dem Update

## 🆘 Support

Falls das Problem weiterhin besteht, senden Sie mir:
1. Screenshot von `docker logs casedesk-backend --tail 100`
2. Screenshot von `docker-compose -f docker-compose.unraid.yml ps`
3. Screenshot vom Browser mit geöffneter Browser-Console (F12)

