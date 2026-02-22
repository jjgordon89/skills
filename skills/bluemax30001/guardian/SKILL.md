---
name: guardian
description: '"I heard OpenClaw has security risks. How do I lock it down?" Install Guardian. That''s it.'
version: 2.0.5
metadata:
  openclaw:
    requires:
      bins:
        - python3
      env:
        - name: GUARDIAN_WORKSPACE
          description: "Override workspace path (optional; falls back to OPENCLAW_WORKSPACE then ~/.openclaw/workspace)"
          required: false
        - name: OPENCLAW_WORKSPACE
          description: "OpenClaw workspace root path (optional; used as fallback for DB and config resolution)"
          required: false
        - name: GUARDIAN_CONFIG
          description: "Override path to Guardian config.json (optional)"
          required: false
    permissions:
      - read_workspace
      - write_workspace
      - shell_optional
    notes: >
      Guardian is a defensive security scanner. It reads workspace files and writes
      to a local SQLite database (guardian.db). No network access occurs at runtime;
      definition updates are an explicit operator-triggered action (definitions/update.py).
---

# Guardian

Guardian scans incoming messages and workspace files for prompt injection, credential
exfiltration attempts, and other threats. It runs a lightweight real-time pre-scan
on every user request plus periodic batch scans of workspace files.

## Installation

```bash
cd ~/.openclaw/skills/guardian
./install.sh
```

Then run onboarding to complete setup:

```bash
python3 skills/guardian/scripts/onboard.py
```

## Status Check

```bash
python3 skills/guardian/scripts/admin.py status
```

## Running a Scan

```bash
# Quick report — threats in the last 24 hours
python3 skills/guardian/scripts/guardian.py --report --hours 24

# Full report
python3 skills/guardian/scripts/admin.py report
```

## Admin Commands

```bash
python3 scripts/admin.py status
python3 scripts/admin.py disable
python3 scripts/admin.py disable --until "2h"
python3 scripts/admin.py enable
python3 scripts/admin.py bypass --on
python3 scripts/admin.py bypass --off
python3 scripts/admin.py dismiss INJ-004
python3 scripts/admin.py allowlist add "safe phrase"
python3 scripts/admin.py allowlist remove "safe phrase"
python3 scripts/admin.py threats
python3 scripts/admin.py threats --clear
python3 scripts/admin.py update-defs
```

Add `--json` to any command for machine-readable output.

## Real-Time Pre-Scan

Use `RealtimeGuard` to intercept threats before they reach the model:

```python
from core.realtime import RealtimeGuard

guard = RealtimeGuard()
result = guard.scan_message(user_text, channel="discord")
if guard.should_block(result):
    return guard.format_block_response(result)
```

Scans only `high` and `critical` signatures for low latency.

## Configuration (`config.json`)

Key settings:

| Setting | Description |
|---|---|
| `enabled` | Master on/off switch |
| `admin_override` | Bypass mode (log but don't block) |
| `severity_threshold` | Blocking threshold: `low`, `medium`, `high`, `critical` |
| `scan_paths` | Paths to scan (`["auto"]` discovers common folders) |
| `db_path` | SQLite location (`"auto"` resolves to `<workspace>/guardian.db`) |
| `scan_interval_minutes` | Batch scan cadence |
| `alerts.notify_on_critical` | Emit critical alerts |
| `alerts.notify_on_high` | Emit high alerts |
| `alerts.daily_digest` | Send daily digest |

## Standalone Dashboard

```bash
cd skills/guardian/dashboard
python3 -m http.server 8091
# Open: http://localhost:8091/guardian.html
```

## Troubleshooting

- **`admin.py status` fails:** ensure `config.json` is valid JSON and DB path is writable.
- **No threats detected:** confirm definitions exist in `definitions/*.json` and `enabled` is `true`.
- **Unexpected blocking:** inspect with `python3 scripts/admin.py threats --json` and tune `severity_threshold` or add allowlist patterns.
- **Update checks fail:** validate network access to `definitions.update_url` and run `python3 definitions/update.py --version`.
