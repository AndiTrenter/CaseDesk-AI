#!/bin/bash
# ============================================================
# CaseDesk AI - Automatisches Update Script für Unraid
# ============================================================
# Dieses Script wird vom Host aus ausgeführt (nicht im Container)
#
# Installation:
#   1. Script nach /mnt/user/appdata/casedesk/ kopieren
#   2. chmod +x update-casedesk.sh
#   3. ./update-casedesk.sh
#
# Automatisches Update via Web-UI:
#   Das Script kann auch von der CaseDesk Web-Oberfläche
#   getriggert werden, wenn Docker-Socket gemountet ist.
# ============================================================

set -e

# Konfiguration
CASEDESK_DIR="${CASEDESK_DIR:-/mnt/user/appdata/casedesk}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.unraid.yml}"
LOG_FILE="${CASEDESK_DIR}/update.log"
BACKUP_DIR="${CASEDESK_DIR}/backups"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

error() {
    local msg="[ERROR] $1"
    echo -e "${RED}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

warn() {
    local msg="[WARN] $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}$1${NC}"
}

# Banner
echo ""
echo "============================================================"
echo "       CaseDesk AI - Update Script v1.5.0"
echo "============================================================"
echo ""

# Prüfe ob Verzeichnis existiert
if [ ! -d "$CASEDESK_DIR" ]; then
    error "CaseDesk Verzeichnis nicht gefunden: $CASEDESK_DIR"
    echo ""
    echo "Bitte CASEDESK_DIR setzen oder Script aus dem richtigen Verzeichnis ausführen."
    exit 1
fi

cd "$CASEDESK_DIR"
log "Arbeitsverzeichnis: $(pwd)"

# Prüfe Compose-Datei
if [ ! -f "$COMPOSE_FILE" ]; then
    if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    elif [ -f "docker-compose.yaml" ]; then
        COMPOSE_FILE="docker-compose.yaml"
    else
        error "Keine docker-compose Datei gefunden!"
        exit 1
    fi
fi

log "Verwende Compose-Datei: $COMPOSE_FILE"

# Backup erstellen
mkdir -p "$BACKUP_DIR"
BACKUP_NAME="backup_$(date '+%Y%m%d_%H%M%S')"
log "Erstelle Backup: $BACKUP_NAME"

# Aktuelle Version speichern
if command -v curl &> /dev/null; then
    CURRENT_VERSION=$(curl -s http://localhost:9090/api/health 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    echo "$CURRENT_VERSION" > "$BACKUP_DIR/${BACKUP_NAME}_version.txt"
    log "Aktuelle Version: $CURRENT_VERSION"
fi

# Git Pull (falls git repo)
if [ -d ".git" ]; then
    log "Hole neueste Änderungen von GitHub..."
    git fetch origin 2>&1 | tee -a "$LOG_FILE"
    git pull origin main 2>&1 | tee -a "$LOG_FILE"
    log "Git Pull abgeschlossen"
else
    warn "Kein Git-Repository - überspringe Git Pull"
fi

# Container stoppen
log "Stoppe Container..."
docker-compose -f "$COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE" || \
docker compose -f "$COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE"

# Neue Images holen
log "Hole neue Docker Images..."
docker-compose -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$LOG_FILE" || \
docker compose -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$LOG_FILE"

# Container neu starten
log "Starte Container..."
docker-compose -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE" || \
docker compose -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"

# Status anzeigen
log "Container Status:"
docker-compose -f "$COMPOSE_FILE" ps 2>&1 | tee -a "$LOG_FILE" || \
docker compose -f "$COMPOSE_FILE" ps 2>&1 | tee -a "$LOG_FILE"

# Warte auf Health Check
log "Warte auf Services (max 60s)..."
HEALTH_URL="http://localhost:9090/api/health"
COUNTER=0
MAX_WAIT=60

while [ $COUNTER -lt $MAX_WAIT ]; do
    if command -v curl &> /dev/null; then
        HEALTH=$(curl -s "$HEALTH_URL" 2>/dev/null || echo "")
        if echo "$HEALTH" | grep -q "healthy"; then
            NEW_VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
            log "Health Check erfolgreich!"
            log "Neue Version: $NEW_VERSION"
            break
        fi
    fi
    sleep 2
    COUNTER=$((COUNTER + 2))
    echo -n "."
done

if [ $COUNTER -ge $MAX_WAIT ]; then
    warn "Health Check Timeout - bitte manuell prüfen"
fi

echo ""
echo "============================================================"
echo -e "  ${GREEN}CaseDesk AI Update abgeschlossen!${NC}"
echo "============================================================"
echo ""
echo "  Web-Oberfläche: http://$(hostname -I | awk '{print $1}'):9090"
echo "  Log-Datei: $LOG_FILE"
echo ""

# Optional: Alte Backups aufräumen (behalte letzte 5)
if [ -d "$BACKUP_DIR" ]; then
    cd "$BACKUP_DIR"
    ls -t backup_*_version.txt 2>/dev/null | tail -n +6 | xargs -r rm -f
fi

exit 0
