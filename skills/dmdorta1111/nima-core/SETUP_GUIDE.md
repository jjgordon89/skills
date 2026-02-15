# NIMA Setup Guide

Complete step-by-step guide to set up NIMA (Neural Integrated Memory Architecture).

## Prerequisites

- Python 3.11+
- Node.js 18+ (for OpenClaw hooks)
- OpenClaw Gateway installed

## Quick Start (5 minutes)

```bash
# 1. Clone nima-core
git clone https://github.com/your-org/nima-core.git
cd nima-core

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install OpenClaw hooks
cp -r openclaw_hooks/* ~/.openclaw/extensions/

# 4. Configure environment
export NIMA_EMBEDDER=voyage
export VOYAGE_API_KEY=your-api-key

# 5. Initialize database
python -c "from nima_core import NIMA; NIMA().init()"

# 6. Restart OpenClaw
openclaw restart
```

## Detailed Setup

### Step 1: Install Dependencies

**Python packages:**
```bash
pip install numpy pandas sqlite3
pip install real-ladybug  # Optional, for LadybugDB
pip install sentence-transformers  # Optional, for local embeddings
```

**Node.js packages** (handled automatically by OpenClaw):
- None required (hooks use Node.js built-ins)

### Step 2: Choose Database

**Option A: SQLite (Default)**
- No additional setup required
- Database created automatically at `~/.nima/memory/graph.sqlite`

**Option B: LadybugDB (Recommended for production)**
```bash
pip install real-ladybug
python scripts/ladybug_parallel.py --migrate
```

See [DATABASE_OPTIONS.md](./docs/DATABASE_OPTIONS.md) for details.

### Step 3: Choose Embedding Provider

**Option A: Voyage (Recommended)**
```bash
export NIMA_EMBEDDER=voyage
export VOYAGE_API_KEY=pa-xxx...
```

**Option B: OpenAI**
```bash
export NIMA_EMBEDDER=openai
export OPENAI_API_KEY=sk-xxx...
```

**Option C: Local (Free)**
```bash
export NIMA_EMBEDDER=local
pip install sentence-transformers
```

See [EMBEDDING_PROVIDERS.md](./docs/EMBEDDING_PROVIDERS.md) for details.

### Step 4: Install Hooks

**Copy hooks to OpenClaw extensions:**
```bash
# Memory capture hook
cp -r openclaw_hooks/nima-memory ~/.openclaw/extensions/

# Memory recall hook
cp -r openclaw_hooks/nima-recall-live ~/.openclaw/extensions/

# Affect system hook (optional)
cp -r openclaw_hooks/nima-affect ~/.openclaw/extensions/
```

**Or use the install script:**
```bash
./install.sh
```

### Step 5: Configure OpenClaw

Add to `~/.openclaw/openclaw.json`:

```json
{
  "plugins": {
    "slots": {
      "memory": "nima-memory"
    }
  },
  "hooks": {
    "nima-recall": {
      "enabled": true,
      "priority": 15
    }
  }
}
```

### Step 6: Initialize Database

```bash
# Create database directory
mkdir -p ~/.nima/memory

# Initialize tables
python -c "
from nima_core.db import init_db
init_db()
"

# Build embedding index (for SQLite)
python openclaw_hooks/nima-recall-live/build_embedding_index.py
```

### Step 7: Verify Installation

```bash
# Check database
python -c "
from nima_core.db import get_stats
print(get_stats())
"

# Test recall
python scripts/quick_recall.py 'test query' --top 3

# Run benchmarks
python scripts/ladybug_parallel.py --benchmark
```

### Step 8: Restart OpenClaw

```bash
openclaw restart
```

## Hook Configuration

### nima-memory (Capture)

Captures memories during conversations.

**Config:**
```json
{
  "capture": {
    "enabled": true,
    "min_text_length": 10,
    "layers": ["input", "contemplation", "output"],
    "who_mapping": {
      "user": ["David Dorta", "Melissa Dorta"],
      "self": ["Lilu", "assistant"]
    }
  }
}
```

### nima-recall-live (Recall)

Injects relevant memories before each response.

**Config:**
```json
{
  "recall": {
    "enabled": true,
    "max_results": 7,
    "token_budget": 500,
    "compressed_format": true,
    "use_ladybug": true,
    "cooldown_ms": 10000
  }
}
```

### nima-affect (Emotional State)

Tracks emotional state across conversations.

**Config:**
```json
{
  "affect": {
    "enabled": true,
    "affects": ["SEEKING", "RAGE", "FEAR", "LUST", "CARE", "PANIC", "PLAY"],
    "decay_rate": 0.05
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NIMA_EMBEDDER` | Embedding provider | `voyage` |
| `NIMA_DB_PATH` | Database path | `~/.nima/memory` |
| `NIMA_DEBUG` | Enable debug logging | `false` |
| `VOYAGE_API_KEY` | Voyage API key | (required for Voyage) |
| `OPENAI_API_KEY` | OpenAI API key | (required for OpenAI) |

## Directory Structure

```
~/.nima/
├── memory/
│   ├── graph.sqlite      # SQLite database
│   ├── ladybug.lbug      # LadybugDB database (if used)
│   ├── embedding_index.npy   # Pre-computed embeddings
│   └── embedding_index_meta.json
├── affect/
│   └── affect_state_agent.json
└── config.json           # NIMA configuration
```

## Troubleshooting

### "No memories found"

1. Check if database exists:
   ```bash
   ls -la ~/.nima/memory/
   ```

2. Check if memories were captured:
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('~/.nima/memory/graph.sqlite')
   print(conn.execute('SELECT COUNT(*) FROM memory_nodes').fetchone())
   "
   ```

3. Check hooks are enabled in `openclaw.json`

### "Embedding index not found"

Build the index:
```bash
python openclaw_hooks/nima-recall-live/build_embedding_index.py
```

### "Recall not working"

1. Check gateway logs:
   ```bash
   tail -f ~/.openclaw/logs/gateway.log | grep nima
   ```

2. Verify hook priority:
   ```json
   {"priority": 15}  // After affect system (10)
   ```

### "LadybugDB not working"

1. Install package:
   ```bash
   pip install real-ladybug
   ```

2. Check migration:
   ```bash
   python scripts/ladybug_parallel.py --benchmark
   ```

3. Enable in config:
   ```javascript
   const USE_LADYBUG = true;
   ```

## Next Steps

- [Migration Guide](./MIGRATION_GUIDE.md) - Migrating from older versions
- [Database Options](./DATABASE_OPTIONS.md) - SQLite vs LadybugDB
- [Embedding Providers](./EMBEDDING_PROVIDERS.md) - Choose your embedding provider
- [Quick Reference](./QUICK_REFERENCE.md) - Common commands and APIs