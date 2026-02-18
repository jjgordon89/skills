---
name: cron-worker-guardrails
slug: cron-worker-guardrails
version: 1.0.0
license: MIT
description: |
  Use when hardening OpenClaw isolated cron jobs (agentTurn) against exec/bash quoting failures (unexpected EOF), command-substitution pitfalls ($()), pipefail+head SIGPIPE issues, and when designing a Cron Agent contract (AGENTS.md-like rules) or moving fragile shell into small scripts.
metadata:
  openclaw:
    emoji: "🧯"
---

# Cron Worker Guardrails

A reliability-first checklist for **isolated cron workers** (agentTurn) and any automation that runs unattended.

## Quick Start

Use this skill when you see errors like:
- `unexpected EOF while looking for matching ')'`
- brittle `bash -lc '...'` quoting failures
- false failures from `pipefail` + `head` (SIGPIPE)
- “works locally, fails in cron” due to cwd/env drift

Default rule: **scripts-first**. If the cron payload is getting long or fragile, move logic into a small script and have cron run exactly one short command.

## Canonical contract pointers
- Primary contract (keep cron payloads short; refer here):
  - `/root/.openclaw/workspace/openclaw-async-coding-playbook/protocol/cron-agent.md`
- Longer pitfall list: `references/pitfalls.md`

## Default stance (reliability-first)
- Prefer **scripts-first** over multi-line `bash -lc '...'`.
- Prefer **one exec = one short command**.
- Prefer **python3 explicitly** (don’t assume `python`). For project deps / reproducibility use:
  - `uv run --python 3.13 --frozen -- <cmd>`
  - Module form: `uv run --python 3.13 --frozen -- python -m <module> ...`
  - **Do not** write `uv run ... -m <module>` (unsupported; will fail).
- Avoid in generated shell:
  - **command substitution** `$(...)` / backticks
  - **heredocs** (`<<EOF`)
  - nested quotes inside a single `bash -lc ' ... '` block
  - `set -o pipefail` when piping into `head` (SIGPIPE → false failure)
  - `rg` (ripgrep) unless you *know* it’s installed

## Common failure patterns → fixes

### 0) Scripts-first wrapper pattern (recommended)
When a cron payload is getting long or you see quoting failures, wrap the whole job into one script and have cron run **exactly one command**.

Rules of thumb:
- use subprocess argv lists (no `shell=True`)
- `chdir` to repo root before `uv run --frozen ...` so lockfile resolution is deterministic
- print either `NO_REPLY` or a short alert

Example (this deployment):
- `/root/.openclaw/workspace/openclaw-async-coding-playbook/tools/openclaw_mem_harvest_triage_job.py` (hardens openclaw-mem harvest+triage)

### 1) `unexpected EOF while looking for matching ')'`
Likely causes:
- unclosed `$(...)` from command substitution
- broken nested quotes in `bash -lc ' ... '`

Fix pattern:
1) Replace the whole multi-line bash with a tiny Python script under the target repo’s `tools/` (or `/root/.openclaw/workspace/tools/`).
2) Cron prompt calls exactly one short command, e.g.:
   - `python3 /abs/path/to/tools/<script>.py --date today`

### 2) `ModuleNotFoundError` during pytest collection (cron/dev)
Common causes:
- running tests **not from repo root** (so the module isn’t on `sys.path`)
- calling the `pytest` entrypoint when it isn’t installed in the env

Safe pattern:
- `cd /path/to/repo`
- ensure pytest exists
- run:
  - `uv run -- python -m pytest -q`

## Safe shell patterns (if you must)
- Print counts without `$(...)`:
  - `echo -n 'lines='; wc -l < "$FILE"`
- “No matches” should not be fatal in exploration:
  - `git grep -n -- 'pattern' path || true`

## Copy/paste hardening header for cron payloads

Use this near the top of a cron `payload.message` (2 lines, low-noise):

- **Hardening (MUST):** read+follow `/root/.openclaw/workspace/openclaw-async-coding-playbook/protocol/cron-agent.md`.
- Also apply `cron-worker-guardrails` (this skill). If anything needs parsing/multi-step logic, write/run a small `tools/*.py` script.
