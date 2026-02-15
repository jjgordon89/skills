#!/usr/bin/env python3
"""
NIMA Voyage Embedding System
=============================
Embeds memory nodes with Voyage-3-lite for semantic search.
Supports: embed single text, batch embed, cosine similarity search.

Usage:
  # Embed a single text
  python3 embeddings.py embed "some text here"
  
  # Backfill all un-embedded nodes
  python3 embeddings.py backfill [--batch-size 64]
  
  # Semantic search
  python3 embeddings.py search "feeling isolated and scared" [--top 5]
  
  # Stats
  python3 embeddings.py stats
"""

import sqlite3
import json
import struct
import sys
import os
import time

GRAPH_DB = os.path.join(os.path.expanduser("~"), ".nima", "memory", "graph.sqlite")
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    print("ERROR: VOYAGE_API_KEY environment variable not set", file=sys.stderr)
MODEL = "voyage-3-lite"
EMBEDDING_DIM = 512
BATCH_SIZE = 64  # Voyage max is 128, stay safe
MAX_TEXT_CHARS = 2000  # Truncate long texts

def get_client():
    import voyageai
    return voyageai.Client(api_key=VOYAGE_API_KEY)

def encode_vector(vec):
    """Pack float list into bytes for SQLite BLOB storage."""
    return struct.pack(f'{len(vec)}f', *vec)

def decode_vector(blob):
    """Unpack bytes back to float list."""
    n = len(blob) // 4
    return list(struct.unpack(f'{n}f', blob))

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def ensure_embedding_column(db):
    """Add embedding column if it doesn't exist."""
    cols = [r[1] for r in db.execute("PRAGMA table_info(memory_nodes)").fetchall()]
    if "embedding" not in cols:
        db.execute("ALTER TABLE memory_nodes ADD COLUMN embedding BLOB DEFAULT NULL")
        db.commit()
        print("✅ Added 'embedding' column to memory_nodes")
    return True

def embed_texts(client, texts):
    """Embed a batch of texts, truncating long ones."""
    truncated = [t[:MAX_TEXT_CHARS] if t else "" for t in texts]
    # Filter empty strings
    valid = [(i, t) for i, t in enumerate(truncated) if t.strip()]
    if not valid:
        return [None] * len(texts)
    
    indices, valid_texts = zip(*valid)
    result = client.embed(list(valid_texts), model=MODEL)
    
    embeddings = [None] * len(texts)
    for idx, emb in zip(indices, result.embeddings):
        embeddings[idx] = emb
    
    return embeddings

def backfill(batch_size=BATCH_SIZE):
    """Embed all nodes that don't have embeddings yet."""
    db = sqlite3.connect(GRAPH_DB)
    db.row_factory = sqlite3.Row
    ensure_embedding_column(db)
    
    # Count un-embedded
    total = db.execute("SELECT COUNT(*) FROM memory_nodes WHERE embedding IS NULL").fetchone()[0]
    embedded_count = db.execute("SELECT COUNT(*) FROM memory_nodes WHERE embedding IS NOT NULL").fetchone()[0]
    print(f"📊 {embedded_count} already embedded, {total} remaining")
    
    if total == 0:
        print("✅ All nodes already embedded!")
        return
    
    client = get_client()
    processed = 0
    total_tokens = 0
    start = time.time()
    
    while True:
        rows = db.execute("""
            SELECT id, text, summary 
            FROM memory_nodes 
            WHERE embedding IS NULL 
            LIMIT ?
        """, (batch_size,)).fetchall()
        
        if not rows:
            break
        
        # Use summary if available, fall back to text
        texts = []
        for r in rows:
            t = r["summary"] if r["summary"] and len(r["summary"]) > 10 else r["text"]
            texts.append(t or "")
        
        try:
            embeddings = embed_texts(client, texts)
            
            db.execute("BEGIN TRANSACTION")
            for row, emb in zip(rows, embeddings):
                if emb:
                    db.execute("UPDATE memory_nodes SET embedding = ? WHERE id = ?",
                              (encode_vector(emb), row["id"]))
            db.execute("COMMIT")
            
            processed += len(rows)
            elapsed = time.time() - start
            rate = processed / elapsed if elapsed > 0 else 0
            print(f"  ... embedded {processed}/{total} ({rate:.0f}/s)")
            
            # Rate limiting — Voyage allows 300 RPM, be conservative
            time.sleep(0.3)
            
        except Exception as e:
            print(f"  ❌ Batch error: {e}")
            db.execute("ROLLBACK")
            time.sleep(2)
            continue
    
    elapsed = time.time() - start
    print(f"\n✅ Backfill complete! {processed} nodes embedded in {elapsed:.1f}s")
    
    final = db.execute("SELECT COUNT(*) FROM memory_nodes WHERE embedding IS NOT NULL").fetchone()[0]
    print(f"   Total embedded: {final}")
    db.close()

def search(query, top_k=5):
    """Semantic search using Voyage embeddings + cosine similarity."""
    db = sqlite3.connect(GRAPH_DB)
    db.row_factory = sqlite3.Row
    
    client = get_client()
    result = client.embed([query[:MAX_TEXT_CHARS]], model=MODEL)
    query_vec = result.embeddings[0]
    
    # Load all embedded nodes (in production, use an index like FAISS)
    rows = db.execute("""
        SELECT id, layer, text, summary, who, timestamp, turn_id, affect_json, embedding
        FROM memory_nodes
        WHERE embedding IS NOT NULL
    """).fetchall()
    
    # Score each
    scored = []
    for r in rows:
        vec = decode_vector(r["embedding"])
        sim = cosine_similarity(query_vec, vec)
        scored.append((sim, r))
    
    # Sort by similarity
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for sim, r in scored[:top_k]:
        results.append({
            "id": r["id"],
            "score": round(sim, 4),
            "layer": r["layer"],
            "who": r["who"],
            "summary": r["summary"][:150],
            "turn_id": r["turn_id"],
            "timestamp": r["timestamp"]
        })
    
    db.close()
    return results

def stats():
    """Show embedding stats."""
    db = sqlite3.connect(GRAPH_DB)
    total = db.execute("SELECT COUNT(*) FROM memory_nodes").fetchone()[0]
    embedded = db.execute("SELECT COUNT(*) FROM memory_nodes WHERE embedding IS NOT NULL").fetchone()[0]
    pct = (embedded / total * 100) if total > 0 else 0
    print(f"📊 Embedding Stats:")
    print(f"   Total nodes: {total}")
    print(f"   Embedded: {embedded} ({pct:.1f}%)")
    print(f"   Remaining: {total - embedded}")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "backfill":
        bs = int(sys.argv[2]) if len(sys.argv) > 2 else BATCH_SIZE
        backfill(bs)
    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        top = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        results = search(query, top)
        for r in results:
            print(f"  [{r['score']:.3f}] [{r['who']}] {r['summary']}")
    elif cmd == "stats":
        stats()
    elif cmd == "embed":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        client = get_client()
        result = client.embed([text], model=MODEL)
        print(f"Dim: {len(result.embeddings[0])}, tokens: {result.total_tokens}")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
