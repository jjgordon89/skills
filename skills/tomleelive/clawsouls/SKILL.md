---
name: clawsouls
description: Manage AI agent personas (Souls) for OpenClaw. Use when the user wants to install, switch, list, or restore AI personalities/personas. Triggers on requests like "install a soul", "switch persona", "change personality", "list souls", "restore my old soul", "use minimalist", "browse personas", or "what souls are available".
---

# ClawSouls — AI Persona Manager

Manage Soul packages that define an AI agent's personality, behavior, and identity.

## Prerequisites

Ensure `clawsouls` CLI is available:

```bash
npx clawsouls --version
```

If not installed, install globally:

```bash
npm install -g clawsouls
```

## Commands

### Install a Soul

```bash
npx clawsouls install <name>
npx clawsouls install <name> --force  # overwrite existing
```

Available souls: brad, devops-veteran, gamedev-mentor, minimalist, code-reviewer, coding-tutor, personal-assistant, tech-writer, data-analyst, storyteller.

Browse all at https://clawsouls.ai

### Activate a Soul

```bash
npx clawsouls use <name>
```

- Automatically backs up current workspace files (SOUL.md, IDENTITY.md, AGENTS.md, HEARTBEAT.md)
- Never overwrites USER.md, MEMORY.md, or TOOLS.md
- Requires session restart to take effect

### Restore Previous Soul

```bash
npx clawsouls restore
```

Reverts to the most recent backup created by `use`.

### List Installed Souls

```bash
npx clawsouls list
```

## Workflow

1. **Browse** — Check available souls at https://clawsouls.ai or suggest from the known list
2. **Install** — `npx clawsouls install <name>`
3. **Activate** — `npx clawsouls use <name>`
4. **Inform user** — Remind them to restart the OpenClaw session
5. **Restore** — If they want to go back, `npx clawsouls restore`

## Important Notes

- After `use`, always remind the user to restart their OpenClaw session
- The `use` command creates automatic backups — data loss is unlikely
- For custom registry (local testing), set env: `CLAWSOULS_CDN=/path/to/souls`
