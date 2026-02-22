#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Prerequisites ────────────────────────────────────────────────────────

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required." >&2
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 8):
    raise SystemExit("Error: Python 3.8+ is required.")
print(f"Python check OK: {sys.version.split()[0]}")
PY

export PYTHONPATH="$ROOT_DIR/core:${PYTHONPATH:-}"

# ── 2. Database ─────────────────────────────────────────────────────────────

python3 - <<'PY'
import sys
sys.path.insert(0, 'core')
from guardian_db import GuardianDB
db = GuardianDB()
print(f"Database ready: {db.db_path}")
db.close()
PY

# ── 3. Validate definitions ─────────────────────────────────────────────────

python3 - <<'PY'
import json, re
from pathlib import Path
defs_dir = Path('definitions')
errors = []
for p in defs_dir.glob('*.json'):
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f"{p.name}: JSON parse failed: {exc}")
        continue
    items = data.get('signatures', data.get('checks', [])) if isinstance(data, dict) else []
    for item in items:
        pat = item.get('pattern')
        if pat:
            try:
                re.compile(pat)
            except re.error as exc:
                errors.append(f"{p.name}:{item.get('id','?')}: invalid regex: {exc}")
if errors:
    raise SystemExit("Definition validation failed:\n" + "\n".join(errors))
print("Definition validation OK")
PY

echo ""
echo "✅ Guardian installation complete."
echo ""
echo "  Database initialised and definitions validated."
echo "  Run 'python3 skills/guardian/scripts/onboard.py' to complete setup."
echo ""
