# clawd-zero-trust

> Zero Trust security hardening skill for [OpenClaw](https://openclaw.ai) deployments.  
> Audited through dual-model review (GPT-5.3 + Sonnet 4.6). Production-stable at v1.1.1.

---

## Why this exists

When you run an AI agent on a server, it talks to the internet constantly — to call AI APIs, fetch data, send messages. By default, **it can reach anything**. No restrictions. No boundaries.

That's a problem.

A misconfigured agent, a compromised plugin, or a prompt injection attack could turn your server into an exfiltration point — quietly sending your data, keys, or internal state to any endpoint on the internet. And you'd never know until it was too late.

**Zero Trust flips the default.** Instead of "allow everything, block the bad stuff", it starts with "block everything, allow only what's explicitly needed."

For an AI agent like OpenClaw, "what's explicitly needed" is a short list: the AI providers it calls (Anthropic, OpenAI, Google), the messaging layer (Telegram), GitHub, search, and Tailscale for remote access. That's it. Nothing else should ever need outbound access from this machine.

This skill enforces exactly that — at the kernel firewall level, using UFW. Not at the application layer where it can be bypassed, but at the OS level where it can't.

### The threat model

| Threat | Without this skill | With this skill |
|--------|-------------------|-----------------|
| Prompt injection → data exfiltration | Agent calls attacker's endpoint | Connection blocked by UFW |
| Compromised plugin phoning home | Unrestricted outbound access | Only allowlisted IPs pass |
| Supply chain attack via npm/pip | Package calls C2 server | Blocked unless explicitly allowed |
| Misconfigured agent leaking secrets | No network boundary | Firewall catches it |
| SSH brute force pivot | Agent can reach any IP | Outbound restricted to known providers |

### What "Zero Trust" means here

1. **Deny all outbound by default** — `ufw default deny outgoing`
2. **Allowlist only what's provably needed** — DNS-resolved IPs for 13 known providers
3. **Verify after every change** — canary mode runs live connectivity checks for 120s before committing
4. **Rollback on any failure** — if post-apply checks fail, firewall reverts automatically
5. **Never trust the script itself** — script hash gate prevents tampered re-applies

---

## Architecture

```
clawd-zero-trust/
├── SKILL.md                        # OpenClaw skill manifest + usage instructions
├── scripts/
│   ├── egress-filter.sh            # Core: UFW Zero Trust egress policy engine
│   ├── harden.sh                   # OpenClaw config hardening (PLP, plugins, gateway)
│   ├── audit.sh                    # Deep security audit + false-positive filter
│   ├── release-gate.sh             # CI pipeline: validate → shellcheck → package → verify
│   ├── quick_validate.py           # Structural skill validator (pre-package)
│   └── package_skill.py            # Skill packager → .skill artifact
└── references/
    ├── false-positives.md          # Registry of known audit false positives
    └── zero-trust-principles.md    # Design rationale and threat model
```

---

## Core: egress-filter.sh

The centerpiece. Implements a **DNS-resolved IP allowlist** enforced via UFW, with a full operational safety stack.

### How it works

```
┌─────────────────────────────────────────────────────────┐
│                      apply_policy()                     │
│                                                         │
│  1. snapshot_ips()                                      │
│     └─ dig A + AAAA for each provider domain           │
│     └─ abort if 0 providers resolve (lockout guard)    │
│                                                         │
│  2. flush_zt_rules()                                    │
│     └─ ufw status numbered → find ZT: tagged rules     │
│     └─ delete in reverse order (index-stable)          │
│                                                         │
│  3. Apply static allows                                 │
│     └─ loopback, DNS(53), SSH(22), Tailscale ports     │
│                                                         │
│  4. Apply provider IP rules (from snapshot)            │
│     └─ ufw allow out to <ip> port 443 comment ZT:...  │
│                                                         │
│  5. ufw default deny outgoing                          │
│  6. ufw reload                                         │
└─────────────────────────────────────────────────────────┘
```

### Provider allowlist (DNS-resolved at runtime)

| Provider | Port |
|----------|------|
| api.anthropic.com | 443 |
| api.openai.com | 443 |
| generativelanguage.googleapis.com | 443 |
| api.telegram.org | 443 |
| api.github.com | 443 |
| api.search.brave.com | 443 |
| controlplane.tailscale.com | 443 |
| login.tailscale.com | 443 |
| log.tailscale.io | 443 |
| accounts.google.com | 443 |
| oauth2.googleapis.com | 443 |
| registry.npmjs.org | 443 |
| api.agentsandbox.co | 443 |

IPs are resolved fresh on every apply — CDN IP rotation is handled automatically. IPv4 + IPv6 both captured.

### Safety stack (layered)

```
Layer 1 — Pre-flight
  check_dep()         → abort if dig/ufw/curl/python3 missing
  check_ufw_active()  → abort if UFW is inactive (rules would be no-ops)
  enforce_profile_gate() → hash mismatch on modified script = abort (TOFU model)

Layer 2 — Apply
  snapshot_ips()      → returns 1 if zero providers resolve
                        apply_policy() propagates → deny-outgoing never fires
  flush_zt_rules()    → clears stale IP rules before re-apply (no accumulation)
                        detects sudo/UFW failure explicitly (no silent skip)

Layer 3 — Post-apply
  verify_critical_endpoints()
                      → curl each endpoint, check HTTP code ≠ 000
                        (CDN 404/421 = reachable; 000 = no connection)

Layer 4 — Rollback
  perform_reset_or_die()
                      → if rollback itself fails: log 🚨 CRITICAL,
                        write LOCKOUT-MANUAL-INTERVENTION-REQUIRED to state,
                        exit 99 (never silently continues)
```

### Execution modes

```bash
bash egress-filter.sh              # Dry-run (default) — preview, zero changes
bash egress-filter.sh --apply      # Transactional apply + post-check + rollback
bash egress-filter.sh --canary     # 120s live verify loop before committing
bash egress-filter.sh --verify     # Endpoint reachability check only
bash egress-filter.sh --reset      # Restore ufw default allow outgoing
bash egress-filter.sh --force      # Bypass hash gate (accept new profile)
```

### Canary mode

```
apply_policy()
  ↓ success
verify_critical_endpoints()  ← every 15s for 120s
  ↓ all pass
ufw reload (commit)
write_state(canary-pass-committed)

  ↓ any fail
perform_reset_or_die("canary-verify-failed")
write_state(canary-failed-rolled-back)
exit 1
```

### State machine

```
.state/egress-profile.json:
  {
    "profileVersion": "1.1.1",
    "scriptHash": "<sha256>",
    "lastAppliedAt": "<ISO8601>",
    "lastResult": "<state>"
  }

States:
  apply-success
  apply-failed-rolled-back
  apply-failed-postcheck-rolled-back
  canary-pass-committed
  canary-failed-rolled-back
  canary-apply-failed-rolled-back
  reset
  reset-failed
  LOCKOUT-MANUAL-INTERVENTION-REQUIRED   ← alert: manual action needed
```

---

## harden.sh

Idempotent OpenClaw config hardening. Reads `~/.openclaw/openclaw.json` via `jq`, applies only missing settings.

| Check | What it does |
|-------|-------------|
| SecureClaw loaded | Verifies plugin is active; prints install steps if not |
| `plugins.allow` | Adds `secureclaw` to allowlist if missing |
| `tools.byProvider` | Applies PLP (Principle of Least Privilege) per-model toolset |
| SSH perimeter | Checks for `0.0.0.0:22` / `[::]:22` exposure; prints fix |
| Gateway bind | Sets `gateway.bind = loopback` if not already set |

Modes: `--dry-run` (default) · `--apply`

---

## audit.sh

Wraps `openclaw security audit --deep` with:
- **False-positive suppression** — filters known safe patterns (`openclaw-agentsandbox`, `secureclaw`) via `grep -v`
- **SSH exposure check** — detects `0.0.0.0:22` and `[::]:22` (IPv4 + IPv6)
- **Port 631 (CUPS)** — flags if still active
- **Dependency check** — `dig`, `ufw` availability
- **Structured log** — append-only at `logs/audit.log` (mode 600)

---

## release-gate.sh

Four-stage CI pipeline — all must pass to produce a `.skill` artifact:

```
Stage 1: quick_validate.py
  └─ Checks SKILL.md present, scripts/ exists, required files in place

Stage 2: shellcheck
  └─ Runs against all .sh files in scripts/
  └─ Fails hard on any warning

Stage 3: package_skill.py
  └─ Bundles skill → skills/dist/clawd-zero-trust.skill

Stage 4: egress-filter.sh --verify
  └─ Live endpoint check: Telegram, GitHub, Anthropic, OpenAI
  └─ Fails if any endpoint returns code 000 (no TCP connection)
```

---

## Design decisions

**Why DNS resolution at apply time, not hardcoded IPs?**  
CDNs (Cloudflare, AWS) rotate IPs. Hardcoded lists go stale within days. Resolving at apply-time keeps rules accurate; canary mode validates connectivity immediately after.

**Why reverse-order UFW rule deletion?**  
UFW renumbers rules after each deletion. Deleting highest-numbered first means lower indices are never invalidated mid-loop.

**Why HTTP code `≠ 000` instead of `curl -f`?**  
`curl -f` fails on HTTP ≥ 400. Anthropic returns 404 and OpenAI returns 421 on the root path — both are valid CDN responses proving full TCP/TLS reachability. Only `000` means no connection established.

**Why TOFU (Trust On First Use) for the hash gate?**  
First run is ungated by design. The gate only fires on subsequent runs where the script has been modified since last apply. The deploy key + private repo is the integrity boundary for the initial install.

**Why `perform_reset_or_die` instead of `perform_reset || true`?**  
Silent rollback failure is the worst outcome — the system appears to be in a safe state but isn't. Better to exit 99 loudly and require manual intervention than to continue with an unknown firewall state.

---

## Version history

| Version | Change |
|---------|--------|
| v1.0.1 | Transactional apply, versioned state, canary mode, dry-run default |
| v1.0.2 | `verify_endpoint`: HTTP code check instead of `curl -f` |
| v1.0.3 | `perform_reset_or_die`, `snapshot_ips` zero-resolve guard, UFW active check |
| v1.1.0 | `flush_zt_rules()` — prevents rule accumulation on repeated runs |
| v1.1.1 | `flush_zt_rules`: return 1 on partial failure; detect sudo/UFW errors explicitly |

---

## Quick start

```bash
# 1. Audit current state
bash scripts/audit.sh

# 2. Preview hardening (safe, no changes)
bash scripts/harden.sh

# 3. Preview egress policy (safe, no changes)
bash scripts/egress-filter.sh

# 4. Apply hardening
bash scripts/harden.sh --apply

# 5. Apply egress policy
bash scripts/egress-filter.sh --apply
```

---

## Requirements

- Ubuntu 20.04+ (UFW + bash 4.2+)
- `ufw`, `curl`, `dig` (dnsutils), `python3`, `shellcheck`
- Passwordless sudo for `ufw` commands
- OpenClaw with SecureClaw plugin loaded

---

## License

MIT
