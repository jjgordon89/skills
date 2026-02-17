---
name: token-usage
description: "Tracks usage and monitors budget thresholds"
homepage: https://github.com/qsmtco/tokenQrusher
metadata: 
  openclaw: 
    emoji: "💰"
    events: ["agent:bootstrap"]
---

# Token Usage Hook

Tracks token usage and monitors budget thresholds on each agent start.

## What It Does

1. Fetches current session cost from OpenClaw
2. Calculates daily/weekly/monthly totals
3. Logs budget status with emoji indicators
4. Warns when approaching limits

## Budget Thresholds

- **80%+**: 🟡 Warning
- **95%+**: 🔴 Critical  
- **100%+**: 🚨 Exceeded

## Configuration

Edit `config.json` to customize budgets:

```json
{
  "enabled": true,
  "budgets": {
    "daily": 5.0,
    "weekly": 30.0,
    "monthly": 100.0
  },
  "warningThreshold": 0.8,
  "criticalThreshold": 0.95
}
```

## Environment Variables

- `TOKENQRUSHER_BUDGET_DAILY` - Daily budget (default: $5)
- `TOKENQRUSHER_BUDGET_WEEKLY` - Weekly budget (default: $30)
- `TOKENQRUSHER_BUDGET_MONTHLY` - Monthly budget (default: $100)
- `TOKENQRUSHER_WARNING_THRESHOLD` - Warning threshold (default: 0.8)
- `TOKENQRUSHER_CRITICAL_THRESHOLD` - Critical threshold (default: 0.95)

## Events

Listens to: `agent:bootstrap`
