# Database Options

NIMA supports multiple database backends for memory storage and retrieval.

## Quick Comparison

| Feature | SQLite | LadybugDB |
|---------|--------|-----------|
| **Type** | Relational | Graph |
| **Size** | ~91 MB | ~50 MB |
| **Text Search** | FTS5 (31ms) | CONTAINS (9ms) |
| **Vector Search** | External | Native HNSW (18ms) |
| **Graph Traversal** | JOINs (0.4ms) | Native Cypher (1.4ms) |
| **Setup** | Zero config | Install `real-ladybug` |
| **Best For** | Simple setups | Production |

## SQLite (Default)

**Pros:**
- Zero configuration
- Widely available
- Good for development/testing
- FTS5 full-text search

**Cons:**
- Larger database size
- Slower text search
- No native vector search (requires external index)
- Manual graph traversal via JOINs

**Setup:**
```bash
# No additional installation needed
# Database created automatically at ~/.nima/memory/graph.sqlite
```

## LadybugDB (Recommended)

**Pros:**
- 44% smaller database
- 3.4x faster text search
- Native HNSW vector index
- Cypher graph queries
- All-in-one solution

**Cons:**
- Requires `real-ladybug` package
- Slightly slower graph traversal (acceptable)

**Setup:**
```bash
# Install LadybugDB
pip install real-ladybug

# Or with uv
uv pip install real-ladybug

# Migrate from SQLite
python scripts/ladybug_parallel.py --migrate

# Run benchmarks
python scripts/ladybug_parallel.py --benchmark
```

### Migration from SQLite

1. **Backup your database:**
   ```bash
   cp ~/.nima/memory/graph.sqlite ~/.nima/memory/graph.sqlite.backup
   ```

2. **Run migration:**
   ```bash
   cd ~/.openclaw/workspace
   source .venv/bin/activate
   python scripts/ladybug_parallel.py --migrate
   ```

3. **Verify migration:**
   ```bash
   python scripts/ladybug_parallel.py --benchmark
   ```

4. **Switch to LadybugDB:**
   ```javascript
   // In nima-recall-live/index.js
   const USE_LADYBUG = true;
   ```

5. **Restart gateway:**
   ```bash
   # Gateway will restart automatically, or:
   openclaw restart
   ```

### Rollback to SQLite

If you encounter issues:

```javascript
// In nima-recall-live/index.js
const USE_LADYBUG = false;

// Restore backup
cp ~/.nima/memory/graph.sqlite.backup ~/.nima/memory/graph.sqlite
```

## Vector Search Configuration

### SQLite + External Index

SQLite requires a separate embedding index:

```bash
# Build embedding index (required for semantic search)
python openclaw_hooks/nima-recall-live/build_embedding_index.py
```

The index is stored at:
- `~/.nima/memory/embedding_index.npy` (embeddings)
- `~/.nima/memory/embedding_index_meta.json` (metadata)

### LadybugDB Native HNSW

LadybugDB includes native HNSW vector search:

```python
# Vector search is built-in
# No separate index needed
# Embeddings stored directly in graph nodes

# Query example:
CALL QUERY_VECTOR_INDEX(
    'MemoryNode',
    'embedding_idx',
    $query_vector,
    10
)
RETURN node, distance;
```

## Performance Benchmarks

Run your own benchmarks:

```bash
python scripts/ladybug_parallel.py --benchmark
```

Expected results (your mileage may vary):

| Query Type | SQLite | LadybugDB | Speedup |
|------------|--------|-----------|---------|
| Text search | 31.7ms | 9.4ms | 3.4x |
| Query by who | 36.0ms | 7.4ms | 4.9x |
| Vector search | N/A | 18ms | NEW |
| Graph traversal | 0.4ms | 1.4ms | 0.3x |

## Database Location

| Database | Path |
|----------|------|
| SQLite | `~/.nima/memory/graph.sqlite` |
| SQLite FTS | `~/.nima/memory/graph.sqlite` (embedded) |
| LadybugDB | `~/.nima/memory/ladybug.lbug` |
| Embedding Index (SQLite) | `~/.nima/memory/embedding_index.npy` |

## Troubleshooting

### LadybugDB not found

```
Error: No module named 'real_ladybug'
```

**Solution:**
```bash
pip install real-ladybug
# or with uv:
uv pip install real-ladybug
```

### Migration fails

```
Error: Cannot copy nodes
```

**Solution:** Check for special characters in text fields. The migration script sanitizes most characters, but extremely long texts (>2000 chars) are truncated.

### Vector search not working

```
Error: function QUERY_VECTOR_INDEX is not defined
```

**Solution:** Load the vector extension:
```python
conn.execute("LOAD VECTOR")
```

This is handled automatically in `ladybug_recall.py`.