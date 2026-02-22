# Security Notes — Guardian Skill

## Purpose

Guardian is a **defensive security scanner** for OpenClaw workspaces. It detects
prompt-injection attempts, data-exfiltration patterns, tool-abuse signatures, and
social-engineering payloads in agent messages and workspace files.

---

## Signature Definitions

- Plaintext signature files (`definitions/*.json`) are **excluded from the published
  package** via `.clawhubignore`. Only the `definitions/encoded/` sub-folder ships.
- At runtime, definitions are decoded from base64-encoded `.enc` files before loading
  into the scanner. This prevents the raw patterns from being trivially copy-pasted
  or misused.

---

## Network Access

- **No external network calls occur at runtime.** The scanner, realtime guard, and
  admin scripts are fully offline.
- `definitions/update.py` is a **maintenance utility** (excluded from the published
  package). It uses `urllib.request.urlopen` to fetch definition updates from a
  configurable URL. It is only ever executed when an operator explicitly runs
  `python3 definitions/update.py --apply`. It is never imported or called by any
  runtime code path.

---

## subprocess Usage

- `subprocess` is used **only** in `scripts/onboard.py` for the optional `--setup-crons`
  flag, which installs crontab entries when the operator explicitly requests it.
- No runtime scanning code uses subprocess.

---

## File I/O

- Guardian reads OpenClaw workspace files (configurable via `scan_paths`).
- It writes to a single SQLite database (`guardian.db`, default in workspace root).
- No files are created outside the workspace directory.

---

## Permissions Summary

| Permission       | Why                                                   |
|------------------|-------------------------------------------------------|
| `read_workspace` | Scans workspace files for threats                     |
| `write_workspace`| Writes `guardian.db` threat log                      |
| `shell_optional` | `onboard.py --setup-crons` writes crontab entries on operator request |

---

## False-Positive Mitigation

The published package excludes:
- `tests/` — test payloads containing intentionally malicious-looking strings
- `assets/` — demo HTML files
- `templates/` — markdown template with placeholder threat examples
- `quickstart.py` — developer demo script
- `definitions/update.py` — maintenance utility with `urlopen` import
- Plaintext `definitions/*.json` — raw signature patterns

This ensures automated security scanners evaluate only the actual runtime code,
not test fixtures or maintenance tooling.
