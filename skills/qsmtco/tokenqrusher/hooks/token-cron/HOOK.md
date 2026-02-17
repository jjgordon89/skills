---
name: token-cron
description: "Runs periodic optimization on gateway startup"
homepage: https://github.com/qsmtco/tokenQrusher
metadata: 
  openclaw: 
    emoji: "⏰"
    events: ["gateway:startup"]
---

# Token Cron Hook

Executes scheduled optimization tasks when OpenClaw gateway starts.

## What It Does

1. Listens for `gateway:startup` event
2. Runs optimization analysis
3. Checks budget status
4. Logs recommendations

## Scheduled Tasks

- **Optimization**: Analyzes usage patterns, suggests improvements
- **Budget Check**: Reports current budget status

## Configuration

```json
{
  "enabled": true,
  "runOnStartup": true,
  "optimizeOnStartup": true,
  "checkBudgetOnStartup": true
}
```

## Scripts

This hook invokes:
- `scripts/cron-optimizer/optimizer.py` - Main optimization
- `scripts/usage/cli.py` - Budget check

## Events

Listens to: `gateway:startup`
