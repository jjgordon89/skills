# 🧠 ClawSouls Skill for OpenClaw

An [OpenClaw](https://github.com/openclaw/openclaw) skill that lets your AI agent manage personas (Souls) — install, switch, list, and restore AI personalities.

## Installation

Add this skill to your OpenClaw workspace:

```bash
# Via ClaWHub (coming soon)
openclaw skill install clawsouls

# Or manually
git clone https://github.com/clawsouls/clawsouls-skill.git ~/.openclaw/skills/clawsouls
```

## What It Does

Once installed, your AI agent can:

- **Install souls** — Download persona packages from the registry
- **Switch personas** — Activate a different personality with automatic backup
- **List installed** — Show all available local souls
- **Restore** — Revert to your previous persona

## Example Prompts

```
"Install the minimalist soul"
"Switch my persona to devops-veteran"
"What souls do I have installed?"
"Restore my previous personality"
"Browse available personas"
```

## Available Souls

| Soul | Description |
|------|-------------|
| 🅱️ Brad | Formal, project-focused development partner |
| 🔧 DevOps Veteran | Battle-scarred infrastructure engineer |
| 🎮 GameDev Mentor | Experienced game developer and mentor |
| ⚡ Minimalist | Extremely concise responses |
| 🔍 Code Reviewer | Thorough, constructive code reviewer |
| 📚 Coding Tutor | Patient programming teacher |
| 📋 Personal Assistant | Proactive daily life assistant |
| 📝 Tech Writer | Clear technical documentation writer |
| 📊 Data Analyst | Insight-driven data analyst |
| ✍️ Storyteller | Narrative crafter and worldbuilder |

Browse all at [clawsouls.ai](https://clawsouls.ai).

## Structure

```
clawsouls-skill/
├── SKILL.md          # Skill instructions (loaded by OpenClaw)
├── scripts/
│   └── clawsouls.sh  # CLI wrapper script
├── package.json      # Dependencies (clawsouls CLI)
├── LICENSE.md        # Apache 2.0
└── README.md         # This file
```

## Links

- 🌐 [clawsouls.ai](https://clawsouls.ai) — Browse souls
- 📦 [clawsouls CLI](https://www.npmjs.com/package/clawsouls) — npm package
- 🐙 [GitHub](https://github.com/clawsouls) — Source code

## License

Apache 2.0 — see [LICENSE.md](LICENSE.md).
