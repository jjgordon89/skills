# NIMA Migration Guide

Migrate from older NIMA versions to the latest release.

## From NIMA v1.x (SQLite-only)

### Step 1: Backup

```bash
# Backup existing database
cp ~/.nima/memory/graph.sqlite ~/.nima/memory/graph.sqlite.v1.backup

# Backup config
cp ~/.nima/config.json ~/.nima/config.json.v1.backup
```

### Step 2: Update Hooks

**Remove old hooks:**
```bash
rm -rf ~/.openclaw/hooks/nima-*
rm -rf ~/.openclaw/workspace/nima-core/openclaw_hooks/nima-*
```

**Install new hooks:**
```bash
cp -r openclaw_hooks/nima-memory ~/.openclaw/extensions/
cp -r openclaw_hooks/nima-recall-live ~/.openclaw/extensions/
cp -r openclaw_hooks/nima-affect ~/.openclaw/extensions/
```

### Step 3: Update Config

**Old config** (`~/.nima/config.json`):
```json
{
  "embedder": "voyage",
  "voyage_api_key": "pa-xxx"
}
```

**New config** (environment variables):
```bash
export NIMA_EMBEDDER=voyage
export VOYAGE_API_KEY=pa-xxx
```

### Step 4: (Optional) Migrate to LadybugDB

```bash
# Install LadybugDB
pip install real-ladybug

# Run migration
python scripts/ladybug_parallel.py --migrate

# Enable in hook
# Edit ~/.openclaw/extensions/nima-recall-live/index.js
# Set: const USE_LADYBUG = true;
```

### Step 5: Rebuild Embedding Index

```bash
# For SQLite
python openclaw_hooks/nima-recall-live/build_embedding_index.py --rebuild

# For LadybugDB (automatic during migration)
```

### Step 6: Verify

```bash
# Check memory count
python -c "
import sqlite3
conn = sqlite3.connect('~/.nima/memory/graph.sqlite')
print('SQLite nodes:', conn.execute('SELECT COUNT(*) FROM memory_nodes').fetchone()[0])
"

# Check recall works
python scripts/quick_recall.py 'hello' --top 3

# Restart gateway
openclaw restart
```

## From NIMA v0.x (VSA-based)

### Step 1: Export VSA Memories

```bash
# VSA memories are stored in sparse_memory.pkl
# Export to SQLite format
python scripts/export_vsa_to_sqlite.py
```

### Step 2: Install New Version

```bash
# Remove old version
rm -rf ~/.nima/vsa

# Install new version
pip install -r requirements.txt
```

### Step 3: Import Memories

```bash
# Import VSA memories into new database
python scripts/import_vsa_memories.py --input sparse_memory.pkl
```

### Step 4: Verify

```bash
# Check imported memories
python -c "
import sqlite3
conn = sqlite3.connect('~/.nima/memory/graph.sqlite')
cursor = conn.execute(\"SELECT COUNT(*) FROM memory_nodes WHERE layer='legacy_vsa'\")
print('Legacy VSA memories:', cursor.fetchone()[0])
"
```

## From Other Memory Systems

### From Mem0

```bash
# Export Mem0 memories
mem0 export --format json > mem0_export.json

# Import to NIMA
python scripts/import_mem0.py --input mem0_export.json
```

### From LangChain Memory

```bash
# Export from LangChain
python scripts/export_langchain.py --output langchain_export.json

# Import to NIMA
python scripts/import_langchain.py --input langchain_export.json
```

## Hook Migration

### Old Hook Structure (v1.x)

```
~/.openclaw/hooks/
├── nima-capture/
│   └── index.js
├── nima-recall/
│   └── index.js
└── nima-affect/
    └── index.py
```

### New Hook Structure (v2.x)

```
~/.openclaw/extensions/
├── nima-memory/
│   ├── index.js
│   └── openclaw.plugin.json
├── nima-recall-live/
│   ├── index.js
│   ├── ladybug_recall.py
│   └── openclaw.plugin.json
└── nima-affect/
    ├── index.js
    └── openclaw.plugin.json
```

### Key Changes

1. **Hooks → Extensions**: Moved from `hooks/` to `extensions/`
2. **Plugin Manifest**: Each extension needs `openclaw.plugin.json`
3. **Event-based**: Hooks now use explicit event declarations

**Old hook registration:**
```javascript
// Old: Implicit registration
module.exports = function(api) {
  api.on('before_agent_start', handler);
};
```

**New hook registration:**
```javascript
// New: Explicit metadata
export const metadata = {
  events: ["before_agent_start", "before_compaction"],
  description: "NIMA Live Recall"
};

export default function(api, config) {
  api.on("before_agent_start", handler, { priority: 15 });
}
```

## Config Migration

### Old Config Locations

| Old Location | New Location |
|--------------|--------------|
| `~/.nima/config.json` | Environment variables |
| `~/.nima/affect/config.json` | `~/.nima/affect/affect_state_agent.json` |
| `~/.nima/hooks/*.json` | `~/.openclaw/extensions/*/openclaw.plugin.json` |

### New Environment Variables

| Variable | Old Config Key |
|----------|----------------|
| `NIMA_EMBEDDER` | `config.embedder` |
| `NIMA_DB_PATH` | `config.db_path` |
| `VOYAGE_API_KEY` | `config.voyage_api_key` |
| `OPENAI_API_KEY` | `config.openai_api_key` |

## Breaking Changes

### v1.x → v2.x

1. **Hook locations moved** - Update paths
2. **Config format changed** - Use environment variables
3. **Embedding index format** - Rebuild required
4. **Affect state format** - Auto-migrated

### v0.x → v1.x

1. **VSA removed** - Memories migrated to SQLite
2. **Capture format changed** - New schema
3. **Recall format changed** - New output format

## Verification Checklist

After migration, verify:

- [ ] Database has correct node count
- [ ] Recall returns results
- [ ] Capture creates new memories
- [ ] Affect state updates
- [ ] No errors in gateway logs

```bash
# Full verification
python scripts/verify_installation.py
```

## Rollback

If migration fails:

```bash
# Restore backup
cp ~/.nima/memory/graph.sqlite.v1.backup ~/.nima/memory/graph.sqlite

# Remove new hooks
rm -rf ~/.openclaw/extensions/nima-*

# Restore old hooks (if available)
cp -r ~/.openclaw/backups/hooks/* ~/.openclaw/hooks/

# Restart
openclaw restart
```

## Getting Help

- GitHub Issues: https://github.com/your-org/nima-core/issues
- Documentation: https://nima-core.ai/docs
- Discord: https://discord.gg/nima-core