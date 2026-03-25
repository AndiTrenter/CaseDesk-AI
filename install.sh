#!/bin/bash
# ============================================
# CaseDesk AI - Installer für Unraid
# ============================================
# Verwendung:
#   curl -sSL https://raw.githubusercontent.com/AndiTrenter/CaseDesk-AI/main/install.sh | bash
# ============================================

set -e

echo "============================================"
echo "  CaseDesk AI - Installer"
echo "============================================"
echo ""

# Zielverzeichnis
INSTALL_DIR="/mnt/user/appdata/casedesk"

# Prüfen ob Git installiert ist
if ! command -v git &> /dev/null; then
    echo "❌ Git nicht gefunden. Bitte installiere Git zuerst."
    exit 1
fi

# Prüfen ob Docker Compose installiert ist
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nicht gefunden."
    exit 1
fi

# Klonen oder updaten
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Verzeichnis existiert bereits. Update wird durchgeführt..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "📦 Klone Repository..."
    git clone https://github.com/AndiTrenter/CaseDesk-AI.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# .env erstellen falls nicht vorhanden
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Erstelle Konfigurationsdatei..."
    cp .env.example .env
    
    # SECRET_KEY generieren
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/change-this-to-a-random-secret/$SECRET_KEY/" .env
    
    echo ""
    echo "⚠️  WICHTIG: Öffne die .env Datei und trage deinen OpenAI API-Key ein:"
    echo ""
    echo "    nano $INSTALL_DIR/.env"
    echo ""
    echo "   Setze OPENAI_API_KEY=sk-..."
    echo ""
fi

# Docker Images laden
echo ""
echo "🐳 Lade Docker Images..."
docker compose -f docker-compose.unraid.yml pull

echo ""
echo "============================================"
echo "  Installation abgeschlossen!"
echo "============================================"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Konfiguration anpassen (falls noch nicht geschehen):"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2. Starten:"
echo "   cd $INSTALL_DIR"
echo "   docker compose -f docker-compose.unraid.yml up -d"
echo ""
echo "3. Im Browser öffnen:"
echo "   http://$(hostname -I | awk '{print $1}'):9090"
echo ""
echo "Optional: Mit lokaler KI (Ollama):"
echo "   docker compose -f docker-compose.unraid.yml --profile ollama up -d"
echo ""
