#!/bin/bash
# ============================================================
# CaseDesk AI - Unraid User Script
# ============================================================
# Dieses Script kann als Unraid User Script verwendet werden.
# 
# Installation in Unraid:
#   1. Öffne Unraid Web-UI
#   2. Gehe zu Settings > User Scripts
#   3. Klicke "ADD NEW SCRIPT"
#   4. Name: "CaseDesk Update"
#   5. Füge diesen Inhalt ein
#   6. Speichern
#
# Verwendung:
#   - Manuell: Klicke "RUN IN BACKGROUND"
#   - Automatisch: Setze Schedule (z.B. täglich um 3:00)
# ============================================================

# Konfiguration
CASEDESK_DIR="/mnt/user/appdata/casedesk"

# Prüfe ob CaseDesk installiert ist
if [ ! -d "$CASEDESK_DIR" ]; then
    echo "CaseDesk nicht gefunden in $CASEDESK_DIR"
    exit 1
fi

# Führe Update aus
cd "$CASEDESK_DIR"

echo "=== CaseDesk Update $(date) ==="

# Git Pull
if [ -d ".git" ]; then
    echo "Hole neueste Version von GitHub..."
    git pull origin main
fi

# Docker Update
echo "Stoppe Container..."
docker-compose -f docker-compose.unraid.yml down 2>/dev/null || docker compose -f docker-compose.unraid.yml down

echo "Hole neue Images..."
docker-compose -f docker-compose.unraid.yml pull 2>/dev/null || docker compose -f docker-compose.unraid.yml pull

echo "Starte Container..."
docker-compose -f docker-compose.unraid.yml up -d 2>/dev/null || docker compose -f docker-compose.unraid.yml up -d

echo "=== Update abgeschlossen ==="

# Zeige Status
sleep 5
curl -s http://localhost:9090/api/health || echo "Health check nicht erreichbar"
