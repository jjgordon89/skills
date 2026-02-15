#!/usr/bin/env python3
"""
NIMA Lazy Reconstruction Recall (Canonical)
============================================

Unified recall system combining FTS + semantic search with intelligent caching.

Optimizations:
  - Pre-computed embedding index (instant semantic search)
  - Query cache (zero latency for repeated queries)
  - Deferred summary loading (load only after final scoring)
  - Affect-weighted reranking (emotional resonance)

Author: Lilu + David Dorta
Date: 2026-02-14
Updated: 2026-02-15 (Consolidated from v1/v2/v3)
"""

import sqlite3
import json
import sys
import os
import time
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, List, Dict, Any

# Config
DEFAULT_DB = os.path.expanduser("~/.nima/memory/graph.sqlite")
EMBEDDING_INDEX_PATH = os.path.expanduser("~/.nima/memory/embedding_index.npy")
EMBEDDING_META_PATH = os.path.expanduser("~/.nima/memory/embedding_index_meta.json")
MAX_RESULTS = 7  # Increased from 3 for richer context
TIME_WINDOW_DAYS = 90
EMBEDDING_THRESHOLD = 0.35
FTS_CONFIDENCE_THRESHOLD = 15.0
FTS_MIN_RESULTS = 3
SKIP_EMBEDDING_MIN_LENGTH = 10

# =============================================================================
# EMBEDDING INDEX (pre-computed, instant search)
# =============================================================================

_embedding_matrix = None
_embedding_meta = None

def load_embedding_index():
    """Load pre-computed embedding index."""
    global _embedding_matrix, _embedding_meta
    
    if _embedding_matrix is not None:
        return _embedding_matrix, _embedding_meta
    
    try:
        if os.path.exists(EMBEDDING_INDEX_PATH) and os.path.exists(EMBEDDING_META_PATH):
            _embedding_matrix = np.load(EMBEDDING_INDEX_PATH)
            with open(EMBEDDING_META_PATH, 'r') as f:
                _embedding_meta = json.load(f)
            return _embedding_matrix, _embedding_meta
    except Exception as e:
        print(f"[lazy_recall] Could not load embedding index: {e}", file=sys.stderr)
    
    return None, None

def search_embedding_index(query_vec: np.ndarray, top_k: int = 20) -> List[Dict]:
    """Search pre-computed embedding index for similar vectors."""
    matrix, meta = load_embedding_index()
    
    if matrix is None or meta is None:
        return []
    
    # Normalize query
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    
    # Normalize all embeddings
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8
    normalized = matrix / norms
    
    # Compute similarities
    similarities = np.dot(normalized, query_norm)
    
    # Get top-k
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = []
    entries = meta.get('entries', [])
    min_timestamp = int((datetime.now() - timedelta(days=TIME_WINDOW_DAYS)).timestamp() * 1000)
    
    for idx in top_indices:
        if similarities[idx] < EMBEDDING_THRESHOLD:
            continue
        if idx < len(entries):
            entry = entries[idx]
            if entry.get('timestamp', 0) >= min_timestamp:
                results.append({
                    'turn_id': entry.get('turn_id'),
                    'timestamp': entry.get('timestamp'),
                    'emb_score': float(similarities[idx])
                })
    
    return results

# =============================================================================
# QUERY CACHE
# =============================================================================

_query_cache: Dict[str, tuple] = {}
_QUERY_CACHE_MAX = 100
_QUERY_CACHE_TTL = 300  # 5 minutes

def get_cached_result(query: str) -> Optional[Dict]:
    """Get cached result if still valid."""
    if query in _query_cache:
        result, timestamp = _query_cache[query]
        if time.time() - timestamp < _QUERY_CACHE_TTL:
            return result
    return None

def cache_result(query: str, result: Dict):
    """Cache a result."""
    global _query_cache
    
    if len(_query_cache) >= _QUERY_CACHE_MAX:
        # Evict oldest
        oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]
    
    _query_cache[query] = (result, time.time())

# =============================================================================
# VOYAGE API (fallback if no pre-computed index)
# =============================================================================

def get_embedding_voyage(text: str) -> Optional[np.ndarray]:
    """Get embedding from Voyage API."""
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("ERROR: VOYAGE_API_KEY environment variable not set", file=sys.stderr)
        return None
    try:
        import voyageai
        client = voyageai.Client(api_key=api_key)
        result = client.embed([text[:500]], model="voyage-3-lite")
        return np.array(result.embeddings[0], dtype=np.float32)
    except Exception as e:
        print(f"[lazy_recall] Voyage error: {e}", file=sys.stderr)
        return None

# =============================================================================
# FTS5 SEARCH
# =============================================================================

def sanitize_fts5_query(text: str) -> str:
    """Escape special FTS5 characters."""
    if not text:
        return ""
    import re
    cleaned = re.sub(r'[()\{\}\[\]"\'\*\^\-\+:\~\?,\.!]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def normalize_timestamp(ts: int) -> int:
    """Normalize timestamp to milliseconds."""
    if ts < 4102444800:
        return ts * 1000
    return ts

def fts_search(db, query: str, limit: int, min_timestamp: int) -> List[Dict]:
    """FTS5 search for candidate turn_ids."""
    safe_query = sanitize_fts5_query(query)
    if not safe_query:
        return []
    
    try:
        cursor = db.execute("""
            SELECT n.turn_id, n.timestamp, MIN(fts.rank) as best_score
            FROM memory_fts fts
            JOIN memory_nodes n ON fts.rowid = n.id
            WHERE memory_fts MATCH ?
            GROUP BY n.turn_id
            ORDER BY best_score
            LIMIT ?
        """, (safe_query, limit * 10))
        
        results = []
        for r in cursor:
            ts = normalize_timestamp(r[1])
            if ts >= min_timestamp:
                results.append({
                    'turn_id': r[0],
                    'timestamp': ts,
                    'fts_score': abs(r[2])
                })
                if len(results) >= limit * 3:
                    break
        
        return results
    except Exception as e:
        print(f"[lazy_recall] FTS error: {e}", file=sys.stderr)
        return []

# =============================================================================
# DEFERRED SUMMARY LOADING
# =============================================================================

AFFECT_DIMENSIONS = ["SEEKING", "RAGE", "FEAR", "LUST", "CARE", "PANIC", "PLAY"]

def parse_affect_json(affect_json_str: str) -> Dict[str, float]:
    if not affect_json_str:
        return {}
    try:
        data = json.loads(affect_json_str)
        return {k: float(v) for k, v in data.items() 
                if k in AFFECT_DIMENSIONS and isinstance(v, (int, float))}
    except:
        return {}

def load_summaries_for_turns(db, turn_ids: List[str]) -> Dict[str, Dict]:
    """Load summaries only for the final top candidates."""
    if not turn_ids:
        return {}
    
    placeholders = ",".join("?" * len(turn_ids))
    cursor = db.execute(f"""
        SELECT turn_id, layer, summary, who, affect_json
        FROM memory_nodes
        WHERE turn_id IN ({placeholders})
    """, turn_ids)
    
    results = {}
    for row in cursor:
        tid = row[0]
        if tid not in results:
            results[tid] = {'layers': {}, 'who': row[3] or 'unknown', 'affect': {}}
        results[tid]['layers'][row[1]] = row[2] or ''
        if row[4]:
            results[tid]['affect'] = parse_affect_json(row[4])
    
    return results

def compute_affect_resonance(memory_affect: Dict, current_affect: Dict) -> float:
    if not memory_affect or not current_affect:
        return 0.5
    
    total_diff = 0.0
    dimensions = 0
    
    for dim in AFFECT_DIMENSIONS:
        if dim in memory_affect and dim in current_affect:
            total_diff += abs(memory_affect[dim] - current_affect[dim])
            dimensions += 1
        elif dim in memory_affect or dim in current_affect:
            total_diff += 0.3
            dimensions += 1
    
    return 1.0 - min(total_diff / max(dimensions, 1), 1.0) if dimensions > 0 else 0.5

def compute_affect_bleed(memories: List[Dict], current_affect: Dict, 
                         bleed_factor: float = 0.08) -> Dict[str, float]:
    bleed = {dim: 0.0 for dim in AFFECT_DIMENSIONS}
    for m in memories:
        affect = m.get('affect', {})
        for dim in AFFECT_DIMENSIONS:
            if dim in affect:
                bleed[dim] += affect[dim] * bleed_factor
    return bleed

# =============================================================================
# MAIN RECALL
# =============================================================================

def lazy_recall(query_text: str, db_path: str = DEFAULT_DB, 
                 max_results: int = MAX_RESULTS,
                 current_affect: Optional[Dict] = None,
                 use_embedding: Optional[bool] = None) -> Dict:
    """
    Optimized lazy recall with:
      - Pre-computed embedding index (instant semantic search)
      - Query cache (zero latency for repeated queries)
      - Deferred summary loading (load only after scoring)
    
    Args:
        query_text: Search query
        db_path: Path to graph database
        max_results: Maximum results to return
        current_affect: Current affect state for resonance scoring
        use_embedding: If None, auto-decide based on query length.
                      If False, skip embedding search (FTS-only mode).
                      If True, always use embedding search.
    """
    start_time = time.time()
    
    # 1. Check cache
    cached = get_cached_result(query_text)
    if cached:
        print(f"[lazy_recall] Cache hit for '{query_text[:30]}...'", file=sys.stderr)
        return cached
    
    min_timestamp = int((datetime.now() - timedelta(days=TIME_WINDOW_DAYS)).timestamp() * 1000)
    
    # Auto-decide embedding use if not specified
    if use_embedding is None:
        use_embedding = len(query_text) >= SKIP_EMBEDDING_MIN_LENGTH
    
    db = sqlite3.connect(db_path)
    
    # 2. FTS search (always run)
    fts_candidates = fts_search(db, query_text, max_results, min_timestamp)
    
    # 3. Check if we can skip embedding
    skipped_embedding = False
    if fts_candidates and len(fts_candidates) >= FTS_MIN_RESULTS:
        best_fts_score = min(c.get('fts_score', 999) for c in fts_candidates)
        if best_fts_score < FTS_CONFIDENCE_THRESHOLD:
            skipped_embedding = True
            print(f"[lazy_recall] Skipping embedding (FTS score {best_fts_score:.1f})", 
                  file=sys.stderr)
    
    # 4. Embedding search (if needed)
    emb_candidates = []
    if use_embedding and not skipped_embedding:
        # Try pre-computed index first
        matrix, meta = load_embedding_index()
        
        if matrix is not None:
            # Get query embedding from Voyage
            query_vec = get_embedding_voyage(query_text)
            if query_vec is not None:
                emb_candidates = search_embedding_index(query_vec, max_results * 3)
                print(f"[lazy_recall] Index search found {len(emb_candidates)} candidates", 
                      file=sys.stderr)
        else:
            print(f"[lazy_recall] No pre-computed index, run build_embedding_index.py", 
                  file=sys.stderr)
    
    # 5. Merge and score candidates
    merged = {}
    for c in fts_candidates:
        merged[c['turn_id']] = c
    
    for c in emb_candidates:
        tid = c['turn_id']
        if tid in merged:
            merged[tid]['emb_score'] = c.get('emb_score', 0)
        else:
            merged[tid] = c
    
    # 6. Score without loading summaries
    candidates = list(merged.values())
    for c in candidates:
        fts_norm = min(c.get('fts_score', 0) / 50, 1.0)
        emb_norm = c.get('emb_score', 0)
        affect_res = compute_affect_resonance(c.get('affect', {}), current_affect or {})
        
        if skipped_embedding or not use_embedding:
            c['score'] = (fts_norm * 0.85) + (affect_res * 0.15)
        else:
            c['score'] = (fts_norm * 0.35) + (emb_norm * 0.50) + (affect_res * 0.15)
        
        c['affect_resonance'] = affect_res
    
    # 7. Sort and take top N
    ranked = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)[:max_results]
    
    # 8. NOW load summaries only for top N
    top_turn_ids = [c['turn_id'] for c in ranked]
    summaries = load_summaries_for_turns(db, top_turn_ids)
    db.close()
    
    # Merge summaries into results
    for c in ranked:
        tid = c.get('turn_id')
        if tid in summaries:
            c['layers'] = summaries[tid]['layers']
            c['who'] = summaries[tid]['who']
            c['affect'] = summaries[tid]['affect']
        else:
            c['layers'] = {}
            c['who'] = 'unknown'
    
    # 9. Compute affect bleed
    affect_bleed = compute_affect_bleed(ranked, current_affect)
    
    # 10. Format output
    output = []
    for r in ranked:
        parts = []
        layers = r.get('layers', {})
        if layers.get('input'):
            parts.append(f"In: {layers['input'][:100]}")
        if layers.get('output'):
            parts.append(f"Out: {layers['output'][:100]}")
        if layers.get('contemplation'):
            parts.append(f"Think: {layers['contemplation'][:80]}")
        if parts:
            who = r.get('who', 'unknown')
            output.append(f"[{who}] " + " | ".join(parts))
    
    result = {
        'memories': output,
        'affect_bleed': affect_bleed
    }
    
    # Cache result
    cache_result(query_text, result)
    
    elapsed = time.time() - start_time
    if elapsed > 0.1:
        print(f"[lazy_recall] Slow query: {elapsed*1000:.0f}ms for '{query_text[:30]}...'", 
              file=sys.stderr)
    
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NIMA Lazy Recall v3")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--affect", help="Current affect state as JSON")
    parser.add_argument("--fts-only", action="store_true", help="Use FTS-only mode (skip embeddings)")
    parser.add_argument("--max-results", type=int, default=7, help="Max results to return")
    args = parser.parse_args()
    
    current_affect = None
    if args.affect:
        try:
            current_affect = json.loads(args.affect)
        except:
            pass
    
    # FTS-only mode skips embedding search entirely
    result = lazy_recall(
        args.query, 
        current_affect=current_affect,
        use_embedding=not args.fts_only,
        max_results=args.max_results
    )
    print(json.dumps(result))