#!/bin/bash
# =============================================================================
# CaseDesk AI - Ollama Initialisierungsscript
# =============================================================================
# Dieses Script wird automatisch gestartet und lädt das KI-Modell herunter
# wenn es noch nicht vorhanden ist.
#
# Verwendung:
#   ./scripts/ollama-init.sh
#
# Oder als Docker-Container Entrypoint (empfohlen)
# =============================================================================

set -e

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MAX_RETRIES=30
RETRY_DELAY=5

echo "=== CaseDesk AI - Ollama Initialisierung ==="
echo "Modell: $OLLAMA_MODEL"
echo "Host: $OLLAMA_HOST"

# Warte bis Ollama erreichbar ist
echo "Warte auf Ollama-Service..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "✓ Ollama ist erreichbar"
        break
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "✗ Ollama nicht erreichbar nach ${MAX_RETRIES} Versuchen"
        exit 1
    fi
    echo "  Versuch $i/$MAX_RETRIES - warte ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

# Prüfe ob Modell bereits vorhanden
echo "Prüfe ob Modell '$OLLAMA_MODEL' vorhanden ist..."
MODELS=$(curl -s "${OLLAMA_HOST}/api/tags" | grep -o "\"name\":\"[^\"]*\"" | grep -o "\"[^\"]*\"$" | tr -d '"')

if echo "$MODELS" | grep -q "^${OLLAMA_MODEL}"; then
    echo "✓ Modell '$OLLAMA_MODEL' ist bereits installiert"
else
    echo "Lade Modell '$OLLAMA_MODEL' herunter (kann einige Minuten dauern)..."
    curl -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${OLLAMA_MODEL}\"}" --no-buffer | while read line; do
        STATUS=$(echo "$line" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$STATUS" ]; then
            echo "  $STATUS"
        fi
    done
    echo "✓ Modell '$OLLAMA_MODEL' wurde heruntergeladen"
fi

echo "=== Ollama Initialisierung abgeschlossen ==="
echo "Verfügbare Modelle:"
curl -s "${OLLAMA_HOST}/api/tags" | grep -o "\"name\":\"[^\"]*\"" | cut -d'"' -f4 | while read model; do
    echo "  - $model"
done
