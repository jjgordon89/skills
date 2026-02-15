#!/usr/bin/env python3
"""
LadybugDB Parallel Implementation for NIMA Memory System
Creates a side-by-side comparison with SQLite backend
"""

import sqlite3
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any

# Activate venv and import ladybug
import sys
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
    """
    if not s:
        return ""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = re.sub(r'[\x00-\x1f]', '', s)
    return s


def sanitize_text(s: str, max_len: int = 500) -> str:
    """Sanitize text for database storage - removes newlines and escapes quotes"""
    if not s:
        return ""
    s = str(s)[:max_len]
    # Replace newlines with spaces, remove control characters except tab
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # Escape special CSV characters
    s = s.replace("\\", "\\\\")  # Backslash first
    s = s.replace('"', '\\"')    # Double quotes
    s = s.replace("'", "''")      # Single quotes
    s = "".join(c if ord(c) >= 32 or c in "\t" else " " for c in s)
    # Collapse multiple spaces
    s = re.sub(r' +', ' ', s)
    return s.strip()


@dataclass
class BenchmarkResult:
    """Results from a benchmark query"""
    query_name: str
    sqlite_time_ms: float
    ladybug_time_ms: float
    sqlite_results: int
    ladybug_results: int
    speedup: float


class NIMALadybugDB:
    """Parallel LadybugDB backend for NIMA memory system"""
    
    def __init__(self, db_path: str = "~/.nima/memory/ladybug.lbug"):
        self.db_path = Path(db_path).expanduser()
        self.csv_dir = self.db_path.parent / "csv_temp"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.db: Optional[lb.Database] = None
        self.conn: Optional[lb.Connection] = None
        
    def initialize(self):
        """Create the database schema"""
        if self.db_path.exists():
            self.db_path.unlink()
            
        self.db = lb.Database(str(self.db_path))
        self.conn = lb.Connection(self.db)
        
        # Create node table
        self.conn.execute("""
            CREATE NODE TABLE MemoryNode (
                id INT64 PRIMARY KEY,
                timestamp INT64,
                layer STRING,
                text STRING,
                summary STRING,
                who STRING,
                affect_json STRING,
                session_key STRING,
                conversation_id STRING,
                turn_id STRING,
                fe_score DOUBLE
            )
        """)
        
        # Create edge table (relationships between nodes)
        self.conn.execute("""
            CREATE REL TABLE relates_to (
                FROM MemoryNode TO MemoryNode,
                relation STRING,
                weight DOUBLE
            )
        """)
        
        # Create turn table (links input → thinking → output)
        self.conn.execute("""
            CREATE NODE TABLE Turn (
                id INT64 PRIMARY KEY,
                turn_id STRING,
                timestamp INT64,
                affect_json STRING
            )
        """)
        
        # Link turns to nodes
        self.conn.execute("""
            CREATE REL TABLE has_input (FROM Turn TO MemoryNode)
        """)
        self.conn.execute("""
            CREATE REL TABLE has_contemplation (FROM Turn TO MemoryNode)
        """)
        self.conn.execute("""
            CREATE REL TABLE has_output (FROM Turn TO MemoryNode)
        """)
        
        print(f"✅ LadybugDB initialized at {self.db_path}")
        
    def migrate_from_sqlite(self, sqlite_path: str = "~/.nima/memory/graph.sqlite"):
        """Migrate all data from SQLite to LadybugDB using CSV files"""
        sqlite_path = Path(sqlite_path).expanduser()
        
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")
            
        conn_sqlite = sqlite3.connect(str(sqlite_path))
        
        start_time = time.time()
        
        # ==================== NODES ====================
        print("📦 Loading nodes from SQLite...")
        df_nodes = pd.read_sql_query("""
            SELECT id, timestamp, layer, text, summary, who, 
                   affect_json, session_key, conversation_id, turn_id, fe_score
            FROM memory_nodes
            ORDER BY id
        """, conn_sqlite)
        
        # Sanitize text columns - remove newlines and special chars
        for col in ['text', 'summary', 'who', 'affect_json', 'session_key', 'conversation_id', 'turn_id']:
            df_nodes[col] = df_nodes[col].fillna('').apply(
                lambda x: sanitize_text(x, 2000 if col == 'text' else 500)
            )
        
        # Fill numeric nulls
        df_nodes['fe_score'] = df_nodes['fe_score'].fillna(0.5)
        df_nodes['timestamp'] = df_nodes['timestamp'].fillna(0).astype('int64')
        df_nodes['id'] = df_nodes['id'].astype('int64')
        
        print(f"   Found {len(df_nodes):,} nodes")
        
        # Save to CSV - with escape character to handle special chars
        nodes_csv = self.csv_dir / "nodes_csv"
        df_nodes.to_csv(nodes_csv, index=False, escapechar='\\')
        print(f"   Saved to {nodes_csv}")
        
        # COPY FROM CSV - specify file format
        print("📦 Copying nodes to LadybugDB...")
        self.conn.execute(f"COPY MemoryNode FROM '{nodes_csv}' (file_format = 'csv', header = true)")
        
        print(f"✅ Migrated {len(df_nodes):,} nodes")
        
        # ==================== EDGES ====================
        print("📦 Loading edges from SQLite...")
        df_edges = pd.read_sql_query("""
            SELECT source_id, target_id, relation, weight
            FROM memory_edges
        """, conn_sqlite)
        
        if len(df_edges) > 0:
            df_edges['relation'] = df_edges['relation'].fillna('related').apply(lambda x: sanitize_text(x, 100))
            df_edges['weight'] = df_edges['weight'].fillna(1.0)
            df_edges['source_id'] = df_edges['source_id'].astype('int64')
            df_edges['target_id'] = df_edges['target_id'].astype('int64')
            
            print(f"   Found {len(df_edges):,} edges")
            
            # Save to CSV
            edges_csv = self.csv_dir / "edges.csv"
            df_edges.to_csv(edges_csv, index=False, escapechar='\\')
            
            # For edges, we need to create relationships via Cypher after creating edge data
            # LadybugDB doesn't have a direct way to create edges from CSV, so we'll iterate
            
            print("📦 Creating edge relationships...")
            batch_size = 500
            created = 0
            for i in range(0, len(df_edges), batch_size):
                batch = df_edges.iloc[i:i+batch_size]
                for _, row in batch.iterrows():
                    try:
                        self.conn.execute(f"""
                            MATCH (a:MemoryNode {{id: {int(row['source_id'])}}}), 
                                   (b:MemoryNode {{id: {int(row['target_id'])}}})
                            CREATE (a)-[:relates_to {{relation: '{row['relation']}', weight: {row['weight']}}}]->(b)
                        """)
                        created += 1
                    except:
                        pass  # Skip broken edges
                        
                print(f"   Created {min(i + batch_size, len(df_edges)):,}/{len(df_edges):,} edges...")
            
            print(f"✅ Created {created:,} edge relationships")
        
        # ==================== TURNS ====================
        print("📦 Loading turns from SQLite...")
        df_turns = pd.read_sql_query("""
            SELECT id, turn_id, input_node_id, contemplation_node_id, 
                   output_node_id, timestamp, affect_json
            FROM memory_turns
        """, conn_sqlite)
        
        if len(df_turns) > 0:
            df_turns['turn_id'] = df_turns['turn_id'].fillna('').apply(lambda x: sanitize_text(x, 200))
            df_turns['affect_json'] = df_turns['affect_json'].fillna('{}').apply(lambda x: sanitize_text(x, 500))
            df_turns['timestamp'] = df_turns['timestamp'].fillna(0).astype('int64')
            df_turns['id'] = df_turns['id'].astype('int64')
            
            print(f"   Found {len(df_turns):,} turns")
            
            # Save turn nodes to CSV
            df_turns_nodes = df_turns[['id', 'turn_id', 'timestamp', 'affect_json']].copy()
            turns_csv = self.csv_dir / "turns.csv"
            df_turns_nodes.to_csv(turns_csv, index=False, escapechar='\\')
            
            # COPY FROM CSV for turn nodes
            self.conn.execute(f"COPY Turn FROM '{turns_csv}'")
            print(f"✅ Copied {len(df_turns):,} turns")
            
            # Create turn relationships
            print("📦 Creating turn relationships...")
            created = 0
            for _, row in df_turns.iterrows():
                turn_id = int(row['id'])
                try:
                    if pd.notna(row['input_node_id']):
                        self.conn.execute(f"""
                            MATCH (t:Turn {{id: {turn_id}}}), (n:MemoryNode {{id: {int(row['input_node_id'])}}})
                            CREATE (t)-[:has_input]->(n)
                        """)
                        created += 1
                except:
                    pass
                try:
                    if pd.notna(row['contemplation_node_id']):
                        self.conn.execute(f"""
                            MATCH (t:Turn {{id: {turn_id}}}), (n:MemoryNode {{id: {int(row['contemplation_node_id'])}}})
                            CREATE (t)-[:has_contemplation]->(n)
                        """)
                        created += 1
                except:
                    pass
                try:
                    if pd.notna(row['output_node_id']):
                        self.conn.execute(f"""
                            MATCH (t:Turn {{id: {turn_id}}}), (n:MemoryNode {{id: {int(row['output_node_id'])}}})
                            CREATE (t)-[:has_output]->(n)
                        """)
                        created += 1
                except:
                    pass
            
            print(f"✅ Created turn relationships")
        
        elapsed = time.time() - start_time
        print(f"\n✅ Migration complete in {elapsed:.1f}s")
        
        conn_sqlite.close()
        
    def query_by_text(self, search_term: str, limit: int = 10) -> List[Tuple]:
        """Search nodes by text content (Cypher query)"""
        # Safely escape the search term for Cypher
        safe_term = escape_cypher_string(search_term)
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode)
            WHERE n.text CONTAINS '{safe_term}'
            RETURN n.id, n.who, n.layer, n.summary
            LIMIT {limit}
        """)
        return list(result)

    def query_by_who(self, who: str, limit: int = 10) -> List[Tuple]:
        """Query nodes by who said it"""
        safe_who = escape_cypher_string(who)
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode {{who: '{safe_who}'}})
            RETURN n.id, n.text, n.summary
            ORDER BY n.timestamp DESC
            LIMIT {limit}
        """)
        return list(result)
    
    def query_conversation_chain(self, node_id: int, depth: int = 2) -> List[Tuple]:
        """Find conversation chains through turns (multi-hop query)"""
        result = self.conn.execute(f"""
            MATCH (t:Turn)-[:has_input]->(input:MemoryNode {{id: {node_id}}})
            OPTIONAL MATCH (t)-[:has_contemplation]->(think:MemoryNode)
            OPTIONAL MATCH (t)-[:has_output]->(output:MemoryNode)
            RETURN t.turn_id, input.summary, think.summary, output.summary
        """)
        return list(result)
    
    def query_related_nodes(self, node_id: int, limit: int = 10) -> List[Tuple]:
        """Find related nodes through edges"""
        result = self.conn.execute(f"""
            MATCH (n:MemoryNode {{id: {node_id}}})-[r:relates_to]-(related:MemoryNode)
            RETURN related.id, r.relation, r.weight, related.summary
            ORDER BY r.weight DESC
            LIMIT {limit}
        """)
        return list(result)
    
    def close(self):
        if self.conn:
            # LadybugDB auto-commits
            pass


class BenchmarkComparison:
    """Compare SQLite vs LadybugDB performance"""
    
    def __init__(self, sqlite_path: str = "~/.nima/memory/graph.sqlite",
                 ladybug_path: str = "~/.nima/memory/ladybug.lbug"):
        self.sqlite_path = Path(sqlite_path).expanduser()
        self.ladybug_path = Path(ladybug_path).expanduser()
        
    def benchmark_text_search(self, search_term: str = "memory") -> BenchmarkResult:
        """Compare text search performance"""
        
        # SQLite search (FTS5)
        conn = sqlite3.connect(str(self.sqlite_path))
        start = time.time()
        cursor = conn.execute(f"""
            SELECT n.id, n.who, n.layer, n.summary
            FROM memory_nodes n
            JOIN memory_fts fts ON n.id = fts.rowid
            WHERE memory_fts MATCH ?
            ORDER BY bm25(memory_fts)
            LIMIT 10
        """, (search_term,))
        sqlite_results = len(cursor.fetchall())
        sqlite_time = (time.time() - start) * 1000
        conn.close()
        
        # LadybugDB search (CONTAINS)
        db = lb.Database(str(self.ladybug_path))
        lb_conn = lb.Connection(db)
        start = time.time()
        safe_term = search_term.replace("'", "\\'")
        result = lb_conn.execute(f"""
            MATCH (n:MemoryNode)
            WHERE n.text CONTAINS '{safe_term}'
            RETURN n.id, n.who, n.layer, n.summary
            LIMIT 10
        """)
        ladybug_results = len(list(result))
        ladybug_time = (time.time() - start) * 1000
        
        speedup = sqlite_time / ladybug_time if ladybug_time > 0 else float('inf')
        
        return BenchmarkResult(
            query_name=f"Text search: '{search_term}'",
            sqlite_time_ms=sqlite_time,
            ladybug_time_ms=ladybug_time,
            sqlite_results=sqlite_results,
            ladybug_results=ladybug_results,
            speedup=speedup
        )
    
    def benchmark_multi_hop(self) -> BenchmarkResult:
        """Compare multi-hop query performance (turn chains)"""
        
        # SQLite - recursive query
        conn = sqlite3.connect(str(self.sqlite_path))
        
        # First get a node with turns
        cursor = conn.execute("""
            SELECT input_node_id FROM memory_turns 
            WHERE input_node_id IS NOT NULL 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return BenchmarkResult("Multi-hop (turns)", 0, 0, 0, 0, 0)
        node_id = row[0]
        
        start = time.time()
        cursor = conn.execute("""
            SELECT t.turn_id, i.summary, c.summary, o.summary
            FROM memory_turns t
            LEFT JOIN memory_nodes i ON t.input_node_id = i.id
            LEFT JOIN memory_nodes c ON t.contemplation_node_id = c.id
            LEFT JOIN memory_nodes o ON t.output_node_id = o.id
            WHERE t.input_node_id = ?
        """, (node_id,))
        sqlite_results = len(cursor.fetchall())
        sqlite_time = (time.time() - start) * 1000
        conn.close()
        
        # LadybugDB - pattern match
        db = lb.Database(str(self.ladybug_path))
        lb_conn = lb.Connection(db)
        start = time.time()
        result = lb_conn.execute(f"""
            MATCH (t:Turn)-[:has_input]->(input:MemoryNode {{id: {node_id}}})
            OPTIONAL MATCH (t)-[:has_contemplation]->(think:MemoryNode)
            OPTIONAL MATCH (t)-[:has_output]->(output:MemoryNode)
            RETURN t.turn_id, input.summary, think.summary, output.summary
        """)
        ladybug_results = len(list(result))
        ladybug_time = (time.time() - start) * 1000
        
        speedup = sqlite_time / ladybug_time if ladybug_time > 0 else float('inf')
        
        return BenchmarkResult(
            query_name="Multi-hop (turn chains)",
            sqlite_time_ms=sqlite_time,
            ladybug_time_ms=ladybug_time,
            sqlite_results=sqlite_results,
            ladybug_results=ladybug_results,
            speedup=speedup
        )
    
    def benchmark_graph_traversal(self) -> BenchmarkResult:
        """Compare graph edge traversal"""
        
        conn = sqlite3.connect(str(self.sqlite_path))
        
        # Get a node with edges
        cursor = conn.execute("""
            SELECT source_id FROM memory_edges LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return BenchmarkResult("Graph traversal", 0, 0, 0, 0, 0)
        node_id = row[0]
        
        # SQLite - JOIN query
        start = time.time()
        cursor = conn.execute("""
            SELECT e.target_id, e.relation, e.weight, n.summary
            FROM memory_edges e
            JOIN memory_nodes n ON e.target_id = n.id
            WHERE e.source_id = ?
            ORDER BY e.weight DESC
            LIMIT 10
        """, (node_id,))
        sqlite_results = len(cursor.fetchall())
        sqlite_time = (time.time() - start) * 1000
        conn.close()
        
        # LadybugDB - native graph
        db = lb.Database(str(self.ladybug_path))
        lb_conn = lb.Connection(db)
        start = time.time()
        result = lb_conn.execute(f"""
            MATCH (n:MemoryNode {{id: {node_id}}})-[r:relates_to]-(related:MemoryNode)
            RETURN related.id, r.relation, r.weight, related.summary
            ORDER BY r.weight DESC
            LIMIT 10
        """)
        ladybug_results = len(list(result))
        ladybug_time = (time.time() - start) * 1000
        
        speedup = sqlite_time / ladybug_time if ladybug_time > 0 else float('inf')
        
        return BenchmarkResult(
            query_name="Graph traversal (edges)",
            sqlite_time_ms=sqlite_time,
            ladybug_time_ms=ladybug_time,
            sqlite_results=sqlite_results,
            ladybug_results=ladybug_results,
            speedup=speedup
        )
    
    def benchmark_by_who(self, who: str = "David Dorta") -> BenchmarkResult:
        """Compare query by who"""
        
        # SQLite
        conn = sqlite3.connect(str(self.sqlite_path))
        start = time.time()
        cursor = conn.execute("""
            SELECT id, text, summary
            FROM memory_nodes
            WHERE who = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (who,))
        sqlite_results = len(cursor.fetchall())
        sqlite_time = (time.time() - start) * 1000
        conn.close()
        
        # LadybugDB
        db = lb.Database(str(self.ladybug_path))
        lb_conn = lb.Connection(db)
        start = time.time()
        safe_who = who.replace("'", "\\'")
        result = lb_conn.execute(f"""
            MATCH (n:MemoryNode {{who: '{safe_who}'}})
            RETURN n.id, n.text, n.summary
            ORDER BY n.timestamp DESC
            LIMIT 10
        """)
        ladybug_results = len(list(result))
        ladybug_time = (time.time() - start) * 1000
        
        speedup = sqlite_time / ladybug_time if ladybug_time > 0 else float('inf')
        
        return BenchmarkResult(
            query_name=f"Query by who: '{who}'",
            sqlite_time_ms=sqlite_time,
            ladybug_time_ms=ladybug_time,
            sqlite_results=sqlite_results,
            ladybug_results=ladybug_results,
            speedup=speedup
        )
    
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmarks and return results"""
        results = []
        
        print("\n🔬 Running benchmarks...\n")
        
        print("  1. Text search...")
        results.append(self.benchmark_text_search("memory"))
        
        print("  2. Query by who...")
        results.append(self.benchmark_by_who("David Dorta"))
        
        print("  3. Multi-hop queries...")
        results.append(self.benchmark_multi_hop())
        
        print("  4. Graph traversal...")
        results.append(self.benchmark_graph_traversal())
        
        return results


def print_comparison(results: List[BenchmarkResult]):
    """Print benchmark comparison table"""
    print("\n" + "=" * 90)
    print("📊 SQLite vs LadybugDB Performance Comparison")
    print("=" * 90)
    print(f"{'Query Type':<30} {'SQLite (ms)':<15} {'LadybugDB (ms)':<18} {'Results':<12} {'Speedup':<10}")
    print("-" * 90)
    
    for r in results:
        winner = "🚀" if r.speedup > 1 else ("🐢" if r.speedup < 1 else "⚖️")
        print(f"{r.query_name:<30} {r.sqlite_time_ms:<15.2f} {r.ladybug_time_ms:<18.2f} "
              f"{r.sqlite_results}/{r.ladybug_results:<10} {r.speedup:.2f}x {winner}")
    
    print("=" * 90)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NIMA LadybugDB Parallel Implementation")
    parser.add_argument("--migrate", action="store_true", help="Migrate data from SQLite to LadybugDB")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--query", type=str, help="Run a test query")
    
    args = parser.parse_args()
    
    ladybug = NIMALadybugDB()
    
    if args.migrate:
        print("🚀 Starting migration to LadybugDB...")
        ladybug.initialize()
        ladybug.migrate_from_sqlite()
        
    if args.benchmark:
        if not ladybug.db_path.exists():
            print("❌ LadybugDB not found. Run --migrate first.")
            return
        bench = BenchmarkComparison()
        results = bench.run_all_benchmarks()
        print_comparison(results)
        
    if args.query:
        ladybug.db = lb.Database(str(ladybug.db_path))
        ladybug.conn = lb.Connection(ladybug.db)
        print(f"\n🔍 Query: '{args.query}'")
        results = ladybug.query_by_text(args.query)
        for row in results[:5]:
            print(f"  - {row}")


if __name__ == "__main__":
    main()
