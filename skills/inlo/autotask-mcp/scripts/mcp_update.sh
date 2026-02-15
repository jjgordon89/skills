#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

LOGFILE="$(pwd)/logs/update.log"
mkdir -p "$(dirname "$LOGFILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

log "Checking for Autotask MCP image updates..."

# Capture current image digest
OLD_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/asachs01/autotask-mcp:latest 2>/dev/null || echo "none")

# Pull latest image
docker compose pull

# Capture new image digest
NEW_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/asachs01/autotask-mcp:latest 2>/dev/null || echo "unknown")

if [ "$OLD_DIGEST" != "$NEW_DIGEST" ]; then
  log "New image detected: $NEW_DIGEST"
  log "Recreating container with updated image..."
  docker compose up -d
  log "Update complete."
else
  log "Already on latest image: $OLD_DIGEST. No restart needed."
fi
