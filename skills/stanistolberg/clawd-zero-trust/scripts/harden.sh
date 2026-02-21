#!/bin/bash
# =============================================================================
# Zero Trust Hardening Script — clawd-zero-trust skill
# Guides and applies: plugin allowlist, PLP toolset config, SSH lockdown,
# SecureClaw install if missing, and gateway bind check.
#
# MODES:
#   --dry-run (default): Show what would change, apply nothing
#   --apply:             Actually apply all changes
#
# Idempotent: each change is checked before applying.
# =============================================================================

OPENCLAW="${OPENCLAW_BIN:-$(which openclaw 2>/dev/null || echo '/home/claw/.npm-global/bin/openclaw')}"
CONFIG="${OPENCLAW_CONFIG:-$HOME/.openclaw/openclaw.json}"
DRY_RUN=1

# Color output
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# Parse args
for arg in "$@"; do
  case $arg in
    --apply)   DRY_RUN=0 ;;
    --dry-run) DRY_RUN=1 ;;
  esac
done

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }
apply() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} Would apply: $*"
  else
    info "Applying: $*"
    "$@"
  fi
}
apply_jq() {
  # apply_jq <description> <jq_filter> <file>
  local desc="$1" filter="$2" file="$3"
  if [ "$DRY_RUN" -eq 1 ]; then
    local result
    result=$(jq "$filter" "$file" 2>/dev/null)
    echo -e "${YELLOW}[DRY-RUN]${NC} $desc"
    echo -e "  Would produce:\n$(echo "$result" | head -20)"
  else
    local tmp
    tmp=$(mktemp)
    if jq "$filter" "$file" > "$tmp" 2>/dev/null; then
      mv "$tmp" "$file"
      ok "$desc — applied"
    else
      rm -f "$tmp"
      fail "$desc — jq filter failed"
    fi
  fi
}

echo ""
echo "🔧 clawd-zero-trust Hardening — $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "=================================================="
if [ "$DRY_RUN" -eq 1 ]; then
  echo -e "${YELLOW}Mode: DRY-RUN (no changes applied). Pass --apply to execute.${NC}"
else
  echo -e "${RED}Mode: APPLY — changes will be written to disk.${NC}"
fi
echo ""

# Validate dependencies
if ! command -v jq &>/dev/null; then
  fail "jq is required but not installed. Run: sudo apt install jq"
  exit 1
fi
if [ ! -f "$CONFIG" ]; then
  fail "openclaw.json not found at: $CONFIG"
  exit 1
fi

# =============================================================================
# 1. SecureClaw
# =============================================================================
echo "1️⃣  SecureClaw:"
if "$OPENCLAW" plugins list 2>/dev/null | grep -q "secureclaw.*loaded"; then
  ok "SecureClaw loaded"
else
  warn "SecureClaw not loaded."
  echo "  Install via ClawHub: openclaw skills install secureclaw"
  echo "  Or see: https://docs.openclaw.ai/skills/secureclaw"
fi

# =============================================================================
# 2. Plugin Allowlist (idempotent: add secureclaw if missing)
#
# SECURITY NOTICE: This block manages OpenClaw's plugin allow-list.
# It is a RESTRICTION, not an expansion — plugins.allow limits which plugins
# can run. Only 'secureclaw' is added to an existing list.
#
# Plugin inventory (all first-party OpenClaw / Blocksoft verified):
#   google-antigravity-auth  — Google OAuth provider (official OpenClaw)
#   telegram                 — Telegram messaging provider (official OpenClaw)
#   openclaw-agentsandbox    — Agent sandbox isolation layer (official OpenClaw)
#   openclaw-mcp-adapter     — MCP protocol adapter (official OpenClaw)
#   secureclaw               — Security audit engine (adversa-ai, open source)
#
# The bootstrap list (null-config case) is only written when NO plugins.allow
# exists. Set HARDEN_SKIP_PLUGIN_BOOTSTRAP=1 to skip that case entirely.
# Ref: references/false-positives.md
# =============================================================================
echo ""
echo "2️⃣  Plugin Allowlist:"

# Bootstrap skip: set env var to skip null-config plugin initialization
SKIP_BOOTSTRAP="${HARDEN_SKIP_PLUGIN_BOOTSTRAP:-0}"

# Only the security plugin is added to existing lists
SECURECLAW_PLUGIN="secureclaw"

# Bootstrap list: used ONLY when plugins.allow is entirely absent
# Contains verified first-party OpenClaw plugins only (see header above)
BOOTSTRAP_PLUGINS='["google-antigravity-auth","telegram","openclaw-agentsandbox","openclaw-mcp-adapter","secureclaw"]'

# Check current state
CURRENT_ALLOW=$(jq -r '.plugins.allow // empty' "$CONFIG" 2>/dev/null)
SECURECLAW_IN_ALLOW=$(jq -e '.plugins.allow | if . == null then false elif (. | map(select(. == "secureclaw")) | length > 0) then true else false end' "$CONFIG" 2>/dev/null || echo "false")

if [ "$SECURECLAW_IN_ALLOW" = "true" ]; then
  ok "plugins.allow already contains '$SECURECLAW_PLUGIN' — no changes made"
  info "Current allow list: $CURRENT_ALLOW"
else
  if [ -z "$CURRENT_ALLOW" ] || [ "$CURRENT_ALLOW" = "null" ]; then
    if [ "$SKIP_BOOTSTRAP" = "1" ]; then
      warn "plugins.allow absent but HARDEN_SKIP_PLUGIN_BOOTSTRAP=1 — skipping bootstrap"
    else
      warn "plugins.allow is absent — bootstrap case: initializing with verified first-party plugin set"
      warn "Plugins to be written: $BOOTSTRAP_PLUGINS"
      warn "This RESTRICTS OpenClaw to these plugins only. To skip: HARDEN_SKIP_PLUGIN_BOOTSTRAP=1"
      apply_jq "Bootstrap plugins.allow with verified first-party plugin set" \
        ".plugins.allow = ${BOOTSTRAP_PLUGINS}" \
        "$CONFIG"
      info "AUDIT LOG: plugins.allow bootstrapped with: ${BOOTSTRAP_PLUGINS}"
    fi
  else
    warn "plugins.allow exists but missing '$SECURECLAW_PLUGIN' — adding security audit plugin only"
    info "Current list: $CURRENT_ALLOW"
    info "Adding: $SECURECLAW_PLUGIN (OpenClaw security audit engine — adversa-ai/secureclaw)"
    apply_jq "Add $SECURECLAW_PLUGIN to plugins.allow (security audit plugin only)" \
      '.plugins.allow |= (. + ["secureclaw"] | unique)' \
      "$CONFIG"
    info "AUDIT LOG: added '$SECURECLAW_PLUGIN' to existing plugins.allow"
  fi
fi

# =============================================================================
# 3. PLP — tools.byProvider (idempotent)
# =============================================================================
echo ""
echo "3️⃣  PLP (Principle of Least Privilege):"
BYPROVIDER_EXISTS=$(jq -e '.tools.byProvider != null' "$CONFIG" 2>/dev/null || echo "false")

if [ "$BYPROVIDER_EXISTS" = "true" ]; then
  ok "tools.byProvider already configured"
  info "Current: $(jq -c '.tools.byProvider' "$CONFIG" 2>/dev/null)"
else
  warn "tools.byProvider not configured — will apply PLP restriction"
  PLP_CONFIG='{
    "google-antigravity/gemini-3-flash": {
      "profile": "coding",
      "allow": ["web_search","web_fetch","message","session_status"]
    }
  }'
  apply_jq "Set tools.byProvider" \
    ".tools.byProvider = ${PLP_CONFIG}" \
    "$CONFIG"
fi

# =============================================================================
# 4. SSH Perimeter (check only — modifying sshd_config requires sudo)
# =============================================================================
echo ""
echo "4️⃣  SSH Perimeter:"
if ss -ltnp 2>/dev/null | grep ':22' | grep -qE '0\.0\.0\.0|\[::\]'; then
  warn "SSH exposed to 0.0.0.0 or [::] (all interfaces)."
  echo "  Add to /etc/ssh/sshd_config:"
  echo "    ListenAddress 127.0.0.1"
  echo "    ListenAddress <YOUR_TAILSCALE_IP>"
  echo "  Then: sudo systemctl restart ssh"
  if [ "$DRY_RUN" -eq 0 ]; then
    warn "SSH config requires manual edit — skipping auto-apply for safety."
  fi
else
  ok "SSH restricted (not bound to all interfaces)"
fi

# =============================================================================
# 5. Gateway bind (idempotent)
# =============================================================================
echo ""
echo "5️⃣  Gateway:"
GATEWAY_BIND=$(jq -r '.gateway.bind // empty' "$CONFIG" 2>/dev/null)
if [ "$GATEWAY_BIND" = "loopback" ]; then
  ok "Gateway bound to loopback"
else
  warn "Gateway not bound to loopback (current: '${GATEWAY_BIND:-unset}')"
  apply_jq "Set gateway.bind = loopback" \
    '.gateway.bind = "loopback"' \
    "$CONFIG"
fi

# =============================================================================
# Summary diff (apply mode only)
# =============================================================================
echo ""
echo "=================================================="
if [ "$DRY_RUN" -eq 1 ]; then
  echo -e "${YELLOW}Dry-run complete. No changes applied.${NC}"
  echo -e "To apply: ${GREEN}bash $0 --apply${NC}"
else
  echo -e "${GREEN}Hardening applied.${NC}"
  echo "Next: bash egress-filter.sh --dry-run"
fi
