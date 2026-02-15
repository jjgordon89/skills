# NIMA Memory Configuration

## Overview

NIMA Memory now supports comprehensive configuration for tuning memory capture, filtering, and storage without code changes.

## Configuration Example

Add to your OpenClaw config (`~/.openclaw/openclaw.json`):

```json
{
  "plugins": {
    "entries": {
      "nima-memory": {
        "enabled": true,
        "identity_name": "agent",
        "skip_subagents": true,
        "skip_heartbeats": true,
        "content_limits": {
          "max_text_length": 3000,
          "max_summary_length": 300,
          "max_summary_input": 80,
          "max_thinking_summary": 120,
          "max_output_summary": 100
        },
        "free_energy": {
          "min_threshold": 0.2,
          "affect_variance_weight": 0.3,
          "thinking_boost": 0.1,
          "routine_penalty": 0.2,
          "monotonous_penalty": 0.4
        },
        "noise_filtering": {
          "filter_heartbeat_mechanics": true,
          "filter_system_noise": true,
          "filter_empty_exchanges": true,
          "min_exchange_length": 5
        },
        "database": {
          "backend": "sqlite",
          "auto_migrate": false,
          "migration_batch_size": 500,
          "health_check_on_startup": true
        }
      }
    }
  }
}
```

## Configuration Options

### Basic Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable the plugin |
| `identity_name` | string | `"agent"` | Identity name for affect state lookup |
| `skip_subagents` | boolean | `true` | Don't capture memories from subagent sessions |
| `skip_heartbeats` | boolean | `true` | Don't capture memories from heartbeat sessions |

### Content Limits

Prevent memory bloat and protect against oversized content.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_text_length` | number | `3000` | Maximum characters for raw text (security limit) |
| `max_summary_length` | number | `300` | Maximum characters for any summary |
| `max_summary_input` | number | `80` | Maximum characters for input summary (~10-20 tokens) |
| `max_thinking_summary` | number | `120` | Maximum characters for contemplation summary |
| `max_output_summary` | number | `100` | Maximum characters for output summary |

### Free Energy Scoring

Control how "novel" a memory must be to get stored. Lower thresholds = more memories, higher = only significant events.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `min_threshold` | number | `0.2` | Minimum FE score to store (0.0-1.0). Below this = filtered as noise |
| `affect_variance_weight` | number | `0.3` | Weight for affect variance in FE calculation |
| `thinking_boost` | number | `0.1` | FE boost when agent has significant contemplation (>100 chars) |
| `routine_penalty` | number | `0.2` | FE penalty for short/routine exchanges |
| `monotonous_penalty` | number | `0.4` | FE penalty for monotonous patterns (HEARTBEAT_OK, "ok", "yes") |

**Tuning Tips:**

- **Storage bloat?** Increase `min_threshold` to 0.3-0.4 (only memorable events)
- **Missing important memories?** Decrease to 0.1 (capture more)
- **Too many system messages?** Increase `monotonous_penalty` to 0.5-0.6
- **Capturing thoughtful responses?** Increase `thinking_boost` to 0.15-0.2

### Noise Filtering

Fine-tune what gets filtered as system noise.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `filter_heartbeat_mechanics` | boolean | `true` | Filter "heartbeat check", "hygiene check", etc |
| `filter_system_noise` | boolean | `true` | Filter gateway restarts, doctor hints, JSON metadata |
| `filter_empty_exchanges` | boolean | `true` | Filter exchanges with no meaningful content |
| `min_exchange_length` | number | `5` | Minimum combined input+output length (chars) to store |

### Database Settings

Control backend and migration behavior.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backend` | string | `"sqlite"` | Database backend: `"sqlite"` or `"ladybugdb"` |
| `auto_migrate` | boolean | `false` | Auto-migrate from SQLite to LadybugDB on startup (runs once) |
| `migration_batch_size` | number | `500` | Batch size for LadybugDB migration (nodes per batch) |
| `health_check_on_startup` | boolean | `true` | Verify database connectivity on startup |

**Migration Notes:**

- **Raspberry Pi:** Use 300-500 batch size (prevents buffer manager exceptions)
- **Mac mini:** Use 500-1000 batch size (more stable)
- **x86_64:** Use 1000-2000 batch size (most stable)
- Auto-migration runs once on first startup after config change
- See `MIGRATION.md` for manual migration and troubleshooting
- SQLite is never deleted during migration (safe rollback)

## Recommended Configurations

### Conservative (Low Storage)
```json
{
  "free_energy": {
    "min_threshold": 0.35,
    "monotonous_penalty": 0.5
  },
  "noise_filtering": {
    "min_exchange_length": 10
  }
}
```

**Result:** Only stores significant, memorable exchanges. ~60-70% reduction in storage vs default.

### Balanced (Default)
```json
{
  "free_energy": {
    "min_threshold": 0.2
  }
}
```

**Result:** Filters obvious noise, keeps meaningful interactions. Good for most use cases.

### Verbose (Capture Everything)
```json
{
  "free_energy": {
    "min_threshold": 0.0
  },
  "noise_filtering": {
    "filter_heartbeat_mechanics": false,
    "filter_system_noise": false
  }
}
```

**Result:** Stores nearly everything. Useful for debugging or forensic analysis. High storage usage.

## Monitoring

After config changes, restart OpenClaw and check logs:

```bash
openclaw gateway restart
tail -f ~/.openclaw/logs/openclaw.log | grep nima-memory
```

Look for:
- `[nima-memory] Skipping low-FE memory (fe=X.XX, threshold=X.XX)` — FE filtering working
- `[nima-memory] Stored turn: user → thinking → response (affect: X)` — Successful captures

## Performance Impact

| Config Change | Storage Impact | Recall Quality Impact |
|---------------|----------------|----------------------|
| Increase `min_threshold` | ⬇️ Less storage | ⬆️ Higher signal-to-noise |
| Decrease `min_threshold` | ⬆️ More storage | ⬇️ More noise in recalls |
| Increase `max_summary_input` | ➡️ Minimal | ⬆️ Better context in summaries |
| Enable `auto_migrate` to LadybugDB | ⬇️ 44% smaller | ➡️ Same (if working) |

## Troubleshooting

**Problem:** Too many memories being stored

**Solution:** Increase `free_energy.min_threshold` to 0.3 or higher

---

**Problem:** Important conversations not being captured

**Solution:** 
1. Check FE scores in logs (`grep "Skipping low-FE" ~/.openclaw/logs/openclaw.log`)
2. Lower `free_energy.min_threshold` to 0.15
3. Adjust penalties if routine exchanges are important to you

---

**Problem:** LadybugDB migration fails with "Buffer manager exception"

**Solution:** 
1. Known issue on **Raspberry Pi ARM64** (works fine on macOS ARM64)
2. Set `database.backend` to `"sqlite"`
3. Set `database.auto_migrate` to `false`
4. Restart gateway
5. Report to LadybugDB team with Pi specs if you'd like to help fix it

---

## Version History

- **1.0.1** (2026-02-15) — Added comprehensive configuration system
- **1.0.0** (2026-02-13) — Initial three-layer capture release
