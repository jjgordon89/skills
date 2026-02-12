---
name: loxone
version: 1.1.0
homepage: https://github.com/odrobnik/loxone-skill
metadata: {"openclaw": {"emoji": "🏠", "requires": {"bins": ["python3"]}}}
description: Control and monitor a Loxone Miniserver (smart home) via HTTP API and real-time WebSocket. Use for querying room/device status (temperatures, lights), watching live events, and sending safe control commands.
---

# Loxone (Smart Home)

## Setup
- Create `config.json` next to this file (it is gitignored). Start from `config.json.example`.

### Config: Local vs Cloud DNS tunnel
The `host` value can be either:
- **Local**: an IP/hostname, e.g. `192.168.0.222` (typically `use_https: false` on LAN), or
- **Arbitrary hostname**: e.g. `loxone.example.com` or `loxone.example.com:443` (works with HTTPS if the certificate is valid for that hostname), or
- **Cloud DNS shorthand** (preferred for remote access; avoids hard-coded IPs):
  - `dns.loxonecloud.com/<SERIAL>` (or just `<SERIAL>`)

When you use the Cloud DNS shorthand, the skill resolves it at runtime via
`https://dns.loxonecloud.com/?getip&snr=<SERIAL>&json=true` and uses the
certificate-matching `*.dyndns.loxonecloud.com` hostname (including port).

## Commands
- `python3 scripts/loxone.py rooms`
- `python3 scripts/loxone.py map`
- `python3 scripts/loxone.py status "<Room>"`
- `python3 scripts/loxone.py control "<Room>" "<Control>" on|off`
- `python3 scripts/loxone_watch.py --room "<Room>" [--changes-only] [--duration <sec>]`

## Notes
- Treat as **read-only by default**; only use control commands when explicitly requested.
- WebSocket auth can be finicky; if WS fails, fall back to HTTP status queries.


## Security
- HTTPS + certificate verification is enabled by default.
- For LAN access without SSL, set `"use_https": false` in config.json. When `use_https` is true (default), SSL certificates are always verified — install a proper cert or use the Loxone Cloud DNS tunnel.
