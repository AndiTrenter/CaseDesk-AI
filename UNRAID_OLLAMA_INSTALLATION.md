# Ollama Installation auf Unraid für CaseDesk AI

## 🎯 Ziel
Ollama und Open WebUI separat auf Unraid installieren und mit CaseDesk AI verbinden.

---

## 📋 Schritt 1: Ollama auf Unraid installieren

### **Via Unraid Community Apps:**

1. **Öffnen Sie Unraid WebUI** → **Apps**
2. **Suchen Sie nach:** `ollama`
3. **Installieren Sie:** **"ollama"** von ollama (offizielle Version)

### **Konfiguration:**

- **Container Name:** `ollama`
- **Network Type:** `bridge`
- **Port:** `11434` → `11434` (Host Port 11434)
- **Volume Mapping:**
  - Container Path: `/root/.ollama`
  - Host Path: `/mnt/user/appdata/ollama`
- **CPU Pinning:** Optional (für bessere Performance)
- **GPU Support:** Falls Sie NVIDIA GPU haben, aktivieren Sie GPU-Passthrough

**Klicken Sie auf "Apply"** um den Container zu starten.

---

## 🎨 Schritt 2: Open WebUI installieren (Optional aber empfohlen)

### **Via Unraid Community Apps:**

1. **Apps** → Suchen Sie nach: `open-webui`
2. **Installieren Sie:** **"Open WebUI"**

### **Konfiguration:**

- **Container Name:** `open-webui`
- **Network Type:** `bridge`
- **Port:** `3000` → `3000` (oder einen freien Port wie `3001`)
- **Environment Variables:**
  - `OLLAMA_BASE_URL=http://192.168.1.140:11434` (Ihre Unraid IP!)
- **Volume Mapping:**
  - Container Path: `/app/backend/data`
  - Host Path: `/mnt/user/appdata/open-webui`

**Klicken Sie auf "Apply"**.

**Open WebUI Zugriff:** `http://192.168.1.140:3000`

---

## 🚀 Schritt 3: Ollama-Modell herunterladen

### **Terminal öffnen (Unraid → Terminal):**

```bash
docker exec -it ollama ollama pull llama3.2
```

**Oder größere Modelle:**
```bash
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull llama3.1:70b
docker exec -it ollama ollama pull mixtral
```

**Modelle anzeigen:**
```bash
docker exec -it ollama ollama list
```

---

## 🔗 Schritt 4: CaseDesk AI mit externem Ollama verbinden

### **1. Alte CaseDesk Container stoppen:**
```bash
cd /mnt/user/appdata/casedesk
docker-compose -f docker-compose.unraid.yml down
```

### **2. Alte Ollama-Container entfernen:**
```bash
docker stop casedesk-ollama casedesk-ollama-init 2>/dev/null
docker rm casedesk-ollama casedesk-ollama-init 2>/dev/null
```

### **3. Git-Änderungen pullen:**
```bash
git pull origin main
```

### **4. .env Datei anpassen (falls nötig):**
```bash
nano .env
```

**Fügen Sie hinzu oder ändern Sie:**
```env
OLLAMA_URL=http://192.168.1.140:11434
OLLAMA_MODEL=llama3.2
```

**Speichern:** `Ctrl+O` → Enter → `Ctrl+X`

### **5. CaseDesk neu starten:**
```bash
docker-compose -f docker-compose.unraid.yml up -d
```

---

## ✅ Schritt 5: Testen

### **1. Ollama testen:**
```bash
curl http://192.168.1.140:11434/api/tags
```

**Erwartete Ausgabe:** Liste der installierten Modelle

### **2. CaseDesk Backend-Logs prüfen:**
```bash
docker logs casedesk-backend --tail 50
```

**Suchen Sie nach:** `AI Service initialized: provider=ollama`

### **3. In CaseDesk AI:**
1. Öffnen Sie: `http://192.168.1.140:9090`
2. Gehen Sie zu: **Einstellungen** → **AI**
3. Wählen Sie: **Ollama (Lokal)**
4. Klicken Sie: **Speichern**
5. Testen Sie den **KI-Assistenten**

---

## 🎯 Vorteile dieser Lösung

✅ **Ollama läuft unabhängig** von CaseDesk  
✅ **Open WebUI** für direkten Zugriff auf Ollama  
✅ **Modelle bleiben erhalten** bei CaseDesk-Updates  
✅ **Einfachere Verwaltung** über Unraid WebUI  
✅ **Kann von mehreren Apps genutzt werden**

---

## 🔧 Troubleshooting

### **Problem: CaseDesk kann Ollama nicht erreichen**

**Lösung 1:** IP-Adresse prüfen
```bash
ifconfig | grep "inet "
```

**Lösung 2:** Firewall-Regel (falls aktiviert)
```bash
iptables -I INPUT -p tcp --dport 11434 -j ACCEPT
```

### **Problem: Modell wird nicht gefunden**

**Lösung:** Modell neu herunterladen
```bash
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama list
```

---

## 📞 Support

Falls Probleme auftreten:
1. Backend-Logs prüfen: `docker logs casedesk-backend`
2. Ollama-Logs prüfen: `docker logs ollama`
3. Netzwerk testen: `docker exec casedesk-backend ping -c 3 192.168.1.140`

---

**Viel Erfolg! 🚀**
