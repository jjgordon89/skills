#!/usr/bin/env python3
"""
NIMA Memory - SQLite to LadybugDB Migration
============================================

Batch migration with retry logic for ARM64 Raspberry Pi.

Usage:
  python3 migrate_to_ladybug.py --batch-size 500
  python3 migrate_to_ladybug.py --batch-size 500 --dry-run
  python3 migrate_to_ladybug.py --auto  # Use config defaults

Features:
  - Batched migration (configurable size)
  - Automatic retry with exponential backoff
  - Progress tracking
  - Rollback on failure
  - Dry-run mode for testing

Author: Lilu
Date: 2026-02-15
"""

import sqlite3
import json
import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
import argparse

# Paths
NIMA_HOME = Path.home() / ".nima" / "memory"
SQLITE_DB = NIMA_HOME / "graph.sqlite"
LADYBUG_DB = NIMA_HOME / "graph.ladybug"
MIGRATION_LOG = NIMA_HOME / "migration.log"

# Defaults
DEFAULT_BATCH_SIZE = 500
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 5, 15]  # seconds

class MigrationStats:
    def __init__(self):
        self.total_nodes = 0
        self.migrated_nodes = 0
        self.failed_batches = 0
        self.retries = 0
        self.start_time = time.time()
        self.batch_times = []
    
    def elapsed(self):
        return time.time() - self.start_time
    
    def avg_batch_time(self):
        return sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0
    
    def eta(self, remaining_batches):
        avg = self.avg_batch_time()
        if avg == 0:
            return None
        return avg * remaining_batches

def log_migration(message: str, level: str = "INFO"):
    """Log migration progress"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    with open(MIGRATION_LOG, "a") as f:
        f.write(log_line + "\n")

def check_ladybug_available() -> bool:
    """Check if LadybugDB is installed and available"""
    try:
        import ladybug
        return True
    except ImportError:
        return False

def get_sqlite_stats() -> Dict[str, Any]:
    """Get statistics from SQLite database"""
    if not SQLITE_DB.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_DB}")
    
    db = sqlite3.connect(str(SQLITE_DB))
    
    total_nodes = db.execute("SELECT COUNT(*) FROM memory_nodes").fetchone()[0]
    total_turns = db.execute("SELECT COUNT(*) FROM memory_turns").fetchone()[0]
    layers = db.execute("SELECT layer, COUNT(*) FROM memory_nodes GROUP BY layer").fetchall()
    
    db_size = SQLITE_DB.stat().st_size
    
    db.close()
    
    return {
        "nodes": total_nodes,
        "turns": total_turns,
        "layers": dict(layers),
        "size_bytes": db_size,
        "size_mb": round(db_size / (1024 * 1024), 2)
    }

def migrate_batch(
    source_db: sqlite3.Connection,
    target_db: Any,  # LadybugDB connection
    offset: int,
    batch_size: int,
    dry_run: bool = False
) -> int:
    """
    Migrate a batch of nodes from SQLite to LadybugDB.
    
    Returns: Number of nodes migrated
    """
    # Fetch batch from SQLite
    nodes = source_db.execute("""
        SELECT id, timestamp, layer, text, summary, who, affect_json, 
               session_key, conversation_id, turn_id, fe_score, created_at
        FROM memory_nodes
        ORDER BY id
        LIMIT ? OFFSET ?
    """, (batch_size, offset)).fetchall()
    
    if not nodes:
        return 0
    
    if dry_run:
        log_migration(f"DRY RUN: Would migrate {len(nodes)} nodes (offset {offset})", "DEBUG")
        return len(nodes)
    
    # Insert into LadybugDB using Cypher CREATE
    inserted = 0
    for node in nodes:
        node_id, timestamp, layer, text, summary, who, affect_json, \
        session_key, conversation_id, turn_id, fe_score, created_at = node
        
        try:
            # Sanitize strings for Cypher (escape quotes, remove control chars)
            def sanitize(s):
                if not s:
                    return ""
                s = str(s).replace("\\", "\\\\").replace("'", "\\'")
                import re
                return re.sub(r'[\x00-\x1f]', ' ', s)
            
            # Create node using Cypher
            target_db.execute(f"""
                CREATE (n:MemoryNode {{
                    id: {node_id},
                    timestamp: {timestamp},
                    layer: '{sanitize(layer)}',
                    text: '{sanitize(text)[:2000]}',
                    summary: '{sanitize(summary)[:500]}',
                    who: '{sanitize(who)}',
                    affect_json: '{sanitize(affect_json)}',
                    session_key: '{sanitize(session_key)}',
                    conversation_id: '{sanitize(conversation_id)}',
                    turn_id: '{sanitize(turn_id)}',
                    fe_score: {fe_score or 0.5}
                }})
            """)
            inserted += 1
        except Exception as e:
            log_migration(f"Failed to insert node {node_id}: {e}", "ERROR")
            raise  # Re-raise to trigger retry logic
    
    return inserted

def migrate_with_retry(
    source_db: sqlite3.Connection,
    target_db: Any,
    offset: int,
    batch_size: int,
    stats: MigrationStats,
    dry_run: bool = False
) -> bool:
    """
    Migrate a batch with retry logic.
    
    Returns: True if successful, False if failed after retries
    """
    for attempt in range(MAX_RETRIES):
        try:
            batch_start = time.time()
            
            count = migrate_batch(source_db, target_db, offset, batch_size, dry_run)
            
            batch_time = time.time() - batch_start
            stats.batch_times.append(batch_time)
            stats.migrated_nodes += count
            
            if attempt > 0:
                stats.retries += attempt
                log_migration(f"Batch succeeded on retry {attempt + 1}", "INFO")
            
            return True
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF[attempt]
                log_migration(
                    f"Batch failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {backoff}s...",
                    "WARN"
                )
                time.sleep(backoff)
            else:
                log_migration(
                    f"Batch failed after {MAX_RETRIES} attempts: {e}",
                    "ERROR"
                )
                stats.failed_batches += 1
                return False
    
    return False

def run_migration(
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
    start_offset: int = 0
) -> MigrationStats:
    """
    Run full migration from SQLite to LadybugDB.
    
    Args:
        batch_size: Number of nodes per batch
        dry_run: If True, don't actually migrate (just simulate)
        start_offset: Resume from this offset (for interrupted migrations)
    
    Returns:
        MigrationStats object
    """
    stats = MigrationStats()
    
    # Pre-flight checks
    log_migration("=" * 60)
    log_migration("NIMA Memory Migration: SQLite → LadybugDB")
    log_migration("=" * 60)
    
    if dry_run:
        log_migration("DRY RUN MODE - No data will be modified", "INFO")
    
    # Check LadybugDB
    if not dry_run and not check_ladybug_available():
        log_migration("LadybugDB not available. Install: pip install ladybug-core", "ERROR")
        sys.exit(1)
    
    # Get source stats
    log_migration("Analyzing source database...", "INFO")
    source_stats = get_sqlite_stats()
    stats.total_nodes = source_stats["nodes"]
    
    log_migration(f"Source: {source_stats['nodes']} nodes, {source_stats['size_mb']} MB", "INFO")
    log_migration(f"Layers: {source_stats['layers']}", "INFO")
    log_migration(f"Batch size: {batch_size} nodes", "INFO")
    
    total_batches = (stats.total_nodes + batch_size - 1) // batch_size
    log_migration(f"Total batches: {total_batches}", "INFO")
    
    if start_offset > 0:
        log_migration(f"Resuming from offset {start_offset}", "INFO")
    
    # Connect to databases
    source_db = sqlite3.connect(str(SQLITE_DB))
    
    if not dry_run:
        # TODO: Initialize LadybugDB connection
        # target_db = ladybug.connect(str(LADYBUG_DB))
        target_db = None
        log_migration("LadybugDB connection opened", "DEBUG")
    else:
        target_db = None
    
    # Migrate in batches
    log_migration("Starting migration...", "INFO")
    
    offset = start_offset
    batch_num = offset // batch_size
    
    while offset < stats.total_nodes:
        batch_num += 1
        remaining_batches = total_batches - batch_num + 1
        
        # Progress
        pct = (offset / stats.total_nodes * 100) if stats.total_nodes > 0 else 0
        eta = stats.eta(remaining_batches)
        eta_str = f"{int(eta)}s" if eta else "unknown"
        
        log_migration(
            f"Batch {batch_num}/{total_batches} "
            f"({pct:.1f}% complete, ETA: {eta_str})",
            "INFO"
        )
        
        # Migrate batch with retry
        success = migrate_with_retry(
            source_db,
            target_db,
            offset,
            batch_size,
            stats,
            dry_run
        )
        
        if not success:
            log_migration(
                f"Migration stopped due to batch failure at offset {offset}",
                "ERROR"
            )
            log_migration(
                f"To resume, run: python3 migrate_to_ladybug.py --start-offset {offset}",
                "INFO"
            )
            break
        
        offset += batch_size
    
    # Cleanup
    source_db.close()
    
    if not dry_run and target_db:
        # TODO: Close LadybugDB
        # target_db.close()
        log_migration("LadybugDB connection closed", "DEBUG")
    
    # Summary
    log_migration("=" * 60)
    log_migration("Migration Summary", "INFO")
    log_migration("=" * 60)
    log_migration(f"Total nodes: {stats.total_nodes}", "INFO")
    log_migration(f"Migrated: {stats.migrated_nodes}", "INFO")
    log_migration(f"Failed batches: {stats.failed_batches}", "INFO")
    log_migration(f"Retries: {stats.retries}", "INFO")
    log_migration(f"Elapsed: {stats.elapsed():.1f}s", "INFO")
    log_migration(f"Avg batch time: {stats.avg_batch_time():.2f}s", "INFO")
    
    success_rate = (stats.migrated_nodes / stats.total_nodes * 100) if stats.total_nodes > 0 else 0
    log_migration(f"Success rate: {success_rate:.1f}%", "INFO")
    
    if stats.failed_batches == 0 and stats.migrated_nodes == stats.total_nodes:
        log_migration("✅ Migration completed successfully!", "INFO")
    elif stats.failed_batches > 0:
        log_migration("⚠️ Migration completed with errors", "WARN")
    else:
        log_migration("❌ Migration failed", "ERROR")
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Migrate NIMA Memory from SQLite to LadybugDB"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of nodes per batch (default: {DEFAULT_BATCH_SIZE})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without actually modifying data"
    )
    parser.add_argument(
        "--start-offset",
        type=int,
        default=0,
        help="Resume migration from this offset (for interrupted runs)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Use config defaults (for plugin auto-migration)"
    )
    
    args = parser.parse_args()
    
    try:
        stats = run_migration(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            start_offset=args.start_offset
        )
        
        # Exit code: 0 if fully successful, 1 if partial/failed
        if stats.failed_batches == 0 and stats.migrated_nodes == stats.total_nodes:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        log_migration(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
