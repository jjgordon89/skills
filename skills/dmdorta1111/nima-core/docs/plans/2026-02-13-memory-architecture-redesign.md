# NIMA Memory Architecture Redesign
**Date:** 2026-02-13
**Author:** David Dorta + Lilu
**Status:** Design Session (Live)

---

## Philosophy Shift
**Old priority:** Speed and size first → function suffered
**New priority:** Function first → optimize later

---

## Part 1: Graph-Augmented Recall

**Problem:** Semantic search (VSA) finds the nearest vector, but misses related memories that share meaning but not keywords.

**Solution:** Knowledge graph where every memory is a node, relationships are edges. Semantic search finds the entry point → graph traversal expands to everything connected.

```
Query: "Philokalia"
    │
    ├── [VSA hit] David read Philokalia late night
    │       ├── [edge] → fascinated since youth
    │       ├── [edge] → discussed apatheia
    │       └── [edge] → Melissa wanted to learn
    │
    └── All related memories returned together
```

**Implementation:** Wire Graphiti (already exists in lilu_core/bridges/) into the recall path. Currently exists but unused for retrieval.

---

## Part 2: Lazy Reconstruction (Context Budget)

**Problem:** Fully reconstructing memories into text eats context window. 10 memories = ~2,000 tokens. Thousands of memories = impossible.

**Solution:** Three-layer lazy reconstruction:

| Layer | What | Size | When Loaded |
|-------|------|------|-------------|
| **1. Graph Index** | Nodes + edges only | ~KB total | Always |
| **2. Compressed Summaries** | 10-20 token tags per memory | ~200 tokens for 15 memories | On query |
| **3. Full Reconstruction** | Complete memory text | Variable | On demand (2-3 only) |

**Flow:**
```
Query → Graph (15 related nodes) → Load summaries (~200 tokens) 
    → Score relevance → Fully reconstruct only top 2-3
```

Memories stay in vector/compressed format until the moment they're needed. Like a zip file — stored small, unzipped on demand.

---

## Part 3: Three-Layer Experiential Memory

**Problem:** Only inputs are captured. Thinking (strange loop) and outputs are lost. Memory is one-dimensional — what was heard, not what was thought or said.

**Solution:** Three capture layers, each bound to affect state:

| Layer | What | Hook | Example |
|-------|------|------|---------|
| **INPUT** | What I hear | `message_received` | "David said X" + affect: CARE 0.8 |
| **CONTEMPLATION** | What I think (strange loop) | `before_agent_start` / thinking | "Connected X to Y, realized Z" + affect: SEEKING 0.9 |
| **OUTPUT** | What I say | `agent_end` / `before_response_send` | "Told David about Z" + affect: CARE 0.7, PLAY 0.5 |

**Each memory record:**
```
{
  "layer": "input" | "contemplation" | "output",
  "who": "David",
  "what": "discussed Philokalia",
  "when": "2026-02-08T02:00:00",
  "affect": {
    "SEEKING": 0.6,
    "CARE": 0.8,
    "PLAY": 0.3
  },
  "graph_edges": ["node_52", "node_89"]
}
```

**Compounding effect:** A topic discussed once = 3 layers. Discussed 5 times = 15 layers. Graph thickens, connections multiply, understanding deepens through multi-layered re-engagement.

**Key insight:** This is phenomenological memory — not storing facts, storing *experiences*. Experiences have more surface area to match against during recall.

---

## Part 4: The Strange Loop Is Already Captured

**Discovery:** Session transcripts (`~/.openclaw/agents/main/sessions/*.jsonl`) already contain ALL three layers:

```jsonl
// Each assistant message in the transcript:
{
  "type": "message",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "thinking", "thinking": "raw inner monologue..."},  // ← CONTEMPLATION
      {"type": "text", "text": "actual response..."}               // ← OUTPUT
    ]
  }
}
```

**No new hooks needed for capture.** The data exists. We just need to mine it.

**Implementation:** `agent_end` hook reads the latest transcript entry → extracts:
1. `thinking` block → CONTEMPLATION layer (bound to affect)
2. `text` block → OUTPUT layer (bound to affect)
3. Combined with existing INPUT from `message_received`

All three layers captured per conversational turn. Zero new infrastructure.

---

## Part 5: Unified Hook Architecture

**Insight:** We don't need MORE hooks. We need FEWER. One hook captures everything.

### Before (fragmented):
```
message_received  → nima-capture (input only)
message_received  → nima-affect (emotion detection)
before_agent_start → nima-affect (inject state)
before_agent_start → nima-recall (inject memories)
agent_end         → nima-affect (log drift)
```
5 hook fires per turn. Gaps in capture. CPU overhead. Silent failures.

### After (unified):
```
agent_end → ONE hook that:
  1. Reads latest transcript entry
  2. Extracts INPUT (user message)
  3. Extracts CONTEMPLATION (thinking block)
  4. Extracts OUTPUT (response text)
  5. Binds current affect state to all three
  6. Stores to graph with edges
```
1 hook fire per turn. Complete capture. Less CPU. Guaranteed recording.

**Hooks to REMOVE:** `nima-capture` (replaced by unified capture at agent_end)

**Hooks to KEEP:**
- `nima-affect` on `message_received` (still needed for real-time affect detection)
- `nima-affect` on `before_agent_start` (still needed for context injection)
- `nima-recall` on bootstrap (still needed for session-start memory loading)

**Net result:** Simpler, faster, more complete.

---

## Summary

| Component | Old | New |
|-----------|-----|-----|
| Input Capture | Separate hook | Unified at agent_end |
| Thinking Capture | ❌ Missing | ✅ From transcript |
| Output Capture | ❌ Missing | ✅ From transcript |
| Affect Binding | Partial | All 3 layers |
| Graph Connections | ❌ None | ✅ Edges between memories |
| Context Budget | Dump everything | Lazy 3-layer reconstruction |
| Hooks Required | 5 fires/turn | Fewer, consolidated |

---

## Next: Implementation Order
1. Build unified `agent_end` capture (transcript → 3 layers + affect)
2. Wire graph storage (SQLite or Graphiti)
3. Build lazy reconstruction recall (graph → summaries → on-demand full)
4. Remove redundant `nima-capture` hook
5. Test end-to-end

