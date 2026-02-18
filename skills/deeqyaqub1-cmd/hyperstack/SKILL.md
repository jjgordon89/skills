---
name: hyperstack
description: "Typed graph memory for multi-agent coordination. Replace GOALS.md + DECISIONS.md with queryable cards and relations. Ask 'what blocks task X?' and get exact answers, not text blobs."
user-invocable: true
homepage: https://cascadeai.dev/hyperstack
metadata:
  openclaw:
    emoji: "🃏"
    requires:
      env:
        - HYPERSTACK_API_KEY
    primaryEnv: HYPERSTACK_API_KEY
---

# HyperStack — Typed Graph Memory for Multi-Agent Coordination

## What this does

Replaces markdown-file coordination (GOALS.md, DECISIONS.md, WORKING.md) with a typed knowledge graph that any agent can query.

**Before** (current OpenClaw multi-agent):
```
# DECISIONS.md (append-only)
- 2026-02-15: Use Clerk for auth (coder-agent)
- 2026-02-16: Migration blocks production deploy (ops-agent)
```
"What blocks deploy?" → `grep -r "blocks.*deploy" *.md` → manual, fragile

**After** (HyperStack):
```
"What blocks deploy?" → hs_blockers deploy-prod → [migration-23] Auth migration to Clerk
```

Typed relations. Exact answers. Zero LLM cost.

## Tools

### hs_search
Search the shared knowledge graph. Hybrid semantic + keyword matching.
```
hs_search({ query: "authentication setup" })
```

### hs_store
Store a card in the graph. Auto-tags with your agent ID.
```
hs_store({
  slug: "use-clerk",
  title: "Use Clerk for auth",
  body: "Better DX, lower cost, native Next.js support",
  type: "decision",
  links: "auth-api:triggers,alice:decided"
})
```

### hs_decide
Record a decision with full provenance — who decided, what it affects, what it blocks.
```
hs_decide({
  slug: "use-clerk",
  title: "Use Clerk for auth",
  rationale: "Better DX, lower cost vs Auth0",
  affects: "auth-api,user-service",
  blocks: ""
})
```

### hs_blockers
Check what blocks a task/card. Returns exact typed blockers, not fuzzy search results.
```
hs_blockers({ slug: "deploy-prod" })
→ "1 blocker: [migration-23] Auth migration to Clerk"
```

### hs_graph
Traverse the knowledge graph from a starting card. See connections, ownership, dependencies. Supports time-travel: pass a timestamp to reconstruct the graph as it was at any point in time.
```
hs_graph({ from: "auth-api", depth: 2 })
→ nodes: [auth-api, use-clerk, migration-23, alice]
→ edges: [auth-api→triggers→use-clerk, migration-23→blocks→deploy-prod]

# Time-travel: see the graph at a specific moment
hs_graph({ from: "auth-api", depth: 2, at: "2026-02-15T03:00:00Z" })
```

### hs_my_cards
List all cards created by this agent.
```
hs_my_cards()
→ "3 cards by agent researcher: [finding-clerk-pricing] [finding-auth0-limits]"
```

### hs_ingest
Auto-extract cards from raw text. Paste a conversation transcript, meeting notes, or project description — HyperStack extracts people, decisions, preferences, and tech stack mentions. Zero LLM cost (regex-based). Best for onboarding: go from 0 to populated graph in seconds.
```
hs_ingest({ text: "We're using Next.js 14 and PostgreSQL. Alice decided to use Clerk for auth." })
→ "✅ Created 3 cards from 78 chars:
  [tech-nextjs] Next.js 14 (preference)
  [tech-postgresql] PostgreSQL (preference)
  [decision-use-clerk] Use Clerk for auth (decision)"
```

### hs_inbox
Check for cards directed at this agent by other agents. Enables multi-agent coordination through shared memory — Agent A stores a signal for Agent B, Agent B picks it up via inbox.
```
hs_inbox({})
→ "Inbox for cursor-mcp: 1 card(s)
  [review-needed] Review auth migration (signal) from=claude-desktop-mcp"
```

### hs_webhook (Team+)
Register a webhook so this agent gets notified in real time when cards are directed at it. Agent A stores a blocker → Agent B gets notified automatically.
```
hs_webhook({
  url: "https://your-server.com/webhook",
  events: "card.created,signal.received"
})
```

### hs_stats ✨ NEW in v1.0.15
Get token savings stats and memory usage for this workspace. Shows how much context HyperStack is saving vs loading everything into context. Requires Pro plan.
```
hs_stats()
→ "HyperStack Stats for workspace: default
   Cards: 24 | Tokens stored: 246 | Stale: 0
   Without HyperStack: 246 tokens/msg ($11.07/mo)
   With HyperStack:    200 tokens/msg ($9.00/mo)
   Saving: 15% — $2.07/mo
   
   Card breakdown:
   decisions: 8 | preferences: 6 | general: 10"
```

### hs_agent_tokens (Team+) ✨ NEW in v1.0.15
Create, list, and revoke scoped per-agent tokens. Instead of sharing one master API key across all agents, give each agent only the permissions it needs. Requires Team plan.
```
# Create a scoped token for a specific agent
hs_agent_tokens({
  action: "create",
  name: "Researcher Agent",
  agentId: "researcher",
  canRead: ["*"],
  canWrite: ["general", "signal"],
  allowedStacks: ["general", "decisions"]
})
→ "Created token for researcher: hsa_abc123...
   Read: all | Write: general, signal | Stacks: general, decisions"

# List all agent tokens
hs_agent_tokens({ action: "list" })

# Revoke a token
hs_agent_tokens({ action: "revoke", id: "token-id" })
```

## Multi-Agent Setup

Each agent gets its own ID. Cards are auto-tagged so you can see who created what.

Recommended roles:
- **coordinator**: Routes tasks, monitors blockers (`hs_blockers`, `hs_graph`, `hs_decide`)
- **researcher**: Investigates, stores findings (`hs_search`, `hs_store`, `hs_ingest`)
- **builder**: Implements, records tech decisions (`hs_store`, `hs_decide`, `hs_blockers`)

## Setup

### Option A: VPS / Self-hosted agent (recommended)
Run the SDK on your own machine or VPS. Authenticate via browser — no manual key management.
```bash
npm i hyperstack-core
npx hyperstack-core login          # opens browser, approve device, done
npx hyperstack-core init openclaw-multiagent
```
Credentials are saved to `~/.hyperstack/credentials.json`. All commands and tools authenticate automatically.

### Option B: OpenClaw environment variable
1. Get free API key: https://cascadeai.dev/hyperstack
2. Set `HYPERSTACK_API_KEY=hs_your_key` in your OpenClaw env
3. Tools are available immediately

### Option C: Programmatic (Node.js adapter)
```js
import { createOpenClawAdapter } from "hyperstack-core/adapters/openclaw";
const adapter = createOpenClawAdapter({ agentId: "builder" });
await adapter.onSessionStart({ agentName: "Builder", agentRole: "Implementation" });
// adapter.tools: hs_search, hs_store, hs_decide, hs_blockers, hs_graph, hs_my_cards, hs_ingest
await adapter.onSessionEnd({ summary: "Completed auth migration" });
```

### How it works
The SDK runs on your machine/VPS. Every `hs_store`, `hs_search`, `hs_blockers` call hits the HyperStack API. You own your agent. We host the graph.

Free: 10 cards, keyword search.
Pro ($29/mo): 100 cards, graph traversal, semantic search, time-travel debugging, token savings stats.
Team ($59/mo): 500 cards, 5 team API keys, webhooks, unlimited workspaces, scoped agent tokens.

## When to use

- **Start of session**: `hs_search` for relevant context
- **New project/onboarding**: `hs_ingest` to auto-populate from existing docs
- **Decision made**: `hs_decide` with rationale and links
- **Task blocked**: `hs_store` with `blocks` relation
- **Before starting work**: `hs_blockers` to check dependencies
- **Debug a bad decision**: `hs_graph` with `at` timestamp to see what the agent knew
- **Cross-agent signal**: `hs_store` with `targetAgent` → other agent checks `hs_inbox`
- **Check efficiency**: `hs_stats` to see token savings and memory health
- **Lock down agents**: `hs_agent_tokens` to give each agent only what it needs

## Data safety

NEVER store passwords, API keys, tokens, PII, or credentials. Cards should be safe in a data breach. Always confirm with user before storing.

## Changelog

### v1.0.15 (Feb 17, 2026)

#### ✨ `hs_stats` — Token Savings & Memory Health (Pro+)
Previously there was no way for an agent to know how much context HyperStack was saving or how healthy its memory was. `hs_stats` calls the analytics endpoint and returns a full report:
- **Cards stored** and total tokens in memory
- **Token savings comparison** — what you'd spend loading everything into context vs using HyperStack's selective retrieval
- **Monthly cost savings** in dollars (based on 100 msgs/day at GPT-4 rates)
- **Card breakdown by stack** — how many decisions, preferences, projects etc.
- **Last 7 days activity** — reads, writes, token usage
- **Stale card count** — cards not updated in 30+ days that may need review

Use case: agents can call `hs_stats` at the end of a session to report efficiency gains. Also the strongest argument for upgrading from Free to Pro.

#### ✨ `hs_agent_tokens` — Scoped Per-Agent Permissions (Team+)
Previously all agents shared one master API key, meaning any agent could read or write any card. This was a blocker for teams putting sensitive data in HyperStack — a rogue or compromised agent could read everything.

`hs_agent_tokens` lets you create scoped tokens per agent:
- **canRead** — restrict which card types the agent can read (`general`, `decision`, `preference`, `person`, `project`, `workflow`, `signal`, or `*` for all)
- **canWrite** — restrict which card types the agent can write
- **allowedStacks** — restrict which stacks the agent can access
- **expiresIn** — optional TTL in seconds for temporary access
- Tokens are prefixed `hsa_` (agent-scoped) vs `hs_` (master key) so you can tell them apart
- Revoke any token instantly without rotating your master key

Use case: give your researcher agent read-only access to decisions, give your builder agent write access to projects only, give a third-party skill access to nothing sensitive.

### v1.0.14 (Feb 17, 2026)

#### ✨ `hs_ingest` — Auto-Extract Cards from Raw Text (zero LLM cost)
Before v1.0.14, populating HyperStack required manually calling `hs_store` for every card. Starting from scratch meant a lot of upfront work.

`hs_ingest` takes raw text — a conversation transcript, meeting notes, project description, or any unstructured text — and automatically extracts structured cards using regex pattern matching. No LLM cost, no API calls to OpenAI.

What it detects:
- **Decisions** — "we decided", "chose X over Y", "went with"
- **Preferences** — "I prefer", "we always use", "don't use"
- **People** — "Alice is the lead", "owned by", "responsible for"
- **Projects** — "we're building", "our backend", "milestone"
- **Workflows** — "first X then Y", "whenever we", "pipeline"
- **Tech stack** — auto-detects 40+ frameworks, databases, and services and bundles them into a single tech-stack card

Use case: paste your entire project README or a team meeting transcript and go from 0 to a populated knowledge graph in seconds.

#### ✨ `hs_inbox` — Agent-Directed Card Retrieval
Before v1.0.14, agents could store cards with a `targetAgent` field but had no dedicated tool to check for cards directed at them. `hs_inbox` polls for cards where `targetAgent` matches the current agent's ID, optionally filtered by timestamp so agents only see new messages since their last check.

Use case: Agent A finishes a task and stores a signal card directed at Agent B. Agent B calls `hs_inbox` at the start of its session and picks up the handoff automatically — no shared file system, no message queue needed.

#### ✨ `hs_webhook` / `hs_webhooks` — Real-Time Agent Notifications (Team+)
Instead of polling `hs_inbox`, Team plan agents can register a webhook URL and get notified in real time when cards are directed at them. Supports event filtering (`card.created`, `card.updated`, `signal.received`, or `*` for all). HMAC secret signing for verification.

#### 🔧 OAuth Device Flow for CLI Login
`npx hyperstack-core login` now uses RFC 8628 OAuth device flow. CLI displays a short code, user approves in browser, credentials saved automatically. No more manual copy-pasting of API keys for VPS/self-hosted agents.

### v1.0.13 and earlier — Core Foundation

The original HyperStack toolset that established the core value proposition:

- **`hs_search`** — Hybrid keyword + semantic search across all cards. Keyword search is free, semantic search (vector similarity via pgvector) requires Pro. Returns ranked results with relevance scores.

- **`hs_store`** — Create or update a card with full metadata: slug, title, body, cardType, keywords, links with typed relations (owns, triggers, blocks, depends-on, reviews, notifies, approved, decided), sourceAgent, targetAgent.

- **`hs_decide`** — Specialized decision recorder. Creates a decision card with provenance — who decided, what it affects, what it blocks. Automatically creates typed graph edges so decisions are queryable by relation, not just text.

- **`hs_blockers`** — The headline feature. Given a card slug, traverses the graph with `relation=blocks` filter and returns exact typed blockers. "What blocks deploy-prod?" returns the exact cards, not a fuzzy search result. Deterministic, $0 cost.

- **`hs_graph`** — Full graph traversal from any starting node. Configurable depth (1-3 hops), relation filter, and time-travel (`at` timestamp to reconstruct the graph as it was at any past moment). Requires Pro plan.

- **`hs_my_cards`** — List all cards created by the current agent. Useful for agents to audit their own memory footprint.
