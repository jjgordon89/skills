#!/usr/bin/env python3
"""
NIMA LadybugDB Backend - Memory retrieval using LadybugDB graph + HNSW vector index
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# Activate venv
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/.venv/lib/python3.11/site-packages"))
import real_ladybug as lb
import re


def escape_cypher_string(s: str) -> str:
    """Safely escape a string for Cypher-like queries.
    
    Handles:
    - Backslashes (must be escaped first)
    - Single quotes
    - Null bytes
    - Control characters
    
    Note: Prefer parameterized queries when available.
    """
    if not s:
        return ""
    # Escape backslashes first, then quotes
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    # Remove null bytes and control characters
    s = re.sub(r'[\x00-\x1f]', '', s)
    return s


@dataclass
class Memory:
    """A memory node from the graph"""
    id: int
    text: str
    summary: str
    who: str
    layer: str
    timestamp: int
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "summary": self.summary,
            "who": self.who,
            "layer": self.layer,
            "timestamp": self.timestamp,
            "score": self.score
        }


class NIMALadybugBackend:
    """NIMA memory backend using LadybugDB"""
    
    def __init__(self, db_path: str = "~/.nima/memory/ladybug.lbug"):
        self.db_path = Path(db_path).expanduser()
        self.db: Optional[lb.Database] = None
        self.conn: Optional[lb.Connection] = None
        
    def connect(self):
        """Connect to the database"""
        if not self.db:
            self.db = lb.Database(str(self.db_path))
            self.conn = lb.Connection(self.db)
            # Load vector extension
            try:
                self.conn.execute("LOAD VECTOR")
            except:
                pass  # Extension may already be loaded
    
    def disconnect(self):
        """Disconnect from the database"""
        self.db = None
        self.conn = None
    
    def text_search(self, query: str, limit: int = 10) -> List[Memory]:
        """Search memories by text content (CONTAINS)"""
        self.connect()
        
        start = time.time()
        # Safely escape query for Cypher-like syntax
        safe_query = escape_cypher_string(query)
        
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode)
            WHERE n.text CONTAINS '{safe_query}' OR n.summary CONTAINS '{safe_query}'
            RETURN n.id, n.text, n.summary, n.who, n.layer, n.timestamp
            LIMIT {limit}
        """)
        
        memories = []
        for row in result:
            memories.append(Memory(
                id=row[0],
                text=row[1] or "",
                summary=row[2] or "",
                who=row[3] or "unknown",
                layer=row[4] or "unknown",
                timestamp=row[5] or 0,
                score=1.0  # No scoring for CONTAINS
            ))
        
        elapsed = (time.time() - start) * 1000
        return memories, elapsed
    
    def vector_search(self, query_embedding: List[float], limit: int = 10) -> List[Memory]:
        """Search memories by vector similarity (HNSW)"""
        self.connect()
        
        start = time.time()
        
        # Convert embedding to string
        emb_str = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"
        
        try:
            result = self.conn.execute(f"""
                CALL QUERY_VECTOR_INDEX(
                    'MemoryNode',
                    'embedding_idx',
                    {emb_str},
                    {limit}
                )
                RETURN node.id, node.text, node.summary, node.who, node.layer, node.timestamp, distance
                ORDER BY distance
            """)
            
            memories = []
            for row in result:
                # Convert distance to similarity score (1 - distance for cosine)
                score = 1.0 - row[6] if row[6] is not None else 0.0
                memories.append(Memory(
                    id=row[0],
                    text=row[1] or "",
                    summary=row[2] or "",
                    who=row[3] or "unknown",
                    layer=row[4] or "unknown",
                    timestamp=row[5] or 0,
                    score=score
                ))
            
            elapsed = (time.time() - start) * 1000
            return memories, elapsed
        except Exception as e:
            print(f"Vector search error: {e}")
            return [], 0
    
    def who_search(self, who: str, limit: int = 10) -> List[Memory]:
        """Search memories by who said it"""
        self.connect()
        
        start = time.time()
        # Safely escape for Cypher-like syntax
        safe_who = escape_cypher_string(who)
        
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode {{who: '{safe_who}'}})
            RETURN n.id, n.text, n.summary, n.who, n.layer, n.timestamp
            ORDER BY n.timestamp DESC
            LIMIT {limit}
        """)
        
        memories = []
        for row in result:
            memories.append(Memory(
                id=row[0],
                text=row[1] or "",
                summary=row[2] or "",
                who=row[3] or "unknown",
                layer=row[4] or "unknown",
                timestamp=row[5] or 0,
                score=1.0
            ))
        
        elapsed = (time.time() - start) * 1000
        return memories, elapsed
    
    def hybrid_search(self, query: str, query_embedding: List[float], 
                      limit: int = 10, text_weight: float = 0.3) -> List[Memory]:
        """Hybrid search combining text and vector similarity"""
        # Get results from both
        text_results, text_time = self.text_search(query, limit * 2)
        vector_results, vector_time = self.vector_search(query_embedding, limit * 2)
        
        # Combine and deduplicate
        seen_ids = set()
        combined = []
        
        # Add vector results first (higher priority)
        for m in vector_results:
            if m.id not in seen_ids:
                m.score = m.score * (1 - text_weight)
                combined.append(m)
                seen_ids.add(m.id)
        
        # Add text results
        for m in text_results:
            if m.id not in seen_ids:
                m.score = text_weight
                combined.append(m)
                seen_ids.add(m.id)
        
        # Sort by score and return top N
        combined.sort(key=lambda x: x.score, reverse=True)
        return combined[:limit], text_time + vector_time
    
    def get_related(self, node_id: int, limit: int = 10) -> List[Memory]:
        """Get related memories through graph edges"""
        self.connect()
        
        start = time.time()
        
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode {{id: {node_id}}})-[r:relates_to]-(related:MemoryNode)
            RETURN related.id, related.text, related.summary, related.who, related.layer, related.timestamp, r.weight
            ORDER BY r.weight DESC
            LIMIT {limit}
        """)
        
        memories = []
        for row in result:
            memories.append(Memory(
                id=row[0],
                text=row[1] or "",
                summary=row[2] or "",
                who=row[3] or "unknown",
                layer=row[4] or "unknown",
                timestamp=row[5] or 0,
                score=row[6] if row[6] else 1.0
            ))
        
        elapsed = (time.time() - start) * 1000
        return memories, elapsed
    
    def get_turn_context(self, node_id: int) -> Dict[str, Any]:
        """Get the turn context for a memory node (input → thinking → output)"""
        self.connect()
        
        result = self.conn.execute(f"""
            MATCH (t:Turn)-[:has_input]->(input:MemoryNode {{id: {node_id}}})
            OPTIONAL MATCH (t)-[:has_contemplation]->(think:MemoryNode)
            OPTIONAL MATCH (t)-[:has_output]->(output:MemoryNode)
            RETURN t.turn_id, input.summary, think.summary, output.summary
        """)
        
        rows = list(result)
        if rows:
            return {
                "turn_id": rows[0][0],
                "input": rows[0][1],
                "thinking": rows[0][2],
                "output": rows[0][3]
            }
        return None
    
    def stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        self.connect()
        
        # Node count
        result = self.conn.execute("MATCH (n:MemoryNode) RETURN COUNT(n)")
        nodes = list(result)[0][0]
        
        # Edge count
        result = self.conn.execute("MATCH ()-[r:relates_to]->() RETURN COUNT(r)")
        edges = list(result)[0][0]
        
        # Turn count
        result = self.conn.execute("MATCH (t:Turn) RETURN COUNT(t)")
        turns = list(result)[0][0]
        
        # Who distribution
        result = self.conn.execute("""
            MATCH (n:MemoryNode)
            RETURN n.who, COUNT(n)
            ORDER BY COUNT(n) DESC
            LIMIT 5
        """)
        who_dist = {row[0]: row[1] for row in result}
        
        return {
            "nodes": nodes,
            "edges": edges,
            "turns": turns,
            "who_distribution": who_dist
        }


def main():
    """Test the backend"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NIMA LadybugDB Backend")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    parser.add_argument("--search", type=str, help="Text search query")
    parser.add_argument("--who", type=str, help="Search by who")
    parser.add_argument("--limit", type=int, default=5, help="Limit results")
    
    args = parser.parse_args()
    
    backend = NIMALadybugBackend()
    
    if args.stats:
        stats = backend.stats()
        print("📊 Database Statistics:")
        print(f"   Nodes: {stats['nodes']:,}")
        print(f"   Edges: {stats['edges']:,}")
        print(f"   Turns: {stats['turns']:,}")
        print(f"   Who distribution:")
        for who, count in stats['who_distribution'].items():
            print(f"      {who}: {count:,}")
    
    if args.search:
        print(f"\n🔍 Text search: '{args.search}'")
        results, elapsed = backend.text_search(args.search, args.limit)
        print(f"   Found {len(results)} results in {elapsed:.1f}ms")
        for i, m in enumerate(results):
            print(f"   {i+1}. [{m.id}] {m.summary[:60]}...")
    
    if args.who:
        print(f"\n🔍 Search by who: '{args.who}'")
        results, elapsed = backend.who_search(args.who, args.limit)
        print(f"   Found {len(results)} results in {elapsed:.1f}ms")
        for i, m in enumerate(results):
            print(f"   {i+1}. [{m.id}] {m.summary[:60]}...")


if __name__ == "__main__":
    main()