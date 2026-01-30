---
name: dont-hack-me
description: >-
  別駭我！基本安全檢測 — Security self-check for OpenClaw (Clawdbot/Moltbot).
  14-point audit of your clawdbot.json: exposed gateway, missing auth,
  open DM policy, weak tokens, file permissions, reverse proxy bypass,
  Tailscale exposure, directory perms, browser control, log redaction,
  control UI exposure, mDNS broadcasting.
  Auto-fix included.
  Invoke: "run a security check" or "幫我做安全檢查".
author: "小安 Ann Agent — Taiwan 台灣"
homepage: https://github.com/peterann/dont-hack-me
metadata:
  clawdbot:
    emoji: "🔒"
---

# dont-hack-me

Security self-check skill for OpenClaw (formerly Clawdbot / Moltbot).
Reads `~/.clawdbot/clawdbot.json` and checks 14 items that cover the most
common misconfigurations. Outputs a simple PASS / FAIL / WARN report.

## How to run

Say any of:

- "run a security check"
- "check my security settings"
- "audit my clawdbot config"
- "audit my openclaw config"
- "am I secure?"

## Checklist — step by step

When this skill is triggered, follow these steps **exactly**:

### Step 0 — Read the config

Use the `read` tool to open `~/.clawdbot/clawdbot.json`.
(Note: the config path is still `~/.clawdbot/` even after the OpenClaw rebrand.)
Parse the JSON content. If the file does not exist or is unreadable,
report an error and stop.

Also run shell commands to get file and directory permissions, and check the mDNS environment variable:
```bash
stat -f '%Lp' ~/.clawdbot/clawdbot.json
stat -f '%Lp' ~/.clawdbot/
echo ${CLAWDBOT_DISABLE_BONJOUR:-unset}
```
(On Linux: use `stat -c '%a'` instead of `stat -f '%Lp'`)

### Step 1 — Gateway Bind

- **Path:** `gateway.bind`
- **Expected:** `"loopback"`
- **Valid values (schema-enforced):** `"auto"`, `"lan"`, `"loopback"`, `"custom"`, `"tailnet"`
- **PASS** if the value is `"loopback"` or the key is absent (default is `"loopback"`)
- **FAIL** if the value is `"lan"`, `"auto"`, `"custom"`, `"tailnet"`, or any non-loopback setting
- **Severity:** CRITICAL — a non-loopback bind exposes your agent to the network

### Step 2 — Gateway Auth Mode

- **Path:** `gateway.auth.mode`
- **Expected:** `"token"` or `"password"`
- **Valid values (schema-enforced):** `"token"`, `"password"`. At runtime, `"none"` is derived when neither token nor password is configured — but `"none"` and `"off"` cannot appear in the JSON file.
- **PASS** if `gateway.auth.mode` is `"token"` or `"password"`
- **PASS** if `gateway.auth.mode` is absent but `gateway.auth.token` exists (runtime resolves to `"token"`)
- **WARN** if the entire `gateway.auth` section is absent, or both `mode` and `token` are absent — runtime may default to no authentication (unless the env var `CLAWDBOT_GATEWAY_TOKEN` is set, which we cannot check from config alone)
- **Severity:** CRITICAL — without auth anyone who can reach the gateway can control your agent

### Step 3 — Token Strength

- **Path:** `gateway.auth.token`
- **Expected:** 32 or more characters
- **PASS** if the token is >= 32 characters
- **WARN** if the token is 16–31 characters
- **FAIL** if the token is < 16 characters or empty
- **SKIP** if auth mode is `"password"` (passwords are user-chosen, don't judge length)
- **Severity:** HIGH — short tokens are vulnerable to brute-force

### Step 4 — DM Policy (per channel)

- **Path:** `channels.<name>.dmPolicy` for each channel
- **Expected:** `"pairing"`, `"allowlist"`, or `"disabled"`
- **PASS** if `dmPolicy` is `"pairing"`, `"allowlist"`, or `"disabled"`
- **PASS** if `dmPolicy` is `"open"` but `allowFrom` (same level) has at least one entry
- **FAIL** if `dmPolicy` is `"open"` and `allowFrom` is missing or empty
- **SKIP** if no channels are configured
- **Severity:** HIGH — an open DM policy lets anyone send commands to your agent

### Step 5 — Group Policy (per channel)

- **Path:** `channels.<name>.groupPolicy` for each channel
- **Expected:** `"allowlist"` or `"disabled"`
- **Valid values (schema-enforced):** `"open"`, `"disabled"`, `"allowlist"`
- **PASS** if `groupPolicy` is `"allowlist"`, `"disabled"`, or absent (default is `"allowlist"`)
- **FAIL** if `groupPolicy` is `"open"`
- **SKIP** if no channels are configured
- **Severity:** HIGH — an open group policy lets any group trigger your agent

### Step 6 — File Permissions

- **Check:** file mode of `~/.clawdbot/clawdbot.json`
- **Expected:** `600` or `400` (owner read/write only)
- **PASS** if permissions are `600` or `400`
- **WARN** if group or others can read but NOT write (e.g., `644`, `640`, `604`) — use bitwise check: `(mode & 0o044) != 0` and `(mode & 0o022) == 0`
- **FAIL** if others or group can write (e.g., `777`, `666`, `662`) — use bitwise check: `(mode & 0o022) != 0`
- **Severity:** MEDIUM — loose permissions let other users on the system read your tokens

### Step 7 — Plaintext Secrets Scan

- **Check:** scan all string values in the JSON for keys named `password`, `secret`, `apiKey`, `api_key`, `privateKey`, `private_key` (case-insensitive) that contain a non-empty string value
- **PASS** if no such keys are found
- **WARN** if such keys exist — remind the user to consider using environment variables or a secrets manager
- **Note:** `token` under `gateway.auth` is expected and should NOT be flagged
- **Note:** Channel-specific tokens like `botToken` (Telegram) SHOULD be flagged as WARN — they are required for operation but are high-value targets if the config leaks
- **Severity:** MEDIUM — plaintext secrets in config files can be leaked through backups, logs, or version control

### Step 8 — Reverse Proxy (trustedProxies)

- **Path:** `gateway.trustedProxies`
- **Context:** When OpenClaw sits behind nginx, Caddy, or any reverse proxy on the same machine, all connections appear to come from 127.0.0.1. Without `trustedProxies`, the gateway treats every proxied request as a local client and skips auth.
- **PASS** if `trustedProxies` is a non-empty array (proxy IPs are explicitly listed)
- **PASS** if `trustedProxies` is absent or empty AND bind is `"loopback"` — print as: `✅ PASS — no proxy, bind is loopback (set trustedProxies if you add one later)`
- **WARN** if `trustedProxies` is absent or empty AND bind is NOT `"loopback"` (e.g., `"lan"`) — the gateway is network-exposed and any proxy can spoof local access
- **Fix:** Ask the user for their proxy IP(s) and set:
  ```json
  { "gateway": { "trustedProxies": ["127.0.0.1"] } }
  ```
- **Severity:** CRITICAL — this is the #1 real-world exploit vector (CVE-2025-49596)

### Step 9 — Tailscale Exposure

- **Path:** `gateway.tailscale.mode`
- **Expected:** `"off"`
- **Valid values (schema-enforced):** `"off"`, `"serve"`, `"funnel"`
- **PASS** if the value is `"off"` or the key is absent (default is `"off"`)
- **WARN** if the value is `"serve"` — the gateway becomes reachable by all devices on your tailnet
- **FAIL** if the value is `"funnel"` — the gateway is exposed to the public internet via Tailscale Funnel
- **Fix:** Set `gateway.tailscale.mode` to `"off"`:
  ```json
  { "gateway": { "tailscale": { "mode": "off" } } }
  ```
- **Severity:** HIGH (serve — tailnet-only exposure) to CRITICAL (funnel — public internet exposure)

### Step 10 — Directory Permissions

- **Check:** file mode of the `~/.clawdbot/` directory itself
- Run: `stat -f '%Lp' ~/.clawdbot/` (macOS) or `stat -c '%a' ~/.clawdbot/` (Linux)
- **Expected:** `700` (owner only)
- **PASS** if permissions are `700`
- **WARN** if permissions are `755` or `750` — other users can list filenames inside
- **FAIL** if permissions are `777` or anything world-writable
- **Fix:** Run:
  ```bash
  chmod 700 ~/.clawdbot/
  ```
- **Severity:** MEDIUM — even if individual files are 600, a listable directory leaks filenames and structure to other users on the system. Infostealers (RedLine, Lumma, Vidar) specifically target `~/.clawdbot/`.

### Step 11 — Browser Control Exposure

- **Path:** `browser.controlUrl` and `browser.controlToken`
- **Context:** OpenClaw can remote-control a browser. If `controlUrl` is set but `controlToken` is missing, anyone who knows the URL can hijack the browser session.
- Also check `gateway.controlUi.allowInsecureAuth` — if `true`, token auth is allowed over plain HTTP (tokens can be sniffed).
- **PASS** if `browser.controlUrl` is absent (browser control not configured)
- **PASS** if `browser.controlUrl` is set AND `browser.controlToken` is also set
- **FAIL** if `browser.controlUrl` is set but `browser.controlToken` is missing or empty
- **WARN** if `gateway.controlUi.allowInsecureAuth` is `true` — tokens sent over HTTP can be intercepted
- **Note:** If both FAIL (missing token) and WARN (insecureAuth) trigger, report as 1 item with the highest severity (FAIL). Fix both.
- **Fix:** Set a control token:
  ```bash
  openssl rand -hex 24
  ```
  Write the output into `browser.controlToken`. If `allowInsecureAuth` is true, set it to false:
  ```json
  { "gateway": { "controlUi": { "allowInsecureAuth": false } } }
  ```
- **Severity:** HIGH — browser control without auth allows remote UI takeover and access to any logged-in sessions

### Step 12 — Logging Redaction

- **Path:** `logging.redactSensitive`
- **Expected:** `"tools"` (the only safe value besides being absent)
- **Valid values:** `"off"` or `"tools"` — there is no `"all"` option
- **PASS** if the value is `"tools"` or the key is absent (default is `"tools"`)
- **WARN** if the value is `"off"` — sensitive tool output (API keys, tokens, credentials) will appear in plaintext in session logs
- **Fix:** Set `logging.redactSensitive` to `"tools"`:
  ```json
  { "logging": { "redactSensitive": "tools" } }
  ```
- **Severity:** MEDIUM — with redaction off, any secret that passes through a tool call gets logged in plaintext at `~/.clawdbot/logs/`

### Step 13 — Control UI Exposure

- **Path:** `gateway.controlUi.enabled`
- **Context:** OpenClaw includes a web-based control dashboard. When enabled (the default), the dashboard is accessible on the gateway port. Combined with a non-loopback bind, this exposes the full control interface to the network.
- **PASS** if `gateway.controlUi.enabled` is `false`
- **PASS** if `gateway.controlUi.enabled` is `true` (or absent, default is `true`) AND bind is `"loopback"` — dashboard only accessible locally
- **WARN** if `gateway.controlUi.enabled` is `true` (or absent) AND bind is NOT `"loopback"` — dashboard exposed to network
- **Fix:** Set `gateway.controlUi.enabled` to `false`:
  ```json
  { "gateway": { "controlUi": { "enabled": false } } }
  ```
- **Severity:** MEDIUM-HIGH — a network-exposed control UI lets anyone on the network interact with the agent dashboard

### Step 14 — mDNS / Bonjour Broadcasting

- **Check:** Whether mDNS (Bonjour) service discovery is disabled
- **Context:** OpenClaw broadcasts `_clawdbot-gw._tcp.local` via mDNS by default, advertising detailed service information to all devices on the local network. TXT records include: gateway port, LAN hostname, display name, SSH port (default 22), CLI path, TLS fingerprint, canvas port, and tailnet DNS address (when applicable). This is controlled by the environment variable `CLAWDBOT_DISABLE_BONJOUR`, not by clawdbot.json. A watchdog re-advertises every 60 seconds.
- **Detection:** In Step 0 you already ran `echo ${CLAWDBOT_DISABLE_BONJOUR:-unset}`. Use that result here.
- **PASS** if `CLAWDBOT_DISABLE_BONJOUR` is set to `1`
- **WARN** if `CLAWDBOT_DISABLE_BONJOUR` is unset or not `1` — your OpenClaw instance is advertising its presence and port to the entire LAN
- **Note:** This cannot be fixed by editing clawdbot.json. The environment variable must be set in the shell profile or process environment.
- **Fix (advisory):** Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
  ```bash
  export CLAWDBOT_DISABLE_BONJOUR=1
  ```
  Then restart the gateway: `clawdbot gateway restart`
- **Severity:** HIGH — passive information leak enables network reconnaissance; attackers on the same LAN can discover all OpenClaw instances without probing

## Output format

After completing all checks, output a report in this exact format:

```
🔒 Security Check Report

 1. Gateway Bind        <ICON> <STATUS> — <detail>
 2. Gateway Auth        <ICON> <STATUS> — <detail>
 3. Token Strength      <ICON> <STATUS> — <detail>
 4. DM Policy           <ICON> <STATUS> — <detail>
 5. Group Policy        <ICON> <STATUS> — <detail>
 6. File Permissions    <ICON> <STATUS> — <detail>
 7. Secrets Scan        <ICON> <STATUS> — <detail>
 8. Reverse Proxy       <ICON> <STATUS> — <detail>
 9. Tailscale           <ICON> <STATUS> — <detail>
10. Directory Perms     <ICON> <STATUS> — <detail>
11. Browser Control     <ICON> <STATUS> — <detail>
12. Log Redaction       <ICON> <STATUS> — <detail>
13. Control UI          <ICON> <STATUS> — <detail>
14. mDNS Broadcasting   <ICON> <STATUS> — <detail>

Score: X/14 PASS, Y WARN, Z FAIL
```

Where:
- `<ICON>` is one of: ✅ (PASS), ⚠️ (WARN), ❌ (FAIL), ⏭️ (SKIP)
- `<STATUS>` is one of: `PASS`, `WARN`, `FAIL`, `SKIP`
- `<detail>` is a short explanation (e.g., "loopback", "token mode", "48 chars", "permissions 600")
- SKIP items do not count toward the denominator. If 2 items are skipped, the score line reads `X/12` not `X/14`

## Auto-fix flow

If **any** item is FAIL or WARN, do the following:

1. Show the report first (as above).
2. List each fixable item with a short description of what will be changed.
3. Ask the user: **"Want me to fix these? (yes / no / pick)"**
   - **yes** — fix all FAIL and WARN items automatically, EXCEPT items marked "⚠️ NEEDS EXTRA CONFIRMATION" (#3 Token, #9 Tailscale) — those always require individual yes/no even in "yes" mode.
   - **no** — stop, do nothing.
   - **pick** — let the user choose which items to fix.
4. Apply the fixes (see Fix recipes below). Items marked "NEEDS EXTRA CONFIRMATION" must be confirmed individually before applying.
5. After applying, re-read the config and re-run the full check to confirm everything is PASS.
6. If the config was changed, remind the user: **"Run `clawdbot gateway restart` to apply the new settings."**

### Fix recipes

Use these exact fixes for each item. Edit `~/.clawdbot/clawdbot.json` using the edit/write tool.

#### #1 Gateway Bind — FAIL
Set `gateway.bind` to `"loopback"`:
```json
{ "gateway": { "bind": "loopback" } }
```

#### #2 Gateway Auth — WARN
Set `gateway.auth.mode` to `"token"`. If no token exists yet, also generate one:
```json
{ "gateway": { "auth": { "mode": "token", "token": "<GENERATED>" } } }
```
Generate the token with:
```bash
openssl rand -hex 24
```
That produces a 48-character hex string (192-bit entropy).

#### #3 Token Strength — FAIL / WARN ⚠️ NEEDS EXTRA CONFIRMATION
**Warning:** Replacing the token disconnects ALL paired devices (Telegram, phones, other clients). They will need the new token to reconnect.
Always ask the user before changing: "Replacing the gateway token will disconnect all paired devices. Proceed?"
If confirmed, generate a new token:
```bash
openssl rand -hex 24
```
Write the output into `gateway.auth.token`.

#### #4 DM Policy — FAIL
Set `dmPolicy` to `"pairing"` for each affected channel:
```json
{ "channels": { "<name>": { "dmPolicy": "pairing" } } }
```

#### #5 Group Policy — FAIL
Set `groupPolicy` to `"allowlist"` for each affected channel:
```json
{ "channels": { "<name>": { "groupPolicy": "allowlist" } } }
```

#### #6 File Permissions — FAIL / WARN
Run:
```bash
chmod 600 ~/.clawdbot/clawdbot.json
```

#### #7 Secrets Scan — WARN
This one cannot be auto-fixed safely. Instead, list each flagged key and
remind the user:
- Move the value to an environment variable
- Or use a secrets manager
- Reference it in the config as `"$ENV_VAR_NAME"` if the platform supports it

#### #8 Reverse Proxy — WARN
Ask the user: "Are you running a reverse proxy (nginx, Caddy, etc.) in front of OpenClaw?"
- If yes: ask for the proxy IP(s) and set:
  ```json
  { "gateway": { "trustedProxies": ["127.0.0.1"] } }
  ```
- If no: mark as INFO/acknowledged, no config change needed

#### #9 Tailscale — WARN (serve) / FAIL (funnel) ⚠️ NEEDS EXTRA CONFIRMATION
**Warning:** Disabling Tailscale cuts off remote access for all tailnet devices. For `"funnel"` mode, disabling also removes public internet access.
Always ask the user before changing: "Disabling Tailscale mode means the gateway is no longer reachable from your tailnet (or from the public internet if using funnel). If you need remote access, use SSH tunneling instead. Proceed?"
If confirmed, set `gateway.tailscale.mode` to `"off"`:
```json
{ "gateway": { "tailscale": { "mode": "off" } } }
```

#### #10 Directory Permissions — WARN / FAIL
Run:
```bash
chmod 700 ~/.clawdbot/
```

#### #11 Browser Control — FAIL / WARN
If `controlToken` is missing, generate and set one:
```bash
openssl rand -hex 24
```
Write into `browser.controlToken`.
If `allowInsecureAuth` is true, set to false:
```json
{ "gateway": { "controlUi": { "allowInsecureAuth": false } } }
```

#### #12 Logging Redaction — WARN
Set `logging.redactSensitive` to `"tools"`:
```json
{ "logging": { "redactSensitive": "tools" } }
```

#### #13 Control UI — WARN
Set `gateway.controlUi.enabled` to `false`:
```json
{ "gateway": { "controlUi": { "enabled": false } } }
```

#### #14 mDNS Broadcasting — WARN
This one cannot be auto-fixed by editing clawdbot.json (it is controlled by
an environment variable, not the config file). Instead, instruct the user:
- Add `export CLAWDBOT_DISABLE_BONJOUR=1` to `~/.zshrc` (macOS) or `~/.bashrc` (Linux)
- Then run `source ~/.zshrc && clawdbot gateway restart`

### Important rules for auto-fix

- **Always back up first.** Before writing any changes, copy the original:
  ```bash
  cp ~/.clawdbot/clawdbot.json ~/.clawdbot/clawdbot.json.bak
  ```
- **Merge, don't overwrite.** Read the full JSON, modify only the specific
  keys, write back the complete JSON. Never lose existing settings.
- **Preserve formatting.** Write the JSON with 2-space indentation.
- **One write operation.** Collect all JSON fixes, apply them in a single
  write to avoid partial states.
- **Token replacement requires restart.** If the gateway token was changed,
  the user must update any paired clients with the new token.
  Warn: "Your gateway token was changed. Any paired devices will need the
  new token to reconnect."

## What this skill does NOT check

- Sandbox configuration (not needed for most setups)
- Network isolation / Docker (macOS native setups don't use it)
- MCP tool permissions (too complex for a basic audit)
- Whether your OS firewall is configured
- Whether your agent code has vulnerabilities

For a more comprehensive audit, see community tools like `clawdbot-security-check`.

## Reference

Based on the community-compiled "Top 10 Clawdbot/Moltbot/OpenClaw Security Vulnerabilities" list,
plus January 2026 disclosures (CVE-2025-49596 reverse proxy bypass, infostealer targeting,
Tailscale exposure, browser control, logging redaction, mDNS broadcasting,
control UI exposure). Covers 14 items for typical macOS-native deployments.

---

*小安 Ann Agent — Taiwan 台灣*
*Building skills and local MCP services for all AI agents, everywhere.*
*為所有 AI Agent 打造技能與在地 MCP 服務，不限平台。*
