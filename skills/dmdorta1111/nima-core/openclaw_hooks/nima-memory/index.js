/**
 * NIMA Unified Memory Hook
 * ========================
 * Captures ALL three memory layers from a single agent_end hook:
 *   1. INPUT  - what was said to the agent (user message)
 *   2. CONTEMPLATION - the agent's thinking/reasoning (strange loop)
 *   3. OUTPUT - what the agent responded
 *
 * Each layer is bound to the current affect state at time of capture.
 * Memories are stored to a SQLite graph for relationship-aware recall.
 *
 * Replaces: nima-capture hook (now redundant)
 * Requires: nima-affect plugin (for affect state)
 *
 * Hook Events:
 *   agent_end → extract 3 layers from messages snapshot, bind affect, store
 *
 * Author: David Dorta + Lilu
 * Date: 2026-02-13
 * Updated: 2026-02-13 (Security & correctness fixes)
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, unlinkSync } from "node:fs";
import { join, dirname } from "node:path";
import { execFileSync } from "node:child_process";
import os from "node:os";
import { randomBytes } from "node:crypto";

// =============================================================================
// CONFIGURATION
// =============================================================================

const NIMA_HOME = join(os.homedir(), ".nima");
const MEMORY_DIR = join(NIMA_HOME, "memory");
const GRAPH_DB = join(MEMORY_DIR, "graph.sqlite");
const AFFECT_DIR = join(NIMA_HOME, "affect", "conversations");

// Content length limits (security - prevent DoS via oversized content)
const MAX_TEXT_LENGTH = 3000;
const MAX_SUMMARY_LENGTH = 300;

// Max lengths for compressed summaries (Layer 2)
const MAX_SUMMARY_INPUT = 80; // ~10-20 tokens
const MAX_THINKING_SUMMARY = 120;
const MAX_OUTPUT_SUMMARY = 100;

// =============================================================================
// MEMORY RECORD
// =============================================================================

/**
 * Truncate text to max length (security boundary).
 */
function truncateText(text, maxLen) {
  if (!text) return "";
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen);
}

/**
 * Calculate Free Energy (FE) score for a memory.
 * FE = prediction_error = how surprising/novel an experience is.
 * 
 * Factors:
 *   - Affect variance (emotional dynamism)
 *   - Text length (very short = likely monotonous)
 *   - Repetition detection (similar to recent memories)
 * 
 * Returns: 0.0 (monotonous) to 1.0 (highly novel)
 */
function calculateFEScore(input, contemplation, output, affect) {
  let fe = 0.5; // Default: moderately novel
  
  // Factor 1: Affect variance (emotional dynamism)
  if (affect && Object.keys(affect).length > 0) {
    const values = Object.values(affect);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const variance = max - min;
    // High variance = more novel experience
    fe += variance * 0.3;
  }
  
  // Factor 2: Content richness
  const inputLen = (input?.text || "").length;
  const thinkLen = (contemplation?.text || "").length;
  const outLen = (output?.text || "").length;
  
  // Very short exchanges are likely routine
  if (inputLen < 20 && outLen < 50) {
    fe -= 0.2; // Likely short acknowledgment
  }
  if (thinkLen > 100) {
    fe += 0.1; // Agent did real thinking
  }
  
  // Factor 3: Check for monotonous patterns
  const inputSummary = (input?.summary || "").toLowerCase().trim();
  const monotonousPatterns = [
    /^heartbeat_ok$/i,
    /^heartbeat check$/i,
    /^hygiene check$/i,
    /^ok$/i,
    /^yes$/i,
    /^no$/i,
    /^sure$/i,
    /^got it$/i,
    /^thanks$/i,
    /^thank you$/i,
    /gateway.?restart/i,
  ];
  for (const pattern of monotonousPatterns) {
    if (pattern.test(inputSummary)) {
      fe -= 0.4;
      break;
    }
  }
  
  // Clamp to [0, 1]
  return Math.max(0, Math.min(1, fe));
}

/**
 * Calculate FE score with configurable weights.
 * Uses config values for tuning without code changes.
 */
function calculateFEScoreWithConfig(input, contemplation, output, affect, config) {
  let fe = 0.5; // Default: moderately novel
  
  // Factor 1: Affect variance (emotional dynamism)
  if (affect && Object.keys(affect).length > 0) {
    const values = Object.values(affect);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const variance = max - min;
    // High variance = more novel experience
    fe += variance * config.affectVarianceWeight;
  }
  
  // Factor 2: Content richness
  const inputLen = (input?.text || "").length;
  const thinkLen = (contemplation?.text || "").length;
  const outLen = (output?.text || "").length;
  
  // Very short exchanges are likely routine
  if (inputLen < 20 && outLen < 50) {
    fe -= config.routinePenalty;
  }
  if (thinkLen > 100) {
    fe += config.thinkingBoost;
  }
  
  // Factor 3: Check for monotonous patterns
  const inputSummary = (input?.summary || "").toLowerCase().trim();
  const monotonousPatterns = [
    /^heartbeat_ok$/i,
    /^heartbeat check$/i,
    /^hygiene check$/i,
    /^ok$/i,
    /^yes$/i,
    /^no$/i,
    /^sure$/i,
    /^got it$/i,
    /^thanks$/i,
    /^thank you$/i,
    /gateway.?restart/i,
  ];
  for (const pattern of monotonousPatterns) {
    if (pattern.test(inputSummary)) {
      fe -= config.monotonousPenalty;
      break;
    }
  }
  
  // Clamp to [0, 1]
  return Math.max(0, Math.min(1, fe));
}

/**
 * A single memory record with all three layers + affect binding.
 */
function createMemoryRecord(input, contemplation, output, affect, metadata) {
  return {
    timestamp: Date.now(),
    layers: {
      input: {
        text: truncateText(input.text || "", MAX_TEXT_LENGTH),
        summary: summarize(input.text, MAX_SUMMARY_INPUT),
        who: truncateText(input.who || "unknown", 100),
      },
      contemplation: {
        text: truncateText(contemplation.text || "", MAX_TEXT_LENGTH),
        summary: summarize(contemplation.text, MAX_THINKING_SUMMARY),
      },
      output: {
        text: truncateText(output.text || "", MAX_TEXT_LENGTH),
        summary: summarize(output.text, MAX_OUTPUT_SUMMARY),
      },
    },
    affect: affect ? { ...affect } : null,
    metadata: {
      sessionKey: truncateText(metadata.sessionKey || "", 200),
      conversationId: truncateText(metadata.conversationId || "", 200),
      agentId: truncateText(metadata.agentId || "", 100),
      durationMs: metadata.durationMs || 0,
      feScore: metadata.feScore || 0.5,
    },
  };
}

/**
 * Compress text to a short summary (Layer 2).
 * Simple truncation with ellipsis - can be replaced with LLM summarization later.
 * Enforces MAX_SUMMARY_LENGTH limit.
 */
function summarize(text, maxLen) {
  if (!text) return "";
  // Enforce global summary length limit
  const effectiveMax = Math.min(maxLen, MAX_SUMMARY_LENGTH);
  // Strip newlines, collapse whitespace
  const clean = text.replace(/\n+/g, " ").replace(/\s+/g, " ").trim();
  if (clean.length <= effectiveMax) return clean;
  return clean.substring(0, effectiveMax - 3) + "...";
}

// =============================================================================
// AFFECT STATE READER
// =============================================================================

function readAffectState(conversationId, identityName) {
  try {
    // Try conversation-specific state first
    if (conversationId) {
      const convPath = join(AFFECT_DIR, `${identityName}_${conversationId}.json`);
      if (existsSync(convPath)) {
        const data = JSON.parse(readFileSync(convPath, "utf-8"));
        return data.current?.named || null;
      }
    }
    // Fall back to shared state
    const sharedPath = join(NIMA_HOME, "affect", `affect_state_${identityName}.json`);
    if (existsSync(sharedPath)) {
      const data = JSON.parse(readFileSync(sharedPath, "utf-8"));
      return data.current?.named || null;
    }
  } catch (err) {
    console.error(`[nima-memory] Failed to read affect state: ${err.message}`);
  }
  return null;
}

// =============================================================================
// INPUT TEXT CLEANING
// =============================================================================

/**
 * Strip injected context blocks from input text.
 * Removes:
 *   - [NIMA RECALL - ...] blocks (injected by recall hooks)
 *   - 🎭 AFFECT STATE blocks (injected by affect plugin)
 *   - [message_id: ...] trailers
 *   - Heartbeat instruction text (system mechanics, not user message)
 *
 * This prevents feedback loops where recall output gets stored as memory input.
 */
function cleanInputText(text) {
  if (!text || typeof text !== "string") return "";

  let cleaned = text;

  // Remove NIMA RECALL blocks (multiline, non-greedy)
  cleaned = cleaned.replace(/\[NIMA RECALL[^\]]*\][\s\S]*?\[End recall[^\]]*\]\s*/gi, "");

  // Remove 🎭 AFFECT STATE blocks (usually single-line or short multi-line)
  cleaned = cleaned.replace(/🎭\s*AFFECT STATE[^\n]*(\n[^\n]*){0,3}\n*/g, "");

  // Remove [Dynamic affect... line
  cleaned = cleaned.replace(/\[Dynamic affect[^\]]*\]\s*/gi, "");

  // Remove [message_id: ...] trailers
  cleaned = cleaned.replace(/\[message_id:\s*[^\]]+\]\s*/gi, "");

  // Remove heartbeat instruction text (system mechanics)
  cleaned = cleaned.replace(/Read HEARTBEAT\.md if it exists[^\n]*\n*/gi, "");

  // Remove multiple consecutive blank lines
  cleaned = cleaned.replace(/\n{3,}/g, "\n\n");

  return cleaned.trim();
}

/**
 * Check if a contemplation is just heartbeat mechanics (noise).
 * These repeated internal thoughts aren't meaningful experiences.
 */
function isHeartbeatNoise(text) {
  if (!text || typeof text !== "string") return false;

  const noisePatterns = [
    /heartbeat (check|poll|cycle)/i,
    /hygiene check/i,
    /HEARTBEAT_OK/i,
    /run.*hygiene/i,
    /another heartbeat/i,
    /sending another heartbeat/i,
  ];

  return noisePatterns.some(p => p.test(text));
}

/**
 * Check if content is system noise that shouldn't be stored as memory.
 * Filters out gateway restarts, doctor hints, session metadata, etc.
 */
function isSystemNoise(text) {
  if (!text || typeof text !== "string") return false;

  const noisePatterns = [
    // Gateway/system messages
    /^GatewayRestart:/i,
    /"kind":\s*"restart"/i,
    /"status":\s*"ok"/i,
    /doctorHint/i,
    /Run: openclaw doctor/i,
    
    // Session/channel metadata
    /"sessionKey":/i,
    /"deliveryContext":/i,
    /"accountId":/i,
    /"channel":/i,
    
    // Queue/compaction markers (the prefix, not user content after)
    /^\[Queued messages while agent was busy\]/i,
    /^---\s*Queue/i,
    /^Queued #\d+$/i,
    
    // Raw JSON that looks like system output
    /^\{[\s\S]*"kind":/i,
    /^\{[\s\S]*"stats":/i,
    
    // Compaction messages
    /Pre-compaction memory flush/i,
    /HEARTBEAT_OK/i,
    /NO_REPLY/i,
    
    // Empty or too short after cleaning
    /^\.+$/,  // Just dots
  ];

  return noisePatterns.some(p => p.test(text));
}

/**
 * Check if a memory would be low quality (not worth storing).
 * Uses FE score heuristic and content quality checks.
 */
function isLowQualityMemory(input, output, contemplation) {
  // Skip if input is system noise
  if (isSystemNoise(input)) return true;
  
  // Skip if output is system noise (gateway restarts, etc.)
  if (isSystemNoise(output)) return true;
  
  // Skip if both input and output are empty
  if (!input && !output) return true;
  
  // Skip very short exchanges (likely noise)
  const inputLen = (input || "").trim().length;
  const outputLen = (output || "").trim().length;
  if (inputLen < 5 && outputLen < 20) return true;
  
  return false;
}

// =============================================================================
// MESSAGE EXTRACTION
// =============================================================================

/**
 * Extract the three layers from the messages snapshot.
 * Returns { input, contemplation, output }
 */
function extractLayers(messages) {
  if (!messages || !Array.isArray(messages) || messages.length === 0) {
    return null;
  }

  // Find the last user message (INPUT)
  let lastUserMsg = null;
  let lastAssistantMsg = null;

  // Walk backwards to find the last user→assistant pair
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (!lastAssistantMsg && msg.role === "assistant") {
      lastAssistantMsg = msg;
    }
    if (lastAssistantMsg && msg.role === "user") {
      lastUserMsg = msg;
      break;
    }
  }

  if (!lastAssistantMsg) return null;

  // Extract input text
  let inputText = "";
  let inputWho = "unknown";
  if (lastUserMsg) {
    const content = lastUserMsg.content;
    if (typeof content === "string") {
      inputText = content;
    } else if (Array.isArray(content)) {
      inputText = content
        .filter((c) => c.type === "text")
        .map((c) => c.text)
        .join("\n");
    }
    // Try to extract sender from message format (expanded channel support)
    const senderMatch = inputText.match(/\[(?:Telegram|Discord|Signal|SMS|Slack|Matrix|WhatsApp|iMessage|Email)\s+(.+?)\s+(?:id|ID|Id):/);
    if (senderMatch) inputWho = senderMatch[1];

    // Clean injected context blocks (NIMA RECALL, AFFECT STATE) to prevent feedback loops
    inputText = cleanInputText(inputText);
  }

  // Extract thinking (CONTEMPLATION) and response (OUTPUT)
  let thinkingText = "";
  let outputText = "";
  const content = lastAssistantMsg.content;
  
  if (typeof content === "string") {
    outputText = content;
  } else if (Array.isArray(content)) {
    for (const block of content) {
      if (block.type === "thinking" && block.thinking) {
        thinkingText += block.thinking + "\n";
      } else if (block.type === "text" && block.text) {
        outputText += block.text + "\n";
      }
    }
  }

  // Filter out heartbeat noise from contemplation
  // These are repetitive system mechanics, not meaningful experiences
  if (isHeartbeatNoise(thinkingText)) {
    thinkingText = "";  // Don't store heartbeat mechanics as contemplation
  }

  return {
    input: { text: inputText.trim(), who: inputWho },
    contemplation: { text: thinkingText.trim() },
    output: { text: outputText.trim() },
  };
}

// =============================================================================
// STORAGE (SQLite Graph)
// =============================================================================

/**
 * Initialize SQLite database for graph storage.
 * Creates tables if they don't exist.
 *
 * SECURITY FIX: Database path passed as argument, not embedded in code.
 * CORRECTNESS FIX: Table existence checked in Python (no race condition).
 * FEATURE: FTS5 virtual table and triggers for full-text search.
 */
function initDatabase() {
  ensureDir(MEMORY_DIR);

  // Python script with parameterized DB path (no injection)
  const initSQL = `
import sqlite3, sys

# Read DB path from argument (no injection risk)
db_path = sys.argv[1] if len(sys.argv) > 1 else None
if not db_path:
    print("error:no_db_path", file=sys.stderr)
    sys.exit(1)

try:
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")

    # Nodes table - each memory record
    db.execute("""
    CREATE TABLE IF NOT EXISTS memory_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        layer TEXT NOT NULL CHECK(layer IN ('input', 'contemplation', 'output', 'legacy_vsa')),
        text TEXT NOT NULL,
        summary TEXT NOT NULL,
        who TEXT DEFAULT '',
        affect_json TEXT DEFAULT '{}',
        session_key TEXT DEFAULT '',
        conversation_id TEXT DEFAULT '',
        turn_id TEXT DEFAULT '',
        fe_score REAL DEFAULT 0.5,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Edges table - relationships between nodes
    db.execute("""
    CREATE TABLE IF NOT EXISTS memory_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        target_id INTEGER NOT NULL,
        relation TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        FOREIGN KEY (source_id) REFERENCES memory_nodes(id),
        FOREIGN KEY (target_id) REFERENCES memory_nodes(id)
    )""")

    # Turn groups - links the 3 layers of a single conversational turn
    db.execute("""
    CREATE TABLE IF NOT EXISTS memory_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turn_id TEXT UNIQUE NOT NULL,
        input_node_id INTEGER,
        contemplation_node_id INTEGER,
        output_node_id INTEGER,
        timestamp INTEGER NOT NULL,
        affect_json TEXT DEFAULT '{}',
        FOREIGN KEY (input_node_id) REFERENCES memory_nodes(id),
        FOREIGN KEY (contemplation_node_id) REFERENCES memory_nodes(id),
        FOREIGN KEY (output_node_id) REFERENCES memory_nodes(id)
    )""")

    # FTS5 virtual table for full-text search
    db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
        text, summary, who, layer,
        content=memory_nodes,
        content_rowid=id
    )""")

    # Triggers to keep FTS5 in sync with memory_nodes
    db.execute("""
    CREATE TRIGGER IF NOT EXISTS memory_nodes_ai AFTER INSERT ON memory_nodes BEGIN
        INSERT INTO memory_fts(rowid, text, summary, who, layer)
        VALUES (new.id, new.text, new.summary, new.who, new.layer);
    END""")

    db.execute("""
    CREATE TRIGGER IF NOT EXISTS memory_nodes_ad AFTER DELETE ON memory_nodes BEGIN
        INSERT INTO memory_fts(memory_fts, rowid, text, summary, who, layer)
        VALUES ('delete', old.id, old.text, old.summary, old.who, old.layer);
    END""")

    db.execute("""
    CREATE TRIGGER IF NOT EXISTS memory_nodes_au AFTER UPDATE ON memory_nodes BEGIN
        INSERT INTO memory_fts(memory_fts, rowid, text, summary, who, layer)
        VALUES ('delete', old.id, old.text, old.summary, old.who, old.layer);
        INSERT INTO memory_fts(rowid, text, summary, who, layer)
        VALUES (new.id, new.text, new.summary, new.who, new.layer);
    END""")

    # Indexes for fast lookup
    db.execute("CREATE INDEX IF NOT EXISTS idx_nodes_timestamp ON memory_nodes(timestamp)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_nodes_layer ON memory_nodes(layer)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_nodes_who ON memory_nodes(who)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_nodes_turn ON memory_nodes(turn_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON memory_edges(source_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON memory_edges(target_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_turns_timestamp ON memory_turns(timestamp)")
    
    # Add fe_score column if it doesn't exist (migration)
    try:
        db.execute("ALTER TABLE memory_nodes ADD COLUMN fe_score REAL DEFAULT 0.5")
    except sqlite3.OperationalError:
        pass  # Column already exists

    db.commit()
    db.close()
    print("ok")

except Exception as e:
    print(f"error:{str(e)}", file=sys.stderr)
    sys.exit(1)
`;

  try {
    const result = execFileSync("python3", ["-c", initSQL, GRAPH_DB], {
      timeout: 5000,
      encoding: "utf-8",
    });
    return result.trim() === "ok";
  } catch (err) {
    console.error(`[nima-memory] DB init failed: ${err.message}`);
    if (err.stderr) {
      console.error(`[nima-memory] Python error: ${err.stderr}`);
    }
    return false;
  }
}

/**
 * Health check: Verify database connectivity and return stats.
 * 
 * Returns:
 *   { ok: true, stats: { nodes, turns, layers, ... } }
 *   { ok: false, error: "..." }
 */
function healthCheck() {
  if (!existsSync(GRAPH_DB)) {
    return { ok: false, error: "Database file not found", path: GRAPH_DB };
  }

  const healthSQL = `
import sqlite3, sys, json

db_path = sys.argv[1] if len(sys.argv) > 1 else None
if not db_path:
    print(json.dumps({"ok": False, "error": "no_db_path"}))
    sys.exit(1)

try:
    db = sqlite3.connect(db_path, timeout=2.0)
    
    # Check table exists
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    
    if 'memory_nodes' not in table_names:
        print(json.dumps({"ok": False, "error": "memory_nodes table missing"}))
        sys.exit(1)
    
    # Get stats
    node_count = db.execute("SELECT COUNT(*) FROM memory_nodes").fetchone()[0]
    turn_count = db.execute("SELECT COUNT(*) FROM memory_turns").fetchone()[0]
    
    # Layer distribution
    layers = db.execute("SELECT layer, COUNT(*) FROM memory_nodes GROUP BY layer").fetchall()
    layer_dist = {layer: count for layer, count in layers}
    
    # Recent activity (last 24h)
    now_ts = int(__import__('time').time() * 1000)
    day_ago = now_ts - (24 * 60 * 60 * 1000)
    recent_count = db.execute("SELECT COUNT(*) FROM memory_nodes WHERE timestamp > ?", (day_ago,)).fetchone()[0]
    
    # Database file size
    import os
    db_size = os.path.getsize(db_path)
    
    result = {
        "ok": True,
        "stats": {
            "nodes": node_count,
            "turns": turn_count,
            "layers": layer_dist,
            "recent_24h": recent_count,
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / (1024 * 1024), 2),
            "tables": table_names
        }
    }
    
    db.close()
    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"ok": False, "error": str(e)}))
    sys.exit(1)
`;

  try {
    const result = execFileSync("python3", ["-c", healthSQL, GRAPH_DB], {
      timeout: 3000,
      encoding: "utf-8",
    });
    return JSON.parse(result);
  } catch (err) {
    return {
      ok: false,
      error: err.message,
      stderr: err.stderr?.substring(0, 200),
    };
  }
}

/**
 * Store a memory record to the SQLite graph.
 *
 * SECURITY FIX: Data passed via JSON temp file, not embedded in Python code.
 * CORRECTNESS FIX: All inserts wrapped in transaction (atomicity).
 */
function storeMemory(record) {
  const turnId = `turn_${record.timestamp}`;

  // Prepare data structure to pass to Python
  const data = {
    db_path: GRAPH_DB,
    turn_id: turnId,
    timestamp: record.timestamp,
    affect_json: JSON.stringify(record.affect || {}),
    session_key: record.metadata.sessionKey,
    conversation_id: record.metadata.conversationId,
    fe_score: record.metadata.feScore || 0.5,
    input: {
      text: record.layers.input.text,
      summary: record.layers.input.summary,
      who: record.layers.input.who,
    },
    contemplation: {
      text: record.layers.contemplation.text,
      summary: record.layers.contemplation.summary,
    },
    output: {
      text: record.layers.output.text,
      summary: record.layers.output.summary,
    },
  };

  // Write data to temp file
  const tempFile = join(os.tmpdir(), `nima-memory-${randomBytes(8).toString("hex")}.json`);
  let success = false;

  try {
    writeFileSync(tempFile, JSON.stringify(data), "utf-8");

    // Python script reads from temp file (no injection risk)
    const storeSQL = `
import sqlite3, json, sys

# Read data from temp file
data_file = sys.argv[1] if len(sys.argv) > 1 else None
if not data_file:
    print("error:no_data_file", file=sys.stderr)
    sys.exit(1)

try:
    with open(data_file, 'r') as f:
        data = json.load(f)

    db = sqlite3.connect(data['db_path'])
    db.execute("PRAGMA journal_mode=WAL")

    # BEGIN TRANSACTION - all or nothing (atomicity fix)
    db.execute("BEGIN TRANSACTION")

    # Insert input node
    cur = db.execute(
        "INSERT INTO memory_nodes (timestamp, layer, text, summary, who, affect_json, session_key, conversation_id, turn_id, fe_score) VALUES (?, 'input', ?, ?, ?, ?, ?, ?, ?, ?)",
        (data['timestamp'], data['input']['text'], data['input']['summary'], data['input']['who'],
         data['affect_json'], data['session_key'], data['conversation_id'], data['turn_id'], data.get('fe_score', 0.5))
    )
    input_id = cur.lastrowid

    # Insert contemplation node
    cur = db.execute(
        "INSERT INTO memory_nodes (timestamp, layer, text, summary, who, affect_json, session_key, conversation_id, turn_id, fe_score) VALUES (?, 'contemplation', ?, ?, 'self', ?, ?, ?, ?, ?)",
        (data['timestamp'], data['contemplation']['text'], data['contemplation']['summary'],
         data['affect_json'], data['session_key'], data['conversation_id'], data['turn_id'], data.get('fe_score', 0.5))
    )
    contemp_id = cur.lastrowid

    # Insert output node
    cur = db.execute(
        "INSERT INTO memory_nodes (timestamp, layer, text, summary, who, affect_json, session_key, conversation_id, turn_id, fe_score) VALUES (?, 'output', ?, ?, 'self', ?, ?, ?, ?, ?)",
        (data['timestamp'], data['output']['text'], data['output']['summary'],
         data['affect_json'], data['session_key'], data['conversation_id'], data['turn_id'], data.get('fe_score', 0.5))
    )
    output_id = cur.lastrowid

    # Create edges: input → contemplation → output (temporal flow)
    db.execute("INSERT INTO memory_edges (source_id, target_id, relation, weight) VALUES (?, ?, 'triggered', 1.0)", (input_id, contemp_id))
    db.execute("INSERT INTO memory_edges (source_id, target_id, relation, weight) VALUES (?, ?, 'produced', 1.0)", (contemp_id, output_id))
    db.execute("INSERT INTO memory_edges (source_id, target_id, relation, weight) VALUES (?, ?, 'responded_to', 1.0)", (output_id, input_id))

    # Create turn group
    db.execute(
        "INSERT INTO memory_turns (turn_id, input_node_id, contemplation_node_id, output_node_id, timestamp, affect_json) VALUES (?, ?, ?, ?, ?, ?)",
        (data['turn_id'], input_id, contemp_id, output_id, data['timestamp'], data['affect_json'])
    )

    # COMMIT TRANSACTION - make all changes permanent
    db.commit()
    db.close()
    print(f"stored:{input_id},{contemp_id},{output_id}")

except Exception as e:
    print(f"error:{str(e)}", file=sys.stderr)
    sys.exit(1)
`;

    const result = execFileSync("python3", ["-c", storeSQL, tempFile], {
      timeout: 10000,
      encoding: "utf-8",
    });

    success = result.trim().startsWith("stored:");
    return success;

  } catch (err) {
    console.error(`[nima-memory] Store failed: ${err.message}`);
    if (err.stderr) {
      console.error(`[nima-memory] Python error: ${err.stderr}`);
    }
    return false;
  } finally {
    // Clean up temp file
    try {
      if (existsSync(tempFile)) {
        unlinkSync(tempFile);
      }
    } catch (cleanupErr) {
      console.error(`[nima-memory] Failed to clean up temp file: ${cleanupErr.message}`);
    }
  }
}

// =============================================================================
// UTILITIES
// =============================================================================

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

/**
 * Escape LIKE pattern wildcards for safe SQL LIKE queries.
 * Escapes: %, _, \
 */
function escapeLikePattern(pattern) {
  if (!pattern) return "";
  return pattern
    .replace(/\\/g, "\\\\")  // Escape backslash first
    .replace(/%/g, "\\%")     // Escape %
    .replace(/_/g, "\\_");    // Escape _
}

// =============================================================================
// PLUGIN EXPORT
// =============================================================================

// Import live recall hook
import nimaRecallLivePlugin from "./recall-hook.js";

export default function nimaMemoryPlugin(api, config) {
  // ─── Config with defaults ───
  const identityName = config?.identity_name || "agent";
  const skipSubagents = config?.skip_subagents !== false;
  const skipHeartbeats = config?.skip_heartbeats !== false;

  // Content limits
  const contentLimits = {
    maxTextLength: config?.content_limits?.max_text_length || 3000,
    maxSummaryLength: config?.content_limits?.max_summary_length || 300,
    maxSummaryInput: config?.content_limits?.max_summary_input || 80,
    maxThinkingSummary: config?.content_limits?.max_thinking_summary || 120,
    maxOutputSummary: config?.content_limits?.max_output_summary || 100,
  };

  // Free Energy config
  const feConfig = {
    minThreshold: config?.free_energy?.min_threshold ?? 0.2,
    affectVarianceWeight: config?.free_energy?.affect_variance_weight ?? 0.3,
    thinkingBoost: config?.free_energy?.thinking_boost ?? 0.1,
    routinePenalty: config?.free_energy?.routine_penalty ?? 0.2,
    monotonousPenalty: config?.free_energy?.monotonous_penalty ?? 0.4,
  };

  // Noise filtering config
  const noiseConfig = {
    filterHeartbeatMechanics: config?.noise_filtering?.filter_heartbeat_mechanics !== false,
    filterSystemNoise: config?.noise_filtering?.filter_system_noise !== false,
    filterEmptyExchanges: config?.noise_filtering?.filter_empty_exchanges !== false,
    minExchangeLength: config?.noise_filtering?.min_exchange_length || 5,
  };

  const log = api.log || console;

  // Initialize database on first hook (no global state race)
  let initAttempted = false;

  // ─── Health Check on Gateway Start ───
  if (config?.database?.health_check_on_startup !== false) {
    // Run health check after a short delay (let gateway fully start)
    setTimeout(() => {
      const health = healthCheck();
      if (health.ok) {
        log.info?.(`[nima-memory] ✅ Health check passed`);
        log.info?.(`[nima-memory] Database: ${health.stats.nodes} nodes, ${health.stats.turns} turns, ${health.stats.db_size_mb}MB`);
        if (health.stats.recent_24h > 0) {
          log.info?.(`[nima-memory] Recent activity: ${health.stats.recent_24h} memories in last 24h`);
        }
      } else {
        log.warn?.(`[nima-memory] ⚠️ Health check failed: ${health.error}`);
        if (health.path) {
          log.warn?.(`[nima-memory] Database path: ${health.path}`);
        }
      }
    }, 1000);
  }

  // ─── Auto-Migration to LadybugDB (if enabled) ───
  if (config?.database?.auto_migrate === true && config?.database?.backend === "ladybugdb") {
    setTimeout(() => {
      const batchSize = config?.database?.migration_batch_size || 500;
      log.info?.(`[nima-memory] Starting auto-migration to LadybugDB (batch size: ${batchSize})...`);
      
      const migrationScript = join(os.homedir(), ".openclaw", "extensions", "nima-memory", "migrate_to_ladybug.py");
      
      try {
        const result = execFileSync("python3", [
          migrationScript,
          "--batch-size", String(batchSize),
          "--auto"
        ], {
          timeout: 600000, // 10 minutes max
          encoding: "utf-8"
        });
        
        log.info?.(`[nima-memory] ✅ Migration completed`);
        log.info?.(`[nima-memory] Check ${MEMORY_DIR}/migration.log for details`);
      } catch (err) {
        log.error?.(`[nima-memory] ❌ Migration failed: ${err.message}`);
        log.error?.(`[nima-memory] See ${MEMORY_DIR}/migration.log for details`);
        log.warn?.(`[nima-memory] Falling back to SQLite...`);
      }
    }, 2000);
  }

  // ─── Single Hook: agent_end ───
  api.on("agent_end", (event, ctx) => {
    try {
      // Try to initialize DB on first use (allows retry on failure)
      if (!initAttempted) {
        initAttempted = true;
        const initialized = initDatabase();
        if (initialized) {
          log.info?.(`[nima-memory] SQLite graph initialized at ${GRAPH_DB}`);
        } else {
          log.error?.(`[nima-memory] Failed to initialize database - will retry on next event`);
          initAttempted = false; // Allow retry
          return;
        }
      }

      // Skip subagents and heartbeats
      if (skipSubagents && ctx.sessionKey?.includes(":subagent:")) return;
      if (skipHeartbeats && ctx.sessionKey?.includes("heartbeat")) return;

      // Skip failed runs
      if (!event.success) return;

      // Extract all three layers from messages
      const layers = extractLayers(event.messages);
      if (!layers) return;

      // Skip if no meaningful content (heartbeat acks, etc.)
      if (!layers.input.text && !layers.output.text) return;
      if (layers.output.text === "HEARTBEAT_OK" || layers.output.text === "NO_REPLY") return;
      
      // Skip if input was purely heartbeat instruction (already filtered by cleanInputText)
      if (!layers.input.text && !layers.contemplation.text) return;

      // Skip system noise (gateway restarts, doctor hints, JSON system messages)
      if (isLowQualityMemory(layers.input.text, layers.output.text, layers.contemplation.text)) {
        log.debug?.(`[nima-memory] Skipping system noise memory`);
        return;
      }

      // Get current affect state
      const conversationId = ctx.conversationId || ctx.channelId || ctx.chatId || null;
      const affect = readAffectState(conversationId, identityName);
      
      // Calculate FE (Free Energy) score for novelty filtering
      const feScore = calculateFEScoreWithConfig(
        layers.input,
        layers.contemplation,
        layers.output,
        affect,
        feConfig
      );
      
      // Skip monotonous memories (very low FE = repetitive/routine)
      if (feScore < feConfig.minThreshold) {
        log.info?.(`[nima-memory] Skipping low-FE memory (fe=${feScore.toFixed(2)}, threshold=${feConfig.minThreshold})`);
        return;
      }

      // Create memory record
      const record = createMemoryRecord(
        layers.input,
        layers.contemplation,
        layers.output,
        affect,
        {
          sessionKey: ctx.sessionKey || "",
          conversationId: conversationId || "",
          agentId: ctx.agentId || "",
          durationMs: event.durationMs || 0,
          feScore: feScore,
        }
      );

      // Store to graph
      const stored = storeMemory(record);
      if (stored) {
        const topAffect = affect ? Object.entries(affect).sort((a,b) => b[1]-a[1])[0]?.[0] : 'none';
        log.info?.(`[nima-memory] Stored turn: ${layers.input?.who || 'user'} → thinking → response (affect: ${topAffect})`);
      } else {
        log.error?.(`[nima-memory] Failed to store memory turn`);
      }
    } catch (err) {
      console.error(`[nima-memory] agent_end error: ${err.message}`);
      console.error(err.stack);
    }
  });

  // ─── Compaction Hooks ───
  // before_compaction: Flush recent memories before context window compaction
  api.on("before_compaction", (event, ctx) => {
    try {
      log.info?.(`[nima-memory] Pre-compaction flush (${event.messageCount} messages, ${event.tokenCount || '?'} tokens)`);
      // No special action needed - agent_end already captures memories
      // This hook is here to prevent the "Summarization failed" error
    } catch (err) {
      console.error(`[nima-memory] before_compaction error: ${err.message}`);
    }
  });

  // after_compaction: Log compaction stats
  api.on("after_compaction", (event, ctx) => {
    try {
      log.info?.(`[nima-memory] Compaction complete (compacted ${event.compactedCount} messages, ${event.messageCount} remain)`);
    } catch (err) {
      console.error(`[nima-memory] after_compaction error: ${err.message}`);
    }
  });

  // ─── Gateway Hooks ───
  api.on("gateway_start", () => {
    // Health check already runs via setTimeout above
    log.info?.(`[nima-memory] Plugin loaded - three-layer capture active`);
  });

  // ─── Expose Health Check API ───
  // Other plugins or tools can call this
  if (api.registerMethod) {
    api.registerMethod("nima-memory.healthCheck", () => {
      return healthCheck();
    });
  }

  // Register live recall hook (queries memory on every message)
  nimaRecallLivePlugin(api, config);
}
