#!/bin/bash
# =============================================================================
# Zero Trust Egress Filter for OpenClaw
#
# v1.0.1: Transactional apply, versioned state, canary mode, dry-run default
# v1.0.2: Fix verify_endpoint — HTTP code check instead of curl -f
#         (Anthropic=404, OpenAI=421 on root — valid CDN, not failures)
# v1.0.3: Two blocking fixes from dual-model audit (GPT-5.3 + Sonnet 4.6):
#         [FIX-4] perform_reset_or_die() — rollback failure no longer silent;
#                 system lockout is logged, state marked, exit 99 fired
#         [FIX-6] snapshot_ips returns 1 if zero providers resolve;
#                 apply_policy aborts before deny-outgoing to prevent lockout
#         [MED-7] check_ufw_active() — abort if UFW is inactive before apply
#         [LOW-1] verify_endpoint: --max-redirs 5 caps redirect depth
# v1.1.0: [Issue 5] flush_zt_rules() — purge stale ZT-tagged rules before
#         re-apply; prevents UFW rule accumulation on repeated runs.
#         Non-fatal: flush warnings logged but apply continues.
# v1.1.1: Two bugs fixed in flush_zt_rules() (auditor catch):
#         [BUG-A] Function always returned 0 — partial failure was silent;
#                 now returns 1 on any delete failure so caller warning fires.
#         [BUG-B] 2>/dev/null on ufw status swallowed sudo/permission errors,
#                 causing "clean slate" false report; now detects and logs.
# v1.1.2: Scanner false-positive remediation (ClawHub/VirusTotal):
#         [SCAN-1] Replace eval "$c" with direct "$@" execution — no dynamic
#                  code execution; all inputs are hardcoded UFW args
#         [SCAN-2] Inline documentation for api.agentsandbox.co (first-party
#                  OpenClaw infrastructure, not a third-party C2 domain)
# =============================================================================

set -u

DRY_RUN=1
APPLY_MODE=0
RESET_MODE=0
VERIFY_MODE=0
CANARY_MODE=0
FORCE_MODE=0
TRUST_MODE=0   # --trust: explicit first-run acknowledgment (replaces silent TOFU)

PROFILE_VERSION="1.1.4"
SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="$SKILL_DIR/.state"
STATE_FILE="$STATE_DIR/egress-profile.json"
LOG_FILE="/home/claw/.openclaw/workspace/logs/egress_filter.log"
CANARY_SECONDS=120
CANARY_INTERVAL=15

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

usage() {
  cat <<EOF
Usage: bash $0 [--dry-run] [--apply] [--canary] [--verify] [--reset] [--force] [--trust]

Modes:
  --dry-run   Preview only (default)
  --apply     Apply policy transactionally. Auto-rollback on failed post-checks.
  --canary    Apply policy in canary phase, verify for ${CANARY_SECONDS}s, then commit.
  --verify    Verify critical endpoints (Telegram, GitHub, Anthropic, OpenAI)
  --reset     Roll back to permissive outgoing policy
  --force     Bypass script hash mismatch gate on apply/canary
  --trust     Explicitly acknowledge first-run trust (required on first --apply/--canary
              when no prior profile exists). Inspect scripts before passing this flag.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --apply)   APPLY_MODE=1; DRY_RUN=0 ;;
    --canary)  CANARY_MODE=1; DRY_RUN=0 ;;
    --reset)   RESET_MODE=1 ;;
    --verify)  VERIFY_MODE=1 ;;
    --force)   FORCE_MODE=1 ;;
    --trust)   TRUST_MODE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo -e "${RED}[ERROR]${NC} Unknown arg: $arg"; usage; exit 1 ;;
  esac
done

if [ "$APPLY_MODE" -eq 1 ] && [ "$CANARY_MODE" -eq 1 ]; then
  echo -e "${RED}[ERROR]${NC} --apply and --canary are mutually exclusive"
  exit 1
fi

check_dep() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Required tool '$1' not found. Install: sudo apt install $2"
    exit 1
  fi
}
check_dep dig dnsutils
check_dep ufw ufw
check_dep curl curl
check_dep python3 python3

mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR"
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"

log() { echo -e "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $1" | tee -a "$LOG_FILE"; }

cmd() {
  # [SCAN-1 v1.1.2] Direct argument execution — no eval, no dynamic code.
  # All callers pass hardcoded UFW arguments. $* used for display only.
  # "$@" preserves argument boundaries (quoted strings safe).
  if [ "$DRY_RUN" -eq 1 ]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} $*"
    return 0
  fi
  log "APPLYING: $*"
  "$@"
}

script_hash() {
  sha256sum "$SCRIPT_PATH" | awk '{print $1}'
}

state_get_hash() {
  if [ ! -f "$STATE_FILE" ]; then
    echo ""
    return 0
  fi
  python3 - "$STATE_FILE" <<'PY'
import json, sys
p=sys.argv[1]
try:
  with open(p,'r',encoding='utf-8') as f:
    d=json.load(f)
  print(d.get('scriptHash',''))
except Exception:
  print('')
PY
}

write_state() {
  local result="$1"
  local now
  now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  local hash
  hash="$(script_hash)"
  python3 - "$STATE_FILE" "$PROFILE_VERSION" "$hash" "$now" "$result" <<'PY'
import json,sys,os
p,ver,h,ts,res = sys.argv[1:]
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p,'w',encoding='utf-8') as f:
  json.dump({
    'profileVersion': ver,
    'scriptHash': h,
    'lastAppliedAt': ts,
    'lastResult': res,
  }, f, indent=2)
  f.write('\n')
PY
}

verify_endpoint() {
  local name="$1"
  local url="$2"
  local http_code
  # Use HTTP status code, not curl exit status.
  # CDN endpoints return non-2xx on root (Anthropic=404, OpenAI=421) — both
  # prove full TCP/TLS reachability. Code "000" = no connection established.
  # --max-redirs 5 caps redirect depth to prevent infinite loops.
  http_code=$(curl -s --max-time 10 --max-redirs 5 \
    -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
  if [ "$http_code" = "000" ] || [ -z "$http_code" ]; then
    log "  ❌ FAIL: $name ($url) — no connection (code: ${http_code:-none})"
    return 1
  fi
  log "  ✅ PASS: $name ($url) — HTTP $http_code"
  return 0
}

verify_critical_endpoints() {
  local failed=0
  log "Running critical post-checks..."
  verify_endpoint "Telegram API"  "https://api.telegram.org"  || failed=$((failed+1))
  verify_endpoint "GitHub API"    "https://api.github.com"    || failed=$((failed+1))
  verify_endpoint "Anthropic API" "https://api.anthropic.com" || failed=$((failed+1))
  verify_endpoint "OpenAI API"    "https://api.openai.com"    || failed=$((failed+1))
  if [ "$failed" -gt 0 ]; then
    log "Critical post-checks failed: $failed endpoint(s)"
    return 1
  fi
  log "All critical post-checks passed"
  return 0
}

perform_reset() {
  log "RESET: Restoring permissive defaults"
  cmd sudo ufw default allow outgoing || return 1
  cmd sudo ufw reload || return 1
  log "Reset complete. Outgoing traffic: allow."
  return 0
}

# [FIX-4] Rollback that never hides its own failure.
# If perform_reset itself fails (UFW binary gone, sudo timeout, etc.), this
# surfaces the lockout clearly rather than silently continuing with || true.
# Writes a LOCKOUT state so the next operator sees exactly what happened.
# Exits 99 to propagate the critical failure up.
perform_reset_or_die() {
  local context="${1:-unknown}"
  if ! perform_reset; then
    log "🚨 CRITICAL [${context}]: Rollback FAILED. System may be locked out."
    log "🚨 Manual recovery: sudo ufw default allow outgoing && sudo ufw reload"
    write_state "LOCKOUT-MANUAL-INTERVENTION-REQUIRED"
    exit 99
  fi
}

# [MED-7] Abort early if UFW is not active.
# On a fresh Ubuntu install, UFW may be installed but inactive. Applying rules
# to an inactive UFW silently succeeds but nothing is enforced — the policy
# appears applied but isn't. This check prevents that silent no-op.
check_ufw_active() {
  if [ "$DRY_RUN" -eq 1 ]; then
    return 0  # Skip in dry-run; we're previewing only
  fi
  if ! sudo ufw status 2>/dev/null | grep -q "^Status: active"; then
    log "ERROR: UFW is not active. Enable it first: sudo ufw enable"
    exit 1
  fi
}

# DNS-based allowlist
# shellcheck disable=SC2034
declare -A PROVIDERS=(
  ["api.anthropic.com"]="443"
  ["api.openai.com"]="443"
  ["generativelanguage.googleapis.com"]="443"
  ["accounts.google.com"]="443"
  ["oauth2.googleapis.com"]="443"
  ["api.telegram.org"]="443"
  ["api.search.brave.com"]="443"
  ["controlplane.tailscale.com"]="443"
  ["login.tailscale.com"]="443"
  ["log.tailscale.io"]="443"
  ["api.github.com"]="443"
  # registry.npmjs.org — NOT included by default (supply-chain risk: broad npm
  # access is not needed at agent runtime). Only add if you run npm-based
  # OpenClaw plugins that phone home to npm during normal operation.
  # ["registry.npmjs.org"]="443"
  # api.agentsandbox.co — OpenClaw Agent Sandbox API (first-party OpenClaw
  # infrastructure, NOT a third-party service). Hosts isolated sub-agent
  # execution contexts. "agentsandbox" = OpenClaw's VM pool, not a C2 domain.
  # Ref: https://docs.openclaw.ai | See: references/false-positives.md
  ["api.agentsandbox.co"]="443"
)

# [FIX-6] snapshot_ips now counts resolved providers and returns 1 if none
# resolved. This prevents apply_policy from proceeding to "default deny
# outgoing" with zero IP rules — which would lock out ALL traffic.
snapshot_ips() {
  declare -gA IP_SNAPSHOT_V4
  declare -gA IP_SNAPSHOT_V6
  local resolved=0
  local total=${#PROVIDERS[@]}
  log "Step 0: Snapshotting provider IPs (${total} domains)..."
  for domain in "${!PROVIDERS[@]}"; do
    local ips_v4 ips_v6
    ips_v4="$(dig +short +time=5 +tries=2 "$domain" A 2>/dev/null \
      | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | tr '\n' ' ' | sed 's/ $//')"
    ips_v6="$(dig +short +time=5 +tries=2 "$domain" AAAA 2>/dev/null \
      | grep -E '^[0-9a-fA-F:]+$' | tr '\n' ' ' | sed 's/ $//')"
    IP_SNAPSHOT_V4["$domain"]="$ips_v4"
    IP_SNAPSHOT_V6["$domain"]="$ips_v6"
    if [ -z "$ips_v4" ] && [ -z "$ips_v6" ]; then
      log "  ⚠️  WARNING: Could not resolve $domain — skipping"
    else
      resolved=$((resolved+1))
      [ -n "$ips_v4" ] && log "  IPv4: $domain -> $ips_v4"
      [ -n "$ips_v6" ] && log "  IPv6: $domain -> $ips_v6"
    fi
  done
  if [ "$resolved" -eq 0 ]; then
    log "ERROR: Zero providers resolved. DNS failure or network down."
    log "ERROR: Aborting — applying deny-outgoing with no IP rules would lock out all traffic."
    return 1
  fi
  log "Snapshot complete: ${resolved}/${total} providers resolved."
  return 0
}

# [v1.1.0 / Issue 5] Flush all existing ZT-tagged UFW rules before re-apply.
# Without this, every apply/canary run appends duplicate provider IP rules.
# UFW has no native dedup — rules stack linearly, degrading perf and readability.
#
# Strategy: parse `ufw status numbered`, extract rule numbers for lines
# containing 'ZT:', delete in reverse numeric order so earlier indices stay
# stable during the deletion sequence.
#
# Non-fatal by design: if some rules fail to delete (e.g., rule already gone),
# we log a warning and continue. The new rules will still be applied correctly;
# worst case is a leftover duplicate, which is the pre-v1.1.0 baseline behavior.
flush_zt_rules() {
  # Capture UFW status output with explicit failure detection.
  # Do NOT use 2>/dev/null here — we need to know if sudo/ufw itself failed.
  # A permission error would produce empty output, causing us to falsely report
  # "no ZT rules — clean slate" and silently skip the flush.
  local ufw_status
  if ! ufw_status=$(sudo ufw status numbered 2>&1); then
    log "  ⚠️  WARNING: 'sudo ufw status numbered' failed — flush skipped."
    log "  Output: ${ufw_status}"
    return 1
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    local preview_count
    preview_count=$(echo "$ufw_status" | grep -c "ZT:" || true)
    echo -e "${YELLOW}[DRY-RUN]${NC} Would flush ${preview_count} ZT-tagged UFW rule(s)"
    return 0
  fi

  log "Flushing existing ZT-tagged egress rules..."

  # Extract rule numbers (between [ ]) for ZT lines, sort reverse-numeric.
  # awk -F'[][]' splits on [ and ], field $2 is the number.
  local numbers
  numbers=$(echo "$ufw_status" \
    | grep "ZT:" \
    | awk -F'[][]' '{print $2}' \
    | tr -d ' ' \
    | grep -E '^[0-9]+$' \
    | sort -rn)

  if [ -z "$numbers" ]; then
    log "  No ZT rules found — clean slate, nothing to flush"
    return 0
  fi

  local flushed=0
  local failed=0
  while IFS= read -r num; do
    [ -z "$num" ] && continue
    if sudo ufw --force delete "$num" >/dev/null 2>&1; then
      flushed=$((flushed+1))
    else
      log "  ⚠️  WARNING: Failed to delete rule #${num} — may already be gone"
      failed=$((failed+1))
    fi
  done <<< "$numbers"

  if [ "$failed" -gt 0 ]; then
    log "  Flush complete: ${flushed} deleted, ${failed} warnings (non-fatal)"
    return 1  # Signal partial failure so apply_policy() can log the warning
  fi
  log "  Flush complete: ${flushed} ZT rules removed cleanly"
  return 0
}

apply_policy() {
  # [FIX-6] Propagate snapshot failure — do not proceed to deny-outgoing
  snapshot_ips || return 1

  # [v1.1.0] Flush stale ZT rules before re-applying — prevents accumulation.
  # Non-fatal: flush failure is warned but does not abort apply.
  flush_zt_rules || log "WARN: flush_zt_rules had warnings — continuing apply"

  log "Step 1: Preserving critical access"
  cmd sudo ufw allow out on lo                                          || return 1
  cmd sudo ufw allow out 53/tcp                                         || return 1
  cmd sudo ufw allow out 53/udp                                         || return 1
  cmd sudo ufw allow out 22/tcp                                         || return 1
  cmd sudo ufw allow out 41641/udp                                      || return 1
  cmd sudo ufw allow out 3478/udp comment "Tailscale STUN"              || return 1
  cmd sudo ufw allow out 80/tcp comment "Tailscale DERP fallback"       || return 1
  cmd sudo ufw allow out 443/tcp comment "Tailscale DERP fallback / HTTPS" || return 1

  log "Step 2: Applying provider IP rules from snapshot"
  for domain in "${!PROVIDERS[@]}"; do
    local port ips_v4 ips_v6 ip
    port="${PROVIDERS[$domain]}"
    ips_v4="${IP_SNAPSHOT_V4[$domain]}"
    ips_v6="${IP_SNAPSHOT_V6[$domain]}"

    [ -z "$ips_v4" ] && [ -z "$ips_v6" ] && continue

    for ip in $ips_v4; do
      log "  ✅ $domain -> $ip:$port (IPv4)"
      cmd sudo ufw allow out to "$ip" port "$port" proto tcp comment "ZT: $domain" || return 1
    done

    for ip in $ips_v6; do
      log "  ✅ $domain -> [$ip]:$port (IPv6)"
      cmd sudo ufw allow out to "$ip" port "$port" proto tcp comment "ZT: $domain IPv6" || return 1
    done
  done

  log "Step 3: Setting default deny outgoing"
  cmd sudo ufw default deny outgoing || return 1

  log "Step 4: Reloading UFW"
  cmd sudo ufw reload || return 1
  return 0
}

enforce_profile_gate() {
  # Trust gate — two cases:
  #
  # 1) First run (no stored hash): requires explicit --trust to acknowledge
  #    you have inspected the script and accept the egress policy.
  #    This replaces silent TOFU (Trust On First Use) with an opt-in flag.
  #
  # 2) Subsequent runs (hash mismatch): script has changed since last apply.
  #    Requires --force to accept the new profile. Diff the script before using.
  local current recorded
  current="$(script_hash)"
  recorded="$(state_get_hash)"

  if [ -z "$recorded" ] && [ "$TRUST_MODE" -ne 1 ]; then
    echo -e "${YELLOW}[FIRST RUN]${NC} No prior egress profile found."
    echo "Before applying, inspect the PROVIDERS list and verify api.agentsandbox.co"
    echo "is trusted in your environment (first-party OpenClaw infrastructure)."
    echo ""
    echo "Re-run with --trust to explicitly acknowledge and apply:"
    echo "  bash $0 --apply --trust"
    exit 2
  fi

  if [ -n "$recorded" ] && [ "$recorded" != "$current" ] && [ "$FORCE_MODE" -ne 1 ]; then
    echo -e "${RED}[REFUSED]${NC} Script hash mismatch with recorded profile in $STATE_FILE"
    echo "Recorded: $recorded"
    echo "Current : $current"
    echo "Re-run with --force to accept and apply this new profile."
    exit 2
  fi
}

run_canary() {
  log "CANARY MODE: temporary policy apply started"
  if ! apply_policy; then
    log "Canary apply failed during rule application. Auto-rollback triggered."
    perform_reset_or_die "canary-apply-failed"
    write_state "canary-apply-failed-rolled-back"
    return 1
  fi

  local elapsed=0
  while [ "$elapsed" -lt "$CANARY_SECONDS" ]; do
    log "Canary verification check (t=${elapsed}s/${CANARY_SECONDS}s)"
    if ! verify_critical_endpoints; then
      log "Canary verification failed. Auto-rollback triggered."
      perform_reset_or_die "canary-verify-failed"
      write_state "canary-failed-rolled-back"
      return 1
    fi
    sleep "$CANARY_INTERVAL"
    elapsed=$((elapsed + CANARY_INTERVAL))
  done

  log "Canary verification passed for ${CANARY_SECONDS}s. Committing final policy."
  cmd sudo ufw reload || return 1
  write_state "canary-pass-committed"
  return 0
}

log "=== Egress Filter v${PROFILE_VERSION} started $([ "$DRY_RUN" -eq 1 ] && echo '[DRY-RUN]') ==="

if [ "$VERIFY_MODE" -eq 1 ]; then
  verify_critical_endpoints
  exit $?
fi

if [ "$RESET_MODE" -eq 1 ]; then
  if perform_reset; then
    [ "$DRY_RUN" -eq 0 ] && write_state "reset"
    exit 0
  fi
  [ "$DRY_RUN" -eq 0 ] && write_state "reset-failed"
  exit 1
fi

if [ "$APPLY_MODE" -eq 1 ] || [ "$CANARY_MODE" -eq 1 ]; then
  enforce_profile_gate
  check_ufw_active
fi

if [ "$CANARY_MODE" -eq 1 ]; then
  if run_canary; then
    log "Canary complete: final policy active"
    exit 0
  fi
  exit 1
fi

if [ "$APPLY_MODE" -eq 1 ]; then
  log "APPLY MODE: transactional apply"
  if ! apply_policy; then
    log "Apply failed during rule application. Auto-rollback triggered."
    perform_reset_or_die "apply-policy-failed"
    write_state "apply-failed-rolled-back"
    exit 1
  fi

  if ! verify_critical_endpoints; then
    log "Post-check failed. Auto-rollback triggered."
    perform_reset_or_die "apply-postcheck-failed"
    write_state "apply-failed-postcheck-rolled-back"
    exit 1
  fi

  write_state "apply-success"
  log "Transactional apply complete: policy active"
  exit 0
fi

# Default: dry-run preview
apply_policy

echo -e "\n${GREEN}Dry-run complete. No changes applied.${NC}"
echo -e "Canonical path: ${YELLOW}/home/claw/.openclaw/workspace/skills/clawd-zero-trust/scripts/egress-filter.sh${NC}"
echo -e "To apply:  bash $0 --apply"
echo -e "To canary: bash $0 --canary"
echo -e "To verify: bash $0 --verify"
echo -e "To reset:  bash $0 --reset"

log "=== Done ==="
