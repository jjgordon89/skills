# FIS (Federal Intelligence System) Architecture Skill

> **Version**: 3.2.6  
> **Name**: Federal Intelligence System (联邦智能系统)  
> **Description**: File-based multi-agent workflow framework. Core: JSON tickets + Markdown knowledge (no Python required). Optional: Python helpers in `lib/` for badge generation. Integrates with OpenClaw QMD for semantic search.
> 
> **Security**: See [SECURITY.md](./SECURITY.md) for subprocess usage, resource permissions, and sandboxing guidelines.
> 
> **Note**: Legacy FIS 3.1 components (memory_manager, skill_registry, etc.) are preserved in GitHub repo history but not included in this release. See repo for historical reference.  
> **Status**: ✅ Stable — Simplified architecture with QMD integration

---

## Before You Install

**Core workflow**: Pure file-based (JSON tickets, Markdown). **No Python required for basic use.**

**Optional components** (review before use):
- `lib/*.py` — Badge generation helpers (require `pip install Pillow qrcode`)
- `lib/fis_lifecycle.py` — CLI helpers for ticket management

**Required**: `mcporter` CLI (included with OpenClaw), `openclaw` CLI

**Security**: Review [SECURITY.md](./SECURITY.md) before running Python scripts or granting ticket `resources` permissions.

---

## Core Principle: FIS Manages Workflow, QMD Manages Content

**FIS 3.2** is a radical simplification of FIS 3.1. We removed components that overlapped with QMD (Query Model Direct) semantic search capabilities:

| Component | FIS 3.1 | FIS 3.2 | Reason |
|-----------|---------|---------|--------|
| Task Management | Python classes + memory_manager | Ticket files (JSON) | Simpler, audit-friendly |
| Memory/Retrieval | memory_manager.py | **QMD** | QMD has native semantic search |
| Skill Discovery | skill_registry.py | **SKILL.md + QMD** | QMD indexes SKILL.md files |
| Knowledge Graph | experimental/kg/ | **QMD** | QMD covers knowledge discovery |
| Deadlock Detection | deadlock_detector.py | Simple conventions | Rarely needed in practice |

**What's Kept**: Only the unique workflow capabilities that FIS provides.

---

## What's New in 3.2.0

### Simplified Architecture
- **Core workflow**: File-based (JSON tickets, Markdown knowledge) — no Python required
- **Optional helpers**: Python scripts in `lib/` for badge generation (auditable, optional)
- **Official integration**: Uses OpenClaw QMD for semantic search — see https://docs.openclaw.ai/concepts/memory
- **Badge generator**: Visual identity for subagents (requires Pillow, optional)

### Directory Structure

```
fis-hub/                    # Your shared hub
├── 📁 tickets/                      # Task workflow (FIS core)
│   ├── active/                      # Active tasks (JSON files)
│   └── completed/                   # Archived tasks
├── 📁 knowledge/                    # Shared knowledge (QMD-indexed)
│   ├── cybermao/                    # System knowledge
│   ├── fis/                         # FIS documentation
│   └── your-domain/                 # Your domain knowledge
├── 📁 results/                      # Research outputs
├── 📁 archive/                      # Archived old versions
│   ├── fis3.1-full/                 # Complete 3.1 backup
│   └── fis3.1-legacy/               # Legacy files
└── 📁 .fis3.1/                      # Light configuration
    └── notifications.json           # Event notifications
```

---

## Quick Start

### 1. Create a Task Ticket

```bash
# Create ticket manually or use helper
cat > ~/.openclaw/fis-hub/tickets/active/TASK_EXAMPLE_001.json << 'EOF'
{
  "ticket_id": "TASK_EXAMPLE_001",
  "agent_id": "worker-001",
  "parent": "cybermao",
  "role": "worker",
  "task": "Analyze GPR signal patterns",
  "status": "active",
  "created_at": "2026-02-19T21:00:00",
  "timeout_minutes": 60
}
EOF
```

**Security Note**: The `resources` field (e.g., `["file_read", "code_execute"]`) can be added to tickets but should be used with caution. Only grant these permissions when necessary and audit all automated actions.

### 2. Generate Badge Image

```bash
cd ~/.openclaw/workspace/skills/fis-architecture/lib
python3 badge_generator_v7.py

# Output: ~/.openclaw/output/badges/TASK_*.png
```

### 3. Complete and Archive

```bash
# Move from active to completed
mv ~/.openclaw/fis-hub/tickets/active/TASK_EXAMPLE_001.json \
   ~/.openclaw/fis-hub/tickets/completed/
```

---

## Ticket Format

```json
{
  "ticket_id": "TASK_FIS-UAV-002_20260220_002600",
  "agent_id": "pulse",
  "parent": "cybermao",
  "role": "worker|reviewer|researcher|formatter",
  "task": {
    "description": "UAV-GPR 旋翼干扰机理分析 - 建立数学模型",
    "created_at": "2026-02-20T00:30:00",
    "deadline": "2026-02-27T09:00:00",
    "status": "active"
  },
  "objective": "理解旋翼干扰的物理机制，建立可解释的数学模型",
  "scope": {
    "must_do": [
      "分析旋翼叶片微多普勒产生的物理过程",
      "建立旋翼-雷达几何关系数学模型"
    ],
    "must_not_do": [
      "不要急于设计滤波器或抑制方法",
      "不要跳过机理直接谈解决"
    ]
  },
  "deliverables": [
    "干扰机理分析报告 (Markdown)",
    "时频分析图 (matplotlib)"
  ],
  "resources": ["file_read", "file_write", "code_execute", "web_search"],
  "output_dir": "fis-hub/results/TASK_FIS-UAV-002/",
  "notes": "关键问题：旋翼干扰是怎么产生的？"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticket_id` | string | ✅ | Unique identifier: `TASK_{agent}_{YYYYMMDD}_{seq}` |
| `agent_id` | string | ✅ | Assigned agent (e.g., "pulse", "worker-001") |
| `parent` | string | ✅ | Coordinating agent (e.g., "cybermao") |
| `role` | enum | ✅ | `worker`, `reviewer`, `researcher`, `formatter` |
| `task` | object | ✅ | `{description, created_at, deadline, status}` |
| `objective` | string | ❌ | High-level goal of the task |
| `scope` | object | ❌ | `{must_do[], must_not_do[]}` boundaries |
| `deliverables` | array | ❌ | Expected outputs/deliverables |
| `resources` | array | ❌ | Permissions: `file_read`, `file_write`, `code_execute`, `web_search` |
| `output_dir` | string | ❌ | Where to save results |
| `notes` | string | ❌ | Additional context or warnings |

---

## Workflow Patterns

### Pattern 1: Worker → Reviewer Pipeline

```
CyberMao (Coordinator)
    ↓ spawn
Worker (Task execution)
    ↓ complete
Reviewer (Quality check)
    ↓ approve
Archive
```

**Tickets**:
1. `TASK_001_worker.json` → active → completed
2. `TASK_002_reviewer.json` → active → completed

### Pattern 2: Parallel Workers

```
CyberMao
    ↓ spawn 4x
Worker-A (chunk 1)
Worker-B (chunk 2)
Worker-C (chunk 3)
Worker-D (chunk 4)
    ↓ all complete
Aggregator (combine results)
```

### Pattern 3: Research → Execute

```
Researcher (investigate options)
    ↓ deliver report
Worker (implement chosen option)
    ↓ deliver code
Reviewer (verify quality)
```

---

## When to Use SubAgents

**Use SubAgent when**:
- Task needs multiple specialized roles
- Expected duration > 10 minutes
- Failure has significant consequences
- Batch processing of many files

**Direct handling when**:
- Quick Q&A (< 5 minutes)
- Simple explanation or lookup
- One-step operations

### Decision Tree

```
User Request
    ↓
┌─────────────────────────────────────────┐
│ 1. Needs multiple specialist roles?     │
│ 2. Duration > 10 minutes?               │
│ 3. Failure impact is high?              │
│ 4. Batch processing needed?             │
└─────────────────────────────────────────┘
    ↓ Any YES
Delegate to SubAgent
    ↓ All NO
Handle directly
```

---

## QMD Integration (Content Management)

**QMD (Query Model Direct)** provides semantic search across all content:

```bash
# Search knowledge base
mcporter call 'exa.web_search_exa(query: "GPR signal processing", numResults: 5)'

# Search for skills
mcporter call 'exa.web_search_exa(query: "SKILL.md image processing", numResults: 5)'
```

**Knowledge placement**:
- Drop Markdown files into `knowledge/` subdirectories
- QMD automatically indexes them
- No manual registration needed

---

## Tool Reference

### Badge Generator v7

**Location**: `lib/badge_generator_v7.py`

**Features**:
- Retro pixel-art avatar generation
- Full Chinese/English support
- Dynamic OpenClaw version display
- Task details with QR code + barcode
- Beautiful gradient design

**Usage**:
```bash
cd ~/.openclaw/workspace/skills/fis-architecture/lib
python3 badge_generator_v7.py

# Interactive prompts for task details
# Output: ~/.openclaw/output/badges/Badge_{TICKET_ID}_{TIMESTAMP}.png
```

### CLI Helper (Optional)

```bash
# Create ticket with helper
python3 fis_subagent_tool.py full \
  --agent "Worker-001" \
  --task "Task description" \
  --role "worker"

# Complete ticket
python3 fis_subagent_tool.py complete \
  --ticket-id "TASK_CYBERMAO_20260219_001"
```

---

## Migration from FIS 3.1

If you have FIS 3.1 components:

1. **Archived components** are in `archive/fis3.1-full/` and `archive/fis3.1-legacy/`
2. **Ticket files** remain compatible (JSON format unchanged)
3. **Skill discovery** — use QMD instead of `skill_registry.py`
4. **Memory queries** — use QMD instead of `memory_manager.py`

---

## Design Principles

1. **FIS Manages Workflow, QMD Manages Content**
   - Tickets for process state
   - QMD for knowledge retrieval

2. **File-First Architecture**
   - No services or databases
   - 100% file-based
   - Git-friendly

3. **Zero Core File Pollution**
   - Never modify other agents' MEMORY.md/HEARTBEAT.md
   - Extensions isolated to `.fis3.1/`

4. **Quality over Quantity**
   - Fewer, better components
   - Remove what QMD already provides

---

## Changelog

### 2026-02-20: v3.2.5-lite Fix Module Names & Uninstall Safety
- **Fix**: Changed dangerous `rm -rf ~/.openclaw/fis-hub/` uninstall suggestion to safe skill-only removal
- **Fix**: Updated all `subagent_lifecycle` references to `fis_lifecycle` for consistency
- **Docs**: Added warning that fis-hub/ contains user data and is NOT removed by default

### 2026-02-20: v3.2.4-lite Remove Archive
- **Security**: Completely removed `archive/` directory from release (legacy 3.1 components preserved in GitHub repo history only)
- **Documentation**: Added note about legacy components availability

### 2026-02-20: v3.2.3-lite Review Feedback
- **Clarity**: Rewrote description to clearly distinguish core workflow (file-based) from optional Python helpers
- **Documentation**: Added "Before You Install" section with security notes and component breakdown
- **Metadata**: Added `mcporter` as required binary in skill.json
- **Links**: Added official OpenClaw QMD documentation link (https://docs.openclaw.ai/concepts/memory)
- **Fix**: Addressed "core uses no Python" vs "includes Python helpers" inconsistency

### 2026-02-20: v3.2.2-lite Security & Documentation Improvements
- **Security**: Removed `archive/deprecated/` from published skill (kept in GitHub repo only)
- **Documentation**: Clarified "Core functionality uses no Python" vs optional Python tools
- **Documentation**: Added security warning about `resources` field in tickets
- **Documentation**: Added Security Checklist to INSTALL_CHECKLIST.md
- **Fix**: Corrected misleading "No Python dependencies" claim to "Core functionality uses no Python"

### 2026-02-20: v3.2.1-lite Documentation Improvements
- Added: Troubleshooting section with common issues and solutions
- Added: Best practices for ticket naming and knowledge organization
- Added: Real-world usage examples in decision tree
- Improved: Clearer distinction between when to use/not use SubAgents

### 2026-02-19: v3.2.0-lite Simplification
- Removed: `memory_manager.py` → use QMD
- Removed: `skill_registry.py` → use SKILL.md + QMD
- Removed: `deadlock_detector.py` → simple conventions
- Removed: `experimental/kg/` → QMD covers this
- Kept: Ticket system, badge generator
- New: Simplified architecture documentation

### 2026-02-18: v3.1.3 Generalization
- Removed personal configuration examples
- GitHub public repository created

### 2026-02-17: v3.1 Lite Initial Deploy
- Shared memory, deadlock detection, skill registry
- SubAgent lifecycle + badge system

---

## File Locations

```
~/.openclaw/workspace/skills/fis-architecture/
├── SKILL.md                    # This file
├── README.md                   # Repository readme
├── QUICK_REFERENCE.md          # Quick command reference
├── AGENT_GUIDE.md              # Agent usage guide
├── lib/                        # Tools (not core)
│   ├── badge_generator_v7.py   # ✅ Badge generation
│   ├── fis_lifecycle.py        # ✅ Lifecycle helpers
│   ├── fis_subagent_tool.py    # ✅ CLI helper
│   └── examples/               # Usage examples
└── examples/                   # Usage examples
```

---

*FIS 3.2.0-lite — Minimal workflow, maximal clarity*  
*Designed by CyberMao 🐱⚡*

---

## Troubleshooting

### Issue: Ticket not found
**Symptom**: `cat: tickets/active/TASK_001.json: No such file or directory`

**Solution**:
```bash
# Check if directory exists
ls ~/.openclaw/fis-hub/tickets/active/

# Create if missing
mkdir -p ~/.openclaw/fis-hub/tickets/{active,completed}
```

### Issue: Badge generation fails
**Symptom**: `ModuleNotFoundError: No module named 'PIL'`

**Solution**:
```bash
pip3 install Pillow qrcode
```

### Issue: QMD search returns no results
**Symptom**: `mcporter call 'exa.web_search_exa(...)'` returns empty

**Solution**:
- Check Exa MCP configuration: `mcporter list exa`
- Verify knowledge files are in `fis-hub/knowledge/` directory
- Ensure files have `.md` extension

### Issue: Permission denied on ticket files
**Symptom**: Cannot write to `tickets/active/`

**Solution**:
```bash
chmod -R u+rw ~/.openclaw/fis-hub/tickets/
```

---

## Best Practices

### Ticket Naming
```
Good:  TASK_UAV_20260220_001_interference_analysis
Bad:   task1, new_task, test
```

### Knowledge Organization
```
knowledge/
├── papers/           # Research papers and notes
├── methods/          # Methodology documentation
├── tools/            # Tool usage guides
└── projects/         # Project-specific knowledge
```

### Regular Maintenance
```bash
# Weekly: Archive completed tickets older than 30 days
find ~/.openclaw/fis-hub/tickets/completed/ -name "*.json" -mtime +30 -exec mv {} archive/old_tickets/ \;

# Monthly: Review and clean knowledge/
ls ~/.openclaw/fis-hub/knowledge/ | wc -l  # Keep count reasonable
```
