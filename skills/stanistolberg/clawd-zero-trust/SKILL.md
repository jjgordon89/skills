---
name: clawd-zero-trust
version: "1.1.4"
author: stanistolberg
homepage: https://github.com/stanistolberg/clawd-zero-trust
description: "Zero Trust security hardening for OpenClaw deployments. Use when asked to audit, harden, or apply Zero Trust architecture to an OpenClaw instance — including NHI identity scoping, Principle of Least Privilege (PLP), Plan-First protocol, DNS-based egress filtering, plugin allowlisting, and SSH/network lockdown. Also triggers on security audit requests, vulnerability analysis, SecureClaw installation, firewall hardening, and post-deployment security reviews."
---

# clawd-zero-trust (v1.1.4)

Zero Trust hardening framework for OpenClaw. Built by Blocksoft.

## Core Principles

1. **NHI (Non-Human Identity):** Sub-agents run as isolated sessions with scoped credentials. Never share 'main' identity for high-risk ops.
2. **PLP (Principle of Least Privilege):** Restrict default model toolset. Use `tools.byProvider` to limit small/untrusted models to `coding` profile.
3. **Plan-First:** Declare intent (what + why + expected outcome) before any write, exec, or network call.
4. **Egress Control:** Whitelist outbound traffic to authorized AI providers only. Preserve Tailscale + Telegram API.
5. **Assumption of Breach:** Design as if the attacker is already in. Verify every plugin, model, and extension.

## Canonical Egress Script Path

Single source of truth:

`/home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh`

Compatibility symlink:

`/home/claw/.openclaw/workspace/scripts/egress_filter.sh -> .../skills/clawd-zero-trust/scripts/egress-filter.sh`

## Workflow: Audit → Harden → Egress → Verify

### 1) Audit
```bash
bash scripts/audit.sh
```

### 2) Harden
```bash
# Preview (default)
bash scripts/harden.sh

# Apply
bash scripts/harden.sh --apply
```

### 3) Egress Policy (dry-run default)
```bash
# Dry-run preview (default)
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --dry-run

# Transactional apply: auto-rollback if Telegram/GitHub/Anthropic/OpenAI checks fail
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --apply

# Canary mode: temporary apply + 120s periodic verification, then commit/rollback
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --canary

# Force apply when script hash changed from stored profile
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --apply --force

# Verify endpoints only
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --verify

# Emergency rollback
bash /home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh --reset
```

### 4) Release Gate (v1.1.4)
```bash
bash scripts/release-gate.sh
```
Gate checks (must all pass):
- `quick_validate.py` on skill structure
- `shellcheck` on all shell scripts (fails with install hint if missing)
- `package_skill.py` packaging to `skills/dist/clawd-zero-trust.skill`
- `--verify` endpoint checks

## Versioned Firewall Profile State

State file:

`/home/claw/.openclaw/workspace/skills/clawd-zero-trust/.state/egress-profile.json`

Tracked fields:
- `profileVersion`
- `scriptHash`
- `lastAppliedAt`
- `lastResult`

On apply/canary, hash mismatch is refused unless `--force` is provided.

## References
- `references/zero-trust-principles.md` — Detailed ZT framework for AI agents
- `references/false-positives.md` — Verified safe patterns that trigger audit warnings
