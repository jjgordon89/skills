---
name: token-model
description: "Routes tasks to appropriate model tiers based on complexity - reduces costs by up to 92%"
homepage: https://github.com/qsmtco/tokenQrusher
metadata: 
  openclaw: 
    emoji: "🤖"
    events: ["agent:bootstrap"]
    requires: 
      config: ["workspace.dir", "agents.defaults.model"]
---

# Token Model Hook

Routes tasks to appropriate AI model tiers based on complexity analysis.

## What It Does

1. Listens for `agent:bootstrap` event
2. Analyzes the user's message
3. Logs model tier recommendation
4. Note: Cannot directly change model (OpenClaw limitation)

## Model Tiers

### Quick (Free)
- `openrouter/stepfun/step-3.5-flash:free`
- For: greetings, acknowledgments, simple queries

### Standard ($0.25/MT)
- `anthropic/claude-haiku-4`
- For: code writing, file operations, regular work

### Deep ($0.60+/MT)
- `openrouter/minimax/minimax-m2.5`
- For: architecture, complex reasoning, debugging

## How Model Selection Works

Since hooks cannot directly change the model:

1. **Fallback Chain** - Configure in openclaw.json
2. **Cron Rotation** - Use tokenQrusher cron jobs
3. **Manual Override** - Use `/model` command

## Configuration

Edit `config.json` to customize model recommendations.

## Events

Listens to: `agent:bootstrap`
