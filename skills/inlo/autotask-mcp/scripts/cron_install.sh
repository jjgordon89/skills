#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

SKILL_DIR="$(pwd)"
SCRIPT_PATH="${SKILL_DIR}/scripts/mcp_update.sh"
CRON_COMMENT="# autotask-mcp weekly update check"
CRON_SCHEDULE="0 3 * * 0"  # Every Sunday at 3:00 AM
CRON_LINE="${CRON_SCHEDULE} ${SCRIPT_PATH} >> ${SKILL_DIR}/logs/cron.log 2>&1"

echo "Autotask MCP — Weekly Update Cron Installer"
echo "============================================"
echo ""
echo "This will add a weekly cron job to pull the latest Docker image."
echo ""
echo "  Schedule : Every Sunday at 03:00 AM"
echo "  Command  : ${SCRIPT_PATH}"
echo "  Log      : ${SKILL_DIR}/logs/cron.log"
echo ""

read -rp "Install cron job? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Remove any existing autotask-mcp cron entry, then add the new one
(crontab -l 2>/dev/null | grep -v "autotask-mcp" || true; echo "${CRON_COMMENT}"; echo "${CRON_LINE}") | crontab -

echo ""
echo "Cron job installed. Current crontab:"
crontab -l | grep -A1 "autotask-mcp"
echo ""
echo "To remove later, run: ./scripts/cron_uninstall.sh"
