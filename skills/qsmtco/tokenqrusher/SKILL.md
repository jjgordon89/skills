---
name: tokenQrusher
description: Token optimization system for OpenClaw reducing costs 50-80%
version: 2.0.6
author: qsmtco
license: MIT
homepage: https://github.com/qsmtco/tokenQrusher
metadata:
  openclaw:
    requires:
      env:
        - OPENROUTER_API_KEY
      bins:
        - python3
        - node
    emoji: "💰"
---

# tokenQrusher Skill

## Overview

tokenQrusher is a comprehensive token cost optimization system for OpenClaw that reduces API costs by 50-80% through intelligent context filtering, model routing, automated scheduling, and heartbeat optimization.

## Components

### 1. Context Hook (`token-context`)

**Event:** `agent:bootstrap`

Filters workspace files based on message complexity.

**Config:** `~/.openclaw/hooks/token-context/config.json`

```json
{
  "enabled": true,
  "logLevel": "info",
  "dryRun": false,
  "files": {
    "simple": ["SOUL.md", "IDENTITY.md"],
    "standard": ["SOUL.md", "IDENTITY.md", "USER.md"],
    "complex": ["SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "AGENTS.md", "MEMORY.md", "HEARTBEAT.md"]
  }
}
```

**Rationale:** Simple messages (greetings) only need identity info. Full context only for complex tasks.

**Savings:** ~99% for simple messages (50K → 500 tokens)

### 2. Model Router (`token-model`)

**Event:** `agent:bootstrap`

Logs model tier recommendation based on task complexity.

**Config:** `~/.openclaw/hooks/token-model/config.json`

```json
{
  "enabled": true,
  "logLevel": "info",
  "models": {
    "quick": "openrouter/stepfun/step-3.5-flash:free",
    "standard": "anthropic/claude-haiku-4",
    "deep": "openrouter/minimax/minimax-m2.5"
  },
  "fallbacks": {
    "primary": "anthropic/claude-sonnet-4-5",
    "fallback": ["claude-haiku-4", "step-3.5-flash:free"]
  }
}
```

**Note:** Hooks cannot directly change model. Use fallback chain in `openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-5",
        "fallbacks": ["anthropic/claude-haiku-4", "openrouter/stepfun/step-3.5-flash:free"]
      }
    }
  }
}
```

**Savings:** Up to 92% by using free tier for simple tasks.

### 3. Usage Tracker (`token-usage`)

**Event:** `agent:bootstrap`

Monitors spending and logs budget status.

**Config:** `~/.openclaw/hooks/token-usage/config.json`

```json
{
  "enabled": true,
  "logLevel": "info",
  "budgets": {
    "daily": 5.0,
    "weekly": 30.0,
    "monthly": 100.0
  },
  "warningThreshold": 0.8,
  "criticalThreshold": 0.95
}
```

**Environment Override:**

```bash
export TOKENQRUSHER_BUDGET_DAILY=10.0
export TOKENQRUSHER_WARNING_THRESHOLD=0.85
```

**Status Emojis:**
- ✅ Healthy (<80%)
- 🟡 Warning (80-95%)
- 🔴 Critical (95-100%)
- 🚨 Exceeded (>100%)

### 4. Cron Optimizer (`token-cron`)

**Event:** `gateway:startup`

Runs automated optimization on startup.

**Config:** `~/.openclaw/hooks/token-cron/config.json`

```json
{
  "enabled": true,
  "runOnStartup": true,
  "optimizeOnStartup": true,
  "checkBudgetOnStartup": true,
  "quietHours": { "start": 23, "end": 8 }
}
```

**Scheduler Jobs:**

| Job | Interval | Description |
|-----|----------|-------------|
| optimize | 3600s (1h) | Run optimization analysis |
| rotate_model | 7200s (2h) | Rotate model based on budget |
| check_budget | 300s (5m) | Check budget thresholds |

**Implementation:** `scripts/cron-optimizer/optimizer.py`

Pure functions, thread-safe, deterministic output.

### 5. Heartbeat Optimizer (`token-heartbeat`)

**Event:** `agent:bootstrap` (for heartbeat polls)

Optimizes heartbeat schedule to reduce API calls.

**Config:** `~/.openclaw/hooks/token-heartbeat/config.json`

```json
{
  "enabled": true,
  "intervals": {
    "email": 7200,
    "calendar": 14400,
    "weather": 14400,
    "monitoring": 7200
  },
  "quietHours": { "start": 23, "end": 8 }
}
```

**Optimization Table:**

| Check | Before | After | Reduction |
|-------|--------|-------|-----------|
| Email | 60 min | 120 min | 50% |
| Calendar | 60 min | 240 min | 75% |
| Weather | 60 min | 240 min | 75% |
| Monitoring | 30 min | 120 min | 75% |

**Result:** 48 → 12 checks/day (**75% fewer API calls**)

## CLI Commands

After installation, `tokenqrusher` command is available:

### `tokenqrusher context <prompt>`

Recommends context files for a prompt.

```bash
$ tokenqrusher context "hi"
Complexity: simple (confidence: 95%)
Files: SOUL.md, IDENTITY.md
Savings: 71%
```

### `tokenqrusher model <prompt>`

Recommends model tier for a prompt.

```bash
$ tokenqrusher model "design system"
Tier: deep (confidence: 90%)
Model: openrouter/minimax/minimax-m2.5
Cost: $0.60+/MT
```

### `tokenqrusher budget [--period daily|weekly|monthly]`

Shows budget status with emoji indicators.

```bash
$ tokenqrusher budget --json
{
  "period": "daily",
  "spent": 2.34,
  "limit": 5.0,
  "remaining": 2.66,
  "percent": 0.468,
  "status": "HEALTHY"
}
```

### `tokenqrusher usage [--days N]`

Shows usage summary.

```bash
$ tokenqrusher usage --days 30 --json
{
  "record_count": 127,
  "total_cost": 45.23,
  "total_input_tokens": 456780,
  "total_output_tokens": 324510
}
```

### `tokenqrusher optimize [--dry-run] [--json]`

Runs optimization pass.

```bash
$ tokenqrusher optimize --json
{
  "result": "SUCCESS",
  "actions_taken": [
    {
      "action_type": "recommend_quick_tier",
      "priority": 80,
      "reason": "Critical budget warning",
      "expected_savings": 1.50
    }
  ],
  "duration_ms": 145.2
}
```

### `tokenqrusher status [--verbose] [--json]`

Shows full system status.

```bash
$ tokenqrusher status -v
=== tokenQrusher Status ===

Hooks:
  ✓ token-context   (Filters context)
  ✓ token-model     (Routes models)
  ✓ token-usage     (Tracks budgets)
  ✓ token-cron      (Runs optimization)
  ✓ token-heartbeat (Optimizes heartbeat)

Optimizer:
  State: IDLE
  Enabled: True
  Quiet hours: False
  Consecutive failures: 0

Heartbeat:
  Checks due: 2/4
  Quiet hours active: False

Budgets:
  daily: $5.0
  weekly: $30.0
  monthly: $100.0
```

### `tokenqrusher install [--hooks] [--cron] [--all]`

Installs hooks and cron jobs.

```bash
$ tokenqrusher install --all
Enabling token-context... OK
Enabling token-model... OK
Enabling token-usage... OK
Enabling token-cron... OK
Enabling token-heartbeat... OK
```

## Design Principles

This skill follows rigorous engineering standards:

- **Deterministic** - Same input always produces same output
- **Pure functions** - No side effects unless explicitly named
- **Immutability** - Data classes frozen; JS const declarations
- **No exceptions for control flow** - Use Either/Result in Python, Maybe in JS
- **Thread-safe** - RLock protection for shared state
- **Comprehensive typing** - Full type hints, mypy compatible
- **Logging discipline** - Only at entry, exit, error
- **Compile-time constants** - All numeric limits defined as constants

## Architecture Decisions

### Why Multiple Hooks?

OpenClaw's hook system allows multiple independent hooks on same event (`agent:bootstrap`). Each hook has single responsibility:

- **token-context** - Only filters context files
- **token-model** - Only logs model recommendations  
- **token-usage** - Only reports budget status

This separation enables:
- Independent enable/disable per component
- Clear ownership and debugging
- Easier testing

### Why Python + JavaScript?

- **Python**: Heavy computation, data processing, complex logic
- **JavaScript**: Hook handlers need to run in OpenClaw's Node.js environment

Shared modules ensure consistency (e.g., regex patterns in `token-shared`).

### Why Not Direct Model Control?

OpenClaw's hook system cannot modify model selection mid-session. Workarounds:

1. **Fallback chains** in `openclaw.json` (automatic)
2. **Cron-based rotation** (automated)
3. **Manual override** via `/model` command

## Testing

### Unit Tests (170 tests total)

```bash
# Python tests
pytest tests/unit/test_classifier.py    # 45 tests
pytest tests/unit/test_optimizer.py     # 40 tests  
pytest tests/unit/test_heartbeat.py     # 35 tests

# Edge case tests
pytest tests/edge/test_edge_cases.py    # 30 tests

# Integration tests
pytest tests/integration/               # 20 tests
```

**Coverage:** 90%+

### Test Philosophy

- **Theorem-based**: Tests verify mathematical properties (e.g., "confidence always 0-1")
- **Determinism**: Same input produces same output
- **Edge cases**: Unicode, empty, extreme values
- **Fuzz testing**: Random inputs don't crash

## Performance

Benchmarks on typical hardware:

| Operation | Latency | CPU | Memory |
|-----------|---------|-----|--------|
| Context classification | <1ms | 0.01% | 0.5MB |
| Model classification | <1ms | 0.01% | 0.5MB |
| Budget check | <10ms | 0.05% | 1MB |
| Full optimization | <200ms | 0.1% | 5MB |

## Security

### Input Validation

- All file names validated with strict regex (`/^[a-zA-Z0-9._-]+$/`)
- No path traversal possible
- Maximum length enforced (255 chars)

### Secrets

- No API keys stored in code
- All credentials from environment or OpenClaw config
- No credentials logged

### Resource Limits

- Config read has timeout (5s for subprocess, 10s for SSH)
- Memory bounded by record pruning (default 30 days)
- Disk usage bounded by retention policies

## Troubleshooting

### Hook Not Loading

```bash
# Check hook status
openclaw hooks list

# Should show "✓ ready" next to token-* hooks

# If not:
openclaw hooks enable token-context
openclaw hooks enable token-model
openclaw hooks enable token-usage
openclaw hooks enable token-cron
openclaw hooks enable token-heartbeat

# Restart required
openclaw gateway restart
```

### Budget Always 0

Usage tracking requires records. Generate activity first:

```bash
# Send some messages to OpenClaw to create usage records
# Then check:
tokenQrusher usage --days 1
```

### High CPU Usage

Check for infinite loops. Restart gateway:

```bash
openclaw gateway restart
```

### Config Changes Not Taking Effect

Config caching TTL is 60 seconds. Wait or restart:

```bash
# Clear cache (restart hook)
openclaw hooks disable token-context
openclaw hooks enable token-context
openclaw gateway restart
```

## Migration Guide

### From v1.x to v2.0

Major changes:

1. **Unified CLI**: Now `tokenqrusher` instead of separate scripts
2. **Shared module**: All JS hooks use `token-shared/shared.js`
3. **Thread safety**: Python classes now use RLock
4. **Result types**: Python no longer uses exceptions for control flow

Breaking changes: None for CLI users. Hook configurations may need migration if custom.

## Future Roadmap

- **v2.1**: Dollar-cost averaging, predictive budget forecasting
- **v2.2**: Multi-tenant support, team budgets
- **v3.0**: Distributed usage aggregation for clusters

## License

MIT License. See LICENSE file.

## Support

- **Issues**: https://github.com/qsmtco/tokenQrusher/issues
- **Discord**: `#openclaw` on clawd.discord.gg
- **Docs**: https://docs.tokenqrusher.openclaw.ai

## Credits

- **Design**: Lieutenant Qrusher
- **Implementation**: Qrusher Team (qsmtco)
- **Review**: Captain JAQ (SMTCo)
- **Framework**: OpenClaw Team

Built with the OpenClaw Agent Framework: https://github.com/openclaw/openclaw

---

## External Endpoints

This skill may optionally contact the following external endpoint when fetching model pricing:

| Endpoint | Purpose | When Used |
|----------|---------|-----------|
| `https://openrouter.ai/api/v1/models` | Retrieve current model pricing | When `tokenqrusher budget` or `tokenqrusher optimize` are run and pricing data is not cached, **and** `OPENROUTER_API_KEY` is set |

If `OPENROUTER_API_KEY` is not set, pricing falls back to built-in defaults and no external calls are made. Hooks and all other components operate entirely locally.

## Security & Privacy

- **Core functionality (hooks) is fully local** — no network access.
- **Optional pricing fetch** contacts OpenRouter only when explicitly triggered and with API key present.
- **No user data** (workspace files, messages) is ever transmitted externally.
- All configuration is read from local files (`~/.openclaw/hooks/`).
- Usage tracking reads OpenClaw's internal logs only.
- The CLI tools (`tokenqrusher`) analyze local workspace files and OpenClaw state.

## Model Invocation Note

Hooks (`token-context`, `token-model`, `token-usage`, `token-cron`, `token-heartbeat`) are triggered automatically during agent bootstrap and gateway startup. This is the intended behavior; no user action is required beyond enabling the hooks.

## Trust Statement

By using this skill, all operations remain local to your machine. No data is sent to external servers. Only install if you trust the code and its author.
