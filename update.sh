#!/bin/bash

# CaseDesk AI Update Script für Unraid
# Version: 1.3.0
# Verwendung: ./update.sh

set -e

echo "=== CaseDesk AI Update Script ==="
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion: Fehler anzeigen
error() {
    echo -e "${RED}❌ FEHLER: $1${NC}"
    exit 1
}

# Funktion: Erfolg anzeigen
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Funktion: Info anzeigen
info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Prüfen, ob im richtigen Verzeichnis
if [ ! -f "docker-compose.unraid.yml" ]; then
    error "docker-compose.unraid.yml nicht gefunden! Bitte führen Sie das Script im CaseDesk-Verzeichnis aus."
fi

info "Starte Update-Prozess..."
echo ""

# 1. Git Pull
info "Schritt 1/5: Hole neueste Änderungen von GitHub..."
git fetch origin
git pull origin main || error "Git pull fehlgeschlagen!"
success "Neueste Änderungen geholt"
echo ""

# 2. Container stoppen
info "Schritt 2/5: Stoppe Container..."
docker-compose -f docker-compose.unraid.yml down || error "Container konnten nicht gestoppt werden!"
success "Container gestoppt"
echo ""

# 3. Alte Images löschen (nur CaseDesk)
info "Schritt 3/5: Lösche alte Images..."
docker images | grep "casedesk-ai\|casedesk" | awk '{print $1":"$2}' | xargs -r docker rmi -f 2>/dev/null || true
success "Alte Images gelöscht"
echo ""

# 4. Lokal neu bauen
info "Schritt 4/5: Baue neue Images (kann 5-10 Minuten dauern)..."
if [ -f "docker-compose.yml" ]; then
    # Verwende normale docker-compose.yml (mit build-Kontext)
    docker-compose build --no-cache || error "Build fehlgeschlagen!"
else
    # Verwende unraid-spezifische
    docker-compose -f docker-compose.unraid.yml build --no-cache || error "Build fehlgeschlagen!"
fi
success "Images gebaut"
echo ""

# 5. Container starten
info "Schritt 5/5: Starte Container..."
docker-compose -f docker-compose.unraid.yml up -d || error "Container-Start fehlgeschlagen!"
success "Container gestartet"
echo ""

# Status prüfen
info "Prüfe Status..."
sleep 3
docker ps | grep casedesk

echo ""
success "Update erfolgreich abgeschlossen!"
echo ""
echo "=== Nächste Schritte ==="
echo "1. Öffnen Sie CaseDesk AI im Browser"
echo "2. Drücken Sie Ctrl+Shift+R (Hard Reload)"
echo "3. Prüfen Sie, ob die neue Version angezeigt wird"
echo ""
echo "Bei Problemen:"
echo "  - Backend-Logs: docker logs casedesk-backend --tail 50"
echo "  - Frontend-Logs: docker logs casedesk-frontend --tail 50"
echo ""
