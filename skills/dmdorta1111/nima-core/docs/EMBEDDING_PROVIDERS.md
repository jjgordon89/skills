# Embedding Providers

NIMA supports multiple embedding providers for semantic memory search.

## Quick Comparison

| Provider | Dimensions | Speed | Cost | Quality |
|----------|------------|-------|------|---------|
| **Voyage** (default) | 1024 | Fast | $0.12/1M tokens | Excellent |
| **OpenAI** | 1536 | Fast | $0.13/1M tokens | Excellent |
| **Local** (sentence-transformers) | 384 | Slowest | Free | Good |

## Configuration

Set your embedding provider in `~/.nima/config.json`:

```json
{
  "embedding": {
    "provider": "voyage",
    "model": "voyage-2",
    "api_key": "your-api-key"
  }
}
```

Or via environment variable:

```bash
export NIMA_EMBEDDER=voyage
export VOYAGE_API_KEY=your-api-key
```

## Voyage (Recommended)

**voyage-2** is the default and recommended provider.

```bash
export NIMA_EMBEDDER=voyage
export VOYAGE_API_KEY=pa-xxx...
```

**Pros:**
- Excellent semantic understanding
- 1024 dimensions (efficient)
- Fast API response
- Good value for money

**Cons:**
- Requires API key
- External dependency

**Get API key:** https://www.voyageai.com/

## OpenAI

**text-embedding-3-small** or **text-embedding-3-large**

```bash
export NIMA_EMBEDDER=openai
export OPENAI_API_KEY=sk-xxx...
```

**Pros:**
- Available if you already use OpenAI
- 1536 dimensions for small, 3072 for large
- Consistent with other OpenAI tools

**Cons:**
- Slightly more expensive
- Larger dimensions = more storage

## Local (Sentence Transformers)

**all-MiniLM-L6-v2** (default local model)

```bash
export NIMA_EMBEDDER=local
# Or specify model:
export NIMA_EMBEDDER=local
export NIMA_LOCAL_MODEL=all-MiniLM-L6-v2
```

**Pros:**
- No API key needed
- Completely private
- No per-token cost

**Cons:**
- Slower (runs locally)
- Lower quality than Voyage/OpenAI
- Requires PyTorch

## Embedding Dimensions

Different providers use different vector dimensions. NIMA handles this automatically:

| Provider | Dimensions | Projection |
|----------|------------|------------|
| Voyage | 1024 | None (native) |
| OpenAI small | 1536 | Truncate to 1024 |
| OpenAI large | 3072 | Truncate to 1024 |
| Local (MiniLM) | 384 | Project to 1024 |

## Switching Providers

When switching embedding providers, you should rebuild the embedding index:

### For SQLite:

```bash
# Rebuild embedding index
python openclaw_hooks/nima-recall-live/build_embedding_index.py --rebuild
```

### For LadybugDB:

LadybugDB stores embeddings inline with nodes — no separate migration needed.
Just set your provider and run:

```bash
export VOYAGE_API_KEY=your-key
python scripts/ladybug_parallel.py --rebuild-embeddings
```

## Cost Estimation

| Usage | Voyage | OpenAI small | Local |
|-------|--------|--------------|-------|
| 10K memories/month | ~$1.20 | ~$1.30 | $0 |
| 100K memories/month | ~$12 | ~$13 | $0 |
| 1M memories/month | ~$120 | ~$130 | $0 |

## Quality Benchmarks

Based on MTEB (Massive Text Embedding Benchmark):

| Model | MTEB Score |
|-------|------------|
| voyage-2 | 68.3 |
| text-embedding-3-large | 67.5 |
| text-embedding-3-small | 65.1 |
| all-MiniLM-L6-v2 | 56.3 |

Higher is better. Scores are approximate and vary by task.

## Troubleshooting

### "No embedding provider configured"

Set the `NIMA_EMBEDDER` environment variable:
```bash
export NIMA_EMBEDDER=voyage
```

### "API key not found"

Set the appropriate API key:
```bash
export VOYAGE_API_KEY=pa-xxx...
# or
export OPENAI_API_KEY=sk-xxx...
```

### "Local model download failed"

Pre-download the model:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('/path/to/local/model')
```

### "Embedding dimension mismatch"

The system automatically handles dimension differences. If you see errors, check:
1. Your `NIMA_EMBEDDER` setting
2. The model specified in your config
3. Run `--rebuild` on your embedding index