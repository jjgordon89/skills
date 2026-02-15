# NIMA Memory Migration Guide

## Overview

NIMA Memory supports migration from SQLite to LadybugDB with intelligent batching and retry logic. This is especially important for ARM64 Raspberry Pi deployments where large migrations can fail with buffer manager exceptions.

## Quick Start

### Manual Migration

```bash
cd /path/to/nima-core/openclaw_hooks/nima-memory

# Dry run (test without modifying data)
python3 migrate_to_ladybug.py --batch-size 500 --dry-run

# Actual migration
python3 migrate_to_ladybug.py --batch-size 500
```

### Auto-Migration (on startup)

Add to your OpenClaw config:

```json
{
  "plugins": {
    "entries": {
      "nima-memory": {
        "database": {
          "backend": "ladybugdb",
          "auto_migrate": true,
          "migration_batch_size": 500
        }
      }
    }
  }
}
```

**Note:** Auto-migration runs once on gateway startup. Check logs and `~/.nima/memory/migration.log` for progress.

## Why Batching?

**The Problem:**

On ARM64 Raspberry Pi, migrating large databases (>5,000 nodes) to LadybugDB in one go can fail with:

```
Buffer manager exception: Releasing physical memory... failed with error code -1
```

**The Solution:**

Migrate in batches of 500-1,000 nodes. This:
- ✅ Prevents memory exhaustion
- ✅ Allows progress tracking
- ✅ Enables resume on failure
- ✅ Provides retry logic per batch

**Proven:**

> "ok I got ladybug db to migrate in the pi, just had to do it in batches so your thinking is correct"  
> — David Dorta, 2026-02-15

## Command-Line Options

### Basic Usage

```bash
python3 migrate_to_ladybug.py [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--batch-size SIZE` | 500 | Number of nodes per batch |
| `--dry-run` | False | Simulate migration without modifying data |
| `--start-offset N` | 0 | Resume from this offset (for interrupted runs) |
| `--auto` | False | Use config defaults (for plugin use) |

### Examples

**Test migration (dry run):**
```bash
python3 migrate_to_ladybug.py --batch-size 500 --dry-run
```

**Small batches (safer for Pi):**
```bash
python3 migrate_to_ladybug.py --batch-size 300
```

**Large batches (faster on Mac mini):**
```bash
python3 migrate_to_ladybug.py --batch-size 1000
```

**Resume interrupted migration:**
```bash
# If migration failed at offset 2500
python3 migrate_to_ladybug.py --start-offset 2500
```

## Retry Logic

Each batch is retried up to **3 times** with exponential backoff:

1. **Attempt 1:** Immediate
2. **Attempt 2:** Wait 1 second
3. **Attempt 3:** Wait 5 seconds
4. **Attempt 4:** Wait 15 seconds

If all retries fail, migration stops and you can resume from that offset.

## Migration Output

### Console Output

```
============================================================
NIMA Memory Migration: SQLite → LadybugDB
============================================================
[2026-02-15 15:35:00] [INFO] Analyzing source database...
[2026-02-15 15:35:00] [INFO] Source: 9770 nodes, 91 MB
[2026-02-15 15:35:00] [INFO] Layers: {'contemplation': 3364, 'input': 3082, 'output': 1859, 'legacy_vsa': 1465}
[2026-02-15 15:35:00] [INFO] Batch size: 500 nodes
[2026-02-15 15:35:00] [INFO] Total batches: 20
[2026-02-15 15:35:00] [INFO] Starting migration...
[2026-02-15 15:35:01] [INFO] Batch 1/20 (2.5% complete, ETA: 95s)
[2026-02-15 15:35:05] [INFO] Batch 2/20 (7.7% complete, ETA: 72s)
...
[2026-02-15 15:36:35] [INFO] Batch 20/20 (100.0% complete, ETA: 0s)
============================================================
Migration Summary
============================================================
[2026-02-15 15:36:35] [INFO] Total nodes: 9770
[2026-02-15 15:36:35] [INFO] Migrated: 9770
[2026-02-15 15:36:35] [INFO] Failed batches: 0
[2026-02-15 15:36:35] [INFO] Retries: 0
[2026-02-15 15:36:35] [INFO] Elapsed: 95.3s
[2026-02-15 15:36:35] [INFO] Avg batch time: 4.77s
[2026-02-15 15:36:35] [INFO] Success rate: 100.0%
[2026-02-15 15:36:35] [INFO] ✅ Migration completed successfully!
```

### Log File

All migration events are logged to `~/.nima/memory/migration.log`:

```
[2026-02-15 15:35:00] [INFO] Source: 9770 nodes, 91 MB
[2026-02-15 15:35:01] [INFO] Batch 1/20 (2.5% complete, ETA: 95s)
[2026-02-15 15:35:05] [WARN] Batch failed (attempt 1/3): Buffer manager exception. Retrying in 1s...
[2026-02-15 15:35:06] [INFO] Batch succeeded on retry 2
...
```

## Platform-Specific Recommendations

### Raspberry Pi (ARM64 Linux)

**Batch size:** 300-500 nodes

**Why:** Limited memory, buffer manager issues

**Example:**
```bash
python3 migrate_to_ladybug.py --batch-size 300
```

### Mac mini (ARM64 macOS)

**Batch size:** 500-1000 nodes

**Why:** More stable, better memory management

**Example:**
```bash
python3 migrate_to_ladybug.py --batch-size 1000
```

### x86_64 (Intel/AMD)

**Batch size:** 1000-2000 nodes

**Why:** Most stable platform for LadybugDB

**Example:**
```bash
python3 migrate_to_ladybug.py --batch-size 2000
```

## Troubleshooting

### Migration Fails Immediately

**Symptom:**
```
[ERROR] LadybugDB not available. Install: pip install ladybug-core
```

**Solution:**
```bash
pip3 install ladybug-core
```

### Buffer Manager Exception

**Symptom:**
```
[ERROR] Batch failed after 3 attempts: Buffer manager exception
```

**Solution:**
1. Note the offset from the error message
2. Reduce batch size
3. Resume from that offset:
```bash
python3 migrate_to_ladybug.py --batch-size 200 --start-offset 2500
```

### Slow Migration

**Symptom:**
```
[INFO] Avg batch time: 15.2s
```

**Solution:**
- This is normal on Raspberry Pi
- For 10,000 nodes at 15s/batch: ~50 minutes total
- Consider running overnight or during low-activity periods

### Interrupted Migration

**Symptom:**
```
^C (Ctrl+C pressed)
```

**Solution:**
Check the log for last completed offset:
```bash
tail ~/.nima/memory/migration.log
```

Resume:
```bash
python3 migrate_to_ladybug.py --start-offset <last_offset>
```

### Partial Migration Success

**Symptom:**
```
[WARN] Migration completed with errors
[INFO] Success rate: 87.3%
```

**Solution:**
1. Check `migration.log` for failed batches
2. Re-run migration with smaller batch size
3. Or manually investigate failed nodes

## Verification

After migration, verify the data:

```bash
# Check LadybugDB stats
python3 -c "
import ladybug
db = ladybug.connect('~/.nima/memory/graph.ladybug')
print(f'Nodes: {db.count_nodes()}')
db.close()
"

# Compare with SQLite stats
python3 health_check.py --db ~/.nima/memory/graph.sqlite
```

## Rollback

If migration fails or you want to go back to SQLite:

1. **Update config:**
```json
{
  "database": {
    "backend": "sqlite",
    "auto_migrate": false
  }
}
```

2. **Restart gateway:**
```bash
openclaw gateway restart
```

3. **Remove LadybugDB file (optional):**
```bash
rm ~/.nima/memory/graph.ladybug
```

SQLite database is never deleted during migration, so rollback is always safe.

## Performance Comparison

### SQLite vs LadybugDB (after migration)

| Metric | SQLite | LadybugDB | Improvement |
|--------|--------|-----------|-------------|
| Text search | 31ms | 9ms | **3.4x faster** |
| Database size | 91 MB | 50 MB | **44% smaller** |
| Vector search | External | Built-in | Native HNSW |
| Platform support | Universal | x86_64 > macOS ARM64 > Linux ARM64 |

## Best Practices

1. **Always dry-run first:**
   ```bash
   python3 migrate_to_ladybug.py --dry-run
   ```

2. **Start with small batches on Pi:**
   - Try 300 nodes first
   - Increase if stable

3. **Monitor the log:**
   ```bash
   tail -f ~/.nima/memory/migration.log
   ```

4. **Back up SQLite before migration:**
   ```bash
   cp ~/.nima/memory/graph.sqlite ~/.nima/memory/graph.sqlite.backup
   ```

5. **Don't delete SQLite after migration:**
   - Keep it as a rollback option
   - Only ~90 MB per database

## Integration with Config

Auto-migration is triggered when both conditions are met:

1. `database.backend = "ladybugdb"`
2. `database.auto_migrate = true`

**First startup only:**

Migration runs once on the first gateway startup after config change. Subsequent startups skip migration.

To re-run migration:
```bash
# Delete LadybugDB file
rm ~/.nima/memory/graph.ladybug

# Restart gateway (migration will run again)
openclaw gateway restart
```

## FAQ

**Q: How long does migration take?**

A: Depends on database size and platform:
- **Pi (300 nodes/batch):** ~10-20s per batch
- **Mac mini (500 nodes/batch):** ~5-10s per batch
- **For 10,000 nodes:** 15-50 minutes

**Q: Can I use NIMA during migration?**

A: Yes, but:
- New memories will only go to SQLite
- After migration, restart gateway to use LadybugDB
- Recommended: migrate during low-activity periods

**Q: What if migration fails halfway?**

A: Resume from the last successful offset:
```bash
python3 migrate_to_ladybug.py --start-offset <offset>
```

**Q: Does migration affect SQLite?**

A: No. SQLite is read-only during migration and never deleted.

**Q: Can I migrate multiple times?**

A: Yes, but it will duplicate data. Delete the LadybugDB file first if you want to re-migrate.

## Version History

- **1.0.2** (2026-02-15) — Batch migration with retry logic added
- **1.0.1** (2026-02-15) — Configuration system
- **1.0.0** (2026-02-13) — Initial release (SQLite only)
