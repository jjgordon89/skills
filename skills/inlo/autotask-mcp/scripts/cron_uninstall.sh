#!/usr/bin/env bash
set -euo pipefail

echo "Removing autotask-mcp cron job..."
(crontab -l 2>/dev/null | grep -v "autotask-mcp" || true) | crontab -
echo "Done. Remaining crontab:"
crontab -l 2>/dev/null || echo "(empty)"
