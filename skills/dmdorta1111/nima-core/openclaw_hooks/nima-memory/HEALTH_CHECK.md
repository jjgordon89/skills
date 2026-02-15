# NIMA Memory Health Check

## Overview

NIMA Memory now includes comprehensive health checking to verify database connectivity, monitor storage health, and provide statistics on memory capture.

## Automatic Health Check on Startup

By default, NIMA Memory runs a health check 1 second after gateway startup. This verifies:

✅ Database file exists  
✅ Required tables are present  
✅ Database is readable  
✅ Statistics are accessible

**Example startup logs:**
```
[nima-memory] ✅ Health check passed
[nima-memory] Database: 9,770 nodes, 5,802 turns, 91MB
[nima-memory] Recent activity: 421 memories in last 24h
```

**If health check fails:**
```
[nima-memory] ⚠️ Health check failed: Database file not found
[nima-memory] Database path: /Users/lilu/.nima/memory/graph.sqlite
```

### Disable Automatic Health Check

Add to your plugin config:

```json
{
  "plugins": {
    "entries": {
      "nima-memory": {
        "database": {
          "health_check_on_startup": false
        }
      }
    }
  }
}
```

## Manual Health Check (CLI)

Use the included CLI tool for detailed diagnostics:

### Basic Check

```bash
python3 /path/to/nima-core/openclaw_hooks/nima-memory/health_check.py
```

**Output:**
```
✅ NIMA Memory Health Check: PASSED

📊 Database Stats:
  Location: /Users/lilu/.nima/memory/graph.sqlite
  Size: 91 MB
  Nodes: 9,770
  Turns: 5,802
  Recent (24h): 421

📁 Layer Distribution:
  contemplation         3,364 ( 34.4%)
  input                 3,082 ( 31.5%)
  output                1,859 ( 19.0%)
  legacy_vsa            1,465 ( 15.0%)

⏰ Timeline:
  First memory: 2026-01-31 17:58
  Last memory:  2026-02-15 15:32

🔍 Features:
  FTS search: ✅ Enabled
```

### Verbose Check

```bash
python3 health_check.py --verbose
```

**Adds:**
- Top 5 contributors (who sent the most messages)
- Average Free Energy score

**Example:**
```
👥 Top Contributors:
  David Dorta          1,234 memories
  Melissa Dorta          456 memories
  unknown                321 memories

🧠 Average Free Energy: 0.478
```

### JSON Output

```bash
python3 health_check.py --json
```

**Output:**
```json
{
  "ok": true,
  "stats": {
    "nodes": 9770,
    "turns": 5802,
    "layers": {
      "contemplation": 3364,
      "input": 3082,
      "output": 1859,
      "legacy_vsa": 1465
    },
    "recent_24h": 421,
    "db_size_bytes": 95375360,
    "db_size_mb": 90.98,
    "tables": [
      "memory_nodes",
      "memory_edges",
      "memory_turns",
      "memory_fts"
    ],
    "fts_enabled": true,
    "first_memory": "2026-01-31 17:58",
    "last_memory": "2026-02-15 15:32"
  }
}
```

### Custom Database Path

```bash
python3 health_check.py --db /path/to/custom/graph.sqlite
```

## Programmatic Health Check (API)

Call the health check from other plugins or scripts:

### JavaScript (from plugin)

```javascript
const health = api.call("nima-memory.healthCheck");

if (health.ok) {
  console.log(`Database has ${health.stats.nodes} nodes`);
} else {
  console.error(`Health check failed: ${health.error}`);
}
```

### Python (direct)

```python
from health_check import health_check

result = health_check()

if result["ok"]:
    print(f"✅ Database healthy: {result['stats']['nodes']} nodes")
else:
    print(f"❌ Health check failed: {result['error']}")
```

## Health Check Metrics

| Metric | Description |
|--------|-------------|
| `nodes` | Total memory nodes (all layers) |
| `turns` | Complete conversational turns (3 layers each) |
| `recent_24h` | Memories captured in last 24 hours |
| `db_size_mb` | Database file size in megabytes |
| `layers` | Distribution of nodes by layer type |
| `fts_enabled` | Whether FTS search is available |
| `first_memory` | Timestamp of oldest memory |
| `last_memory` | Timestamp of newest memory |

**Verbose only:**
| Metric | Description |
|--------|-------------|
| `top_contributors` | Users with most input memories |
| `avg_fe_score` | Average Free Energy score (0.0-1.0) |

## Troubleshooting

### Database Not Found

**Symptom:**
```
❌ NIMA Memory Health Check: FAILED
Error: Database file not found
Path: /Users/lilu/.nima/memory/graph.sqlite
```

**Solution:**
1. Check if NIMA Memory has been initialized (send at least one message)
2. Verify `~/.nima/memory/` directory exists
3. Check file permissions

### Tables Missing

**Symptom:**
```
Error: memory_nodes table missing
```

**Solution:**
1. Database was corrupted or manually modified
2. Delete database and let it reinitialize:
   ```bash
   rm ~/.nima/memory/graph.sqlite
   openclaw gateway restart
   ```

### Timeout

**Symptom:**
```
Error: database is locked
```

**Solution:**
1. Another process is accessing the database (e.g., migration in progress)
2. Wait 10 seconds and retry
3. If persistent, check for stuck Python processes:
   ```bash
   ps aux | grep lazy_recall
   ```

### Low Recent Activity

**Symptom:**
```
Recent (24h): 0
```

**Meaning:** No memories captured in last 24 hours.

**Possible causes:**
- FE threshold too high (increase noise, decrease signal)
- System has been inactive
- Heartbeat/system messages being filtered (expected)

**Check:**
```bash
python3 health_check.py --verbose
```

Look at `avg_fe_score`. If it's > 0.4, you might be filtering too aggressively.

## Integration with Monitoring

### Cron Health Check

Run periodic health checks and alert on failure:

```bash
#!/bin/bash
# Daily health check at 3 AM

HEALTH=$(python3 /path/to/health_check.py --json)

if echo "$HEALTH" | jq -e '.ok == false' > /dev/null; then
  ERROR=$(echo "$HEALTH" | jq -r '.error')
  echo "NIMA Memory health check failed: $ERROR" | mail -s "NIMA Alert" admin@example.com
fi
```

### Prometheus Metrics

Export health metrics to Prometheus:

```python
from health_check import health_check

result = health_check()

if result["ok"]:
    stats = result["stats"]
    print(f"nima_memory_nodes {stats['nodes']}")
    print(f"nima_memory_turns {stats['turns']}")
    print(f"nima_memory_recent_24h {stats['recent_24h']}")
    print(f"nima_memory_size_bytes {stats['db_size_bytes']}")
```

## Version History

- **1.0.2** (2026-02-15) — Added health check system
- **1.0.1** (2026-02-15) — Added configuration system
- **1.0.0** (2026-02-13) — Initial release
