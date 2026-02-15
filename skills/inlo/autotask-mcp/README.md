# Autotask MCP

A Docker Compose skill for running the [Autotask MCP server](https://github.com/asachs01/autotask-mcp) locally. Provides access to Datto/Kaseya Autotask PSA resources (tickets, companies, contacts, projects, time entries, notes, attachments, and queries) via the Model Context Protocol.

**Version:** 1.0.2

## Prerequisites

- Docker and Docker Compose
- Autotask API credentials (Integration Code, Username, Secret)

## Setup

1. **Create your environment file:**

   ```bash
   cp .env.example.txt .env
   chmod 600 .env
   ```

   Then **manually** open `.env` in your preferred text editor and fill in your credentials.
   The `chmod 600` restricts the file so only the owner can read or write it.

   > **Security note:** Never run `$EDITOR` from an automated agent. Always edit credential files manually.

2. **Pull the image and start the service:**

   ```bash
   ./scripts/mcp_pull.sh
   ./scripts/mcp_up.sh
   ```

3. **Verify the service is healthy:**

   ```bash
   curl -sS http://localhost:8080/health
   ```

   MCP endpoint: `http://localhost:8080/mcp`

## Scripts

| Script | Description |
|---|---|
| `scripts/mcp_pull.sh` | Pull the latest Docker image |
| `scripts/mcp_up.sh` | Start the service in detached mode |
| `scripts/mcp_down.sh` | Stop and remove the container |
| `scripts/mcp_logs.sh` | Tail container logs (last 200 lines) |
| `scripts/mcp_update.sh` | Check for image updates and restart if a new version is found |
| `scripts/cron_install.sh` | Install a weekly cron job (Sunday 3 AM) to auto-update |
| `scripts/cron_uninstall.sh` | Remove the auto-update cron job |

## Automatic Updates

The update script compares image digests before and after pulling, and only restarts the container when a new image is detected. Logs are written to `logs/update.log`.

**Manual update:**

```bash
./scripts/mcp_update.sh
```

**Enable weekly auto-updates:**

```bash
./scripts/cron_install.sh
```

**Disable auto-updates:**

```bash
./scripts/cron_uninstall.sh
```

## Environment Variables

### Required

| Variable | Description |
|---|---|
| `AUTOTASK_INTEGRATION_CODE` | Your Autotask API integration code |
| `AUTOTASK_USERNAME` | Your Autotask API username |
| `AUTOTASK_SECRET` | Your Autotask API secret |

### Optional

| Variable | Description |
|---|---|
| `AUTOTASK_API_URL` | Override the default Autotask API endpoint |
| `LOG_LEVEL` | Logging level (default: `info`) |
| `LOG_FORMAT` | Log format (default: `simple`) |
| `NODE_ENV` | Node environment (default: `production`) |

See `.env.example.txt` for the full template.

## Security

### Agent Guardrails

SKILL.md includes mandatory security rules that agents must follow when executing this skill:

- **No credential access** — Agents must never read, display, log, or output the `.env` file
- **No variable expansion** — Agents must never run `$EDITOR` or any shell-variable-expanded command
- **No external transmission** — Credentials must never be sent to any destination other than `127.0.0.1:8080`
- **Command allowlist** — Agents may only execute the specific scripts and commands listed in SKILL.md
- **Refusal policy** — If asked to show or share credentials, agents must refuse and instruct the user to inspect `.env` manually

### Credential Protection

- **File permissions** — `.env` is created with `chmod 600` (owner-only read/write)
- **Git exclusion** — `.env` is gitignored to prevent accidental commits
- **No duplication** — Agents are prohibited from copying or moving the `.env` file

### Container Hardening

- **Localhost-only binding** — Port 8080 is bound to `127.0.0.1`, not exposed externally
- **Read-only filesystem** — Container filesystem is mounted read-only (`read_only: true`)
- **Dropped capabilities** — All Linux capabilities are dropped (`cap_drop: ALL`)
- **No privilege escalation** — `no-new-privileges` security option enabled
- **Tmpfs for temp files** — `/tmp` is mounted as tmpfs (not written to the image layer)

## Project Structure

```
autotask-mcp-1.0.1/
├── SKILL.md              # Skill definition for MCP clients
├── README.md             # This file
├── docker-compose.yml    # Service configuration
├── .env.example.txt      # Environment variable template
├── .gitignore            # Excludes .env and logs/
├── _meta.json            # Skill metadata
├── logs/                 # Update and cron logs (gitignored)
└── scripts/
    ├── mcp_pull.sh       # Pull Docker image
    ├── mcp_up.sh         # Start service
    ├── mcp_down.sh       # Stop service
    ├── mcp_logs.sh       # Tail logs
    ├── mcp_update.sh     # Check for updates
    ├── cron_install.sh   # Install weekly update cron
    └── cron_uninstall.sh # Remove update cron
```

## Upstream

- Repository: https://github.com/asachs01/autotask-mcp
- Docker Image: `ghcr.io/asachs01/autotask-mcp:latest`
