#!/bin/bash
# CaseDesk AI Update Script
# This script should be mounted into the container or run from the host

set -e

# Configuration
CASEDESK_DIR="${CASEDESK_DIR:-/mnt/user/appdata/casedesk}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
LOG_FILE="${CASEDESK_DIR}/update.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    warn "Not running as root. Some operations may fail."
fi

# Check if directory exists
if [ ! -d "$CASEDESK_DIR" ]; then
    error "CaseDesk directory not found: $CASEDESK_DIR"
    exit 1
fi

cd "$CASEDESK_DIR"
log "Working directory: $(pwd)"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    # Try alternative names
    if [ -f "docker-compose.unraid.yml" ]; then
        COMPOSE_FILE="docker-compose.unraid.yml"
    elif [ -f "docker-compose.yaml" ]; then
        COMPOSE_FILE="docker-compose.yaml"
    else
        error "No docker-compose file found!"
        exit 1
    fi
fi

log "Using compose file: $COMPOSE_FILE"

# Pull latest changes from git
log "Pulling latest changes from GitHub..."
if [ -d ".git" ]; then
    git fetch origin
    git pull origin main
    log "Git pull completed"
else
    warn "Not a git repository - skipping git pull"
fi

# Stop containers
log "Stopping containers..."
docker-compose -f "$COMPOSE_FILE" down || docker compose -f "$COMPOSE_FILE" down

# Pull new images
log "Pulling new Docker images..."
docker-compose -f "$COMPOSE_FILE" pull || docker compose -f "$COMPOSE_FILE" pull

# Build if needed (for custom images)
log "Building containers..."
docker-compose -f "$COMPOSE_FILE" build --no-cache || docker compose -f "$COMPOSE_FILE" build --no-cache

# Start containers
log "Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d || docker compose -f "$COMPOSE_FILE" up -d

# Show status
log "Container status:"
docker-compose -f "$COMPOSE_FILE" ps || docker compose -f "$COMPOSE_FILE" ps

# Check health
log "Waiting for services to be healthy..."
sleep 10

# Test health endpoint
HEALTH_URL="http://localhost:9090/api/health"
if command -v curl &> /dev/null; then
    HEALTH=$(curl -s "$HEALTH_URL" 2>/dev/null || echo "failed")
    if echo "$HEALTH" | grep -q "healthy"; then
        log "Health check passed: $HEALTH"
    else
        warn "Health check returned: $HEALTH"
    fi
fi

log "Update completed successfully!"
echo ""
echo "============================================"
echo "  CaseDesk AI Update Complete!"
echo "============================================"
