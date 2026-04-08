# 🔄 CaseDesk AI auf Unraid aktualisieren

## 🚀 **Methode 1: Automatisches Update-Script (EMPFOHLEN)**

### **Schritt 1: Terminal öffnen**
Unraid WebUI → Terminal (oben rechts)

### **Schritt 2: Ins CaseDesk-Verzeichnis wechseln**
```bash
cd /mnt/user/appdata/casedesk
```

### **Schritt 3: Update-Script ausführen**
```bash
./update.sh
```

**Das Script macht automatisch:**
1. ✅ Git pull (neueste Änderungen)
2. ✅ Container stoppen
3. ✅ Alte Images löschen
4. ✅ Neue Images lokal bauen
5. ✅ Container starten

⏳ **Dauer:** 5-10 Minuten

---

## 🔧 **Methode 2: Manuelles Update**

### **Falls das Update-Script nicht funktioniert:**

```bash
cd /mnt/user/appdata/casedesk

# 1. Neueste Änderungen holen
git pull origin main

# 2. Container stoppen
docker-compose -f docker-compose.unraid.yml down

# 3. Alte Images löschen
docker images | grep casedesk | awk '{print $3}' | xargs docker rmi -f 2>/dev/null

# 4. Neu bauen (LOKAL, nicht von GitHub pullen!)
docker-compose build --no-cache

# 5. Container starten
docker-compose -f docker-compose.unraid.yml up -d

# 6. Status prüfen
docker ps
docker logs casedesk-backend --tail 30
```

---

## ⚠️ **WICHTIG: Warum LOKAL bauen?**

### **Problem mit GitHub Images:**
- GitHub Actions baut Images NICHT automatisch bei jedem Push
- `docker-compose pull` holt **ALTE Images** von GitHub
- **Resultat:** Sie bekommen veraltete Versionen mit Bugs!

### **Lösung: Lokal bauen**
```bash
docker-compose build --no-cache
```

**Das verwendet Ihren lokalen Code (neueste Version von Git)!**

---

## 🎯 **Nach dem Update:**

### **1. Browser-Cache leeren**
- Öffnen Sie: `http://192.168.1.140:9090`
- Drücken Sie: **`Ctrl + Shift + R`** (Hard Reload)

### **2. Version prüfen**
- Unten links sollte stehen: **v1.3.0**
- Falls älter: Nochmal `Ctrl + Shift + R`

### **3. Funktionstest**
- ✅ Kalender öffnen → Termine laden
- ✅ Tasks öffnen → Aufgaben anzeigen
- ✅ Dokument hochladen → Vorschau öffnen
- ✅ Browser-Konsole (F12) → **KEINE 404-Fehler**

---

## 🐛 **Troubleshooting**

### **Problem: "Git pull" sagt "Already up to date"**

**Aber Sie wissen, dass es Updates gibt:**

```bash
git fetch origin
git reset --hard origin/main
```

⚠️ **ACHTUNG:** Lokale Änderungen gehen verloren!

---

### **Problem: Container starten nicht**

**Logs prüfen:**
```bash
docker-compose -f docker-compose.unraid.yml logs
```

**Container einzeln neu starten:**
```bash
docker-compose -f docker-compose.unraid.yml restart backend
docker-compose -f docker-compose.unraid.yml restart frontend
```

---

### **Problem: "Failed to load events" immer noch**

**1. Prüfen Sie, welches Image verwendet wird:**
```bash
docker images | grep casedesk
```

**Falls Sie sehen:**
- `ghcr.io/anditrenter/casedesk-ai/frontend:latest` → **ALTE Images von GitHub!**

**Lösung:**
```bash
docker rmi -f ghcr.io/anditrenter/casedesk-ai/frontend:latest
docker-compose build --no-cache frontend
docker-compose -f docker-compose.unraid.yml up -d
```

---

### **Problem: Browser zeigt alte Version**

**Browser-Cache komplett leeren:**

**Chrome:**
1. `Ctrl + Shift + Delete`
2. "Gesamter Zeitraum"
3. "Bilder und Dateien im Cache"
4. "Daten löschen"

**Oder:**
1. F12 → Application Tab
2. "Clear storage"
3. "Clear site data"

---

## 📅 **Update-Zeitplan**

### **Wann sollten Sie updaten?**
- ✅ Nach jedem GitHub-Push mit neuen Features
- ✅ Bei Bug-Fixes (siehe CHANGELOG.md)
- ✅ Mindestens 1x pro Monat

### **Wie oft prüfen?**
```bash
cd /mnt/user/appdata/casedesk
git fetch origin
git status
```

**Falls Sie sehen:** `Your branch is behind 'origin/main'` → Update verfügbar!

---

## 🔔 **Automatische Update-Benachrichtigung**

### **CaseDesk zeigt automatisch:**
- Aktuelle Version: `v1.3.0`
- Falls neue Version verfügbar: "Update verfügbar: v1.4.0"

**Dann einfach `./update.sh` ausführen!**

---

## 📖 **Changelog ansehen**

**Vor dem Update:**
```bash
cat CHANGELOG.md | head -50
```

**Oder online:**
https://github.com/AndiTrenter/CaseDesk-AI/blob/main/CHANGELOG.md

---

## 💾 **Backup vor Update (optional)**

**Datenbank sichern:**
```bash
docker exec casedesk-mongodb mongodump --out /tmp/backup --db casedesk
docker cp casedesk-mongodb:/tmp/backup ./mongodb_backup_$(date +%Y%m%d)
```

**Uploads sichern:**
```bash
cp -r /mnt/user/appdata/casedesk/uploads /mnt/user/appdata/casedesk_uploads_backup_$(date +%Y%m%d)
```

---

**Viel Erfolg beim Update! 🚀**
