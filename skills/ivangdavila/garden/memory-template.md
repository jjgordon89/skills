# Memory Setup - Garden

## Initial Setup

Create directory on first use:

```bash
mkdir -p ~/garden/{plants,zones,log}
touch ~/garden/memory.md ~/garden/climate.md ~/garden/harvests.md
```

## memory.md Template

Copy to `~/garden/memory.md`:

```markdown
# Garden Memory

## Active Alerts
<!-- Frost warnings, pest outbreaks, overdue tasks -->

## Current Focus
<!-- What needs attention this week -->
- [ ] Task pending
- [ ] Another task

## Quick Status
| Zone | Status | Next Action |
|------|--------|-------------|
| bed-1 | Active | Water Thu |
| bed-2 | Fallow | Plant garlic Oct |

## Recent Activity
<!-- Last 5-7 actions, auto-pruned -->

---
*Last: YYYY-MM-DD*
```

## climate.md Template

Copy to `~/garden/climate.md`:

```markdown
# Climate Configuration

## Zone
- **USDA Zone:** 7b
- **Average last frost:** April 15
- **Average first frost:** October 15
- **Growing season:** ~180 days

## Microclimate Notes
- South bed: 1-2 weeks earlier than zone average (sheltered)
- North fence area: colder, frost pocket

## Seasonal Reminders
| Month | Tasks |
|-------|-------|
| Feb | Start seeds indoors |
| Apr | Last frost, transplant |
| Oct | First frost, harvest tender |
| Nov | Plant garlic, cover crops |
```

## harvests.md Template

Copy to `~/garden/harvests.md`:

```markdown
# Harvest Log

## 2026

| Date | Plant | Zone | Yield | Notes |
|------|-------|------|-------|-------|
| 2026-07-15 | Tomato Cherry | bed-1 | 0.5 kg | First harvest |
| 2026-07-22 | Zucchini | bed-2 | 3 fruits | Peak production |

## Season Totals

| Plant | Total Yield | Best Zone | Notes |
|-------|-------------|-----------|-------|
| Tomatoes | 12 kg | bed-1 | Cherry variety best |

---

## Previous Years

### 2025
| Plant | Total | Notes |
|-------|-------|-------|
| Tomatoes | 8 kg | Blight reduced yield |
```

## Plant File Template

Create `plants/{name}.md` for each plant. See `tracking.md` for full template.

Quick version:

```markdown
# Tomato Cherry

- **Variety:** Cherry Bomb
- **Planted:** 2026-03-15
- **Location:** bed-1
- **Care:** Water 2-3 days, feed biweekly
- **Harvest:** July-October

## Health Log
| Date | Issue | Treatment | Outcome |
|------|-------|-----------|---------|
```

## Zone File Template

Create `zones/{name}.md` for each area. See `tracking.md` for full template.

Quick version:

```markdown
# Raised Bed 1

- **Sun:** Full (8+ hours)
- **Soil:** Amended clay, pH 6.5
- **Irrigation:** Drip, zone 2

## Current (2026)
| Position | Plant | Status |
|----------|-------|--------|

## Rotation History
| Year | Plants |
|------|--------|
| 2025 | Squash, garlic |
```
