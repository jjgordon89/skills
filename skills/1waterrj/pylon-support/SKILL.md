---
name: pylon-support
description: Work with Pylon tickets via their REST API. Use when you need to list or inspect issues, add internal notes/customer replies, or run any ad‑hoc Pylon API call.
metadata:
  {
    "openclaw":
      {
        "requires": { "env": ["PYLON_API_TOKEN"] },
        "primaryEnv": "PYLON_API_TOKEN",
      },
  }
---

# Pylon Support Operations

This skill bundles lightweight tooling for interacting with Pylon's REST API so you can audit tickets, chase follow‑ups, or post updates without leaving the terminal.

## Setup

1. Create a Pylon API token with the permissions you need (issues, messages, contacts, etc.).
2. Export it before running any script:
   ```bash
   export PYLON_API_TOKEN="<token>"
   ```
3. Optional: override the base URL (for staging) with `PYLON_API_BASE`.
4. (Optional) Create a config file at `~/.pylonrc` to cache your user id or custom defaults. Use `pylon_env.py` to manage it.

See [`references/pylon_api.md`](references/pylon_api.md) for endpoint summaries and example payloads.

## Scripts

### `scripts/pylon_list_issues.py`
Quickly dumps `/issues` with common filters so you can spot blockers.

```bash
python3 scripts/pylon_list_issues.py --state waiting_on_you --limit 25
python3 scripts/pylon_list_issues.py --team-id team_9
```

Set `--assignee-id <user-id>` if you want the script to filter the response down to a single owner (useful because the API sometimes ignores that server-side filter). You can discover your user ID via: `python3 scripts/pylon_request.py /users --param search=jordan`.

The script prints the API response and, when applicable, the `cursor` for the next page. Feed that cursor back through `--page-cursor` to continue.

### `scripts/pylon_env.py`
Lightweight config helper for caching your user id or preferred defaults inside `~/.pylonrc` (path overridable with `PYLON_CONFIG_FILE`).

```bash
# Discover and cache your /me user id
python3 scripts/pylon_env.py --refresh-user-id

# Set a default window size and view summary
env PYLON_CONFIG_FILE=~/.pylonrc python3 scripts/pylon_env.py --set-window-days 7
python3 scripts/pylon_env.py --show
```

### `scripts/pylon_my_queue.py`
Produces a readable summary of your queue: counts by state plus per-ticket details (title, priority, last update, link).

```bash
# Quick view using cached user id
python3 scripts/pylon_my_queue.py

# Override assignee or window, limit API fetches
python3 scripts/pylon_my_queue.py --assignee-id usr_123 --window-days 14 --limit 400
```

### `scripts/pylon_triage_report.py`
Higher-level triage report: fetch multiple assignees at once, bucket by state, and show the top N tickets per state with last-update timestamps.

```bash
# My queue, 30-day window, top 10 per state
python3 scripts/pylon_triage_report.py --top 10

# Team view for multiple assignees, 14-day window
python3 scripts/pylon_triage_report.py \
  --assignee-id usr_kody --assignee-id usr_skyler --window-days 14 --top 5
```

### `scripts/pylon_update_issue.py`
Quick state/tag/assignee/custom-field updates without opening the UI.

```bash
# Move a ticket to waiting_on_customer and tag it
python3 scripts/pylon_update_issue.py iss_123 --state waiting_on_customer --tags followup pending_ops

# Set priority custom field
python3 scripts/pylon_update_issue.py iss_456 --priority high
```

### `scripts/pylon_add_note.py`
Drop an internal note or customer-visible reply.

```bash
# Internal note from inline text
python3 scripts/pylon_add_note.py iss_123 --text "Looping engineering for root cause" --private

# Customer reply from an HTML snippet
python3 scripts/pylon_add_note.py iss_123 --file reply.html --html
```

### `scripts/pylon_request.py`
General-purpose wrapper for any Pylon endpoint. Provide the path, method, and optional params/body.

```bash
# Update a ticket state
python3 scripts/pylon_request.py /issues/iss_123 \
  --method PATCH \
  --data '{"state":"waiting_on_customer"}'

# Add an internal note
python3 scripts/pylon_request.py /issues/iss_123/messages \
  --method POST \
  --data '{"message_html":"<p>Looping product...</p>","is_private":true}'

# Fetch issue messages (GET is default)
python3 scripts/pylon_request.py /issues/iss_123/messages
```

Flags:
- `--param key=value` (repeatable) to add query params.
- `--data '{...}'` or `--data-file payload.json` for the request body.

### `scripts/pylon_client.py`
Shared helper that handles auth, base URL, and JSON parsing. Import it if you add more task-specific scripts.

## Workflow tips

1. **Triage every morning**: `pylon_list_issues.py --state waiting_on_you` gives you the queue of items where your team owes a reply.
2. **Deep dive a ticket**: use `pylon_request.py /issues/<id>` to pull the metadata, then `/issues/<id>/messages` for the conversation history.
3. **Update statuses quickly**: patch the issue state or snooze window via `--method PATCH` calls.
4. **Add context while handoffs happen**: post internal notes with `is_private=true` before tagging teammates in Slack.

Refer to [`references/pylon_api.md`](references/pylon_api.md) for the full list of helpful endpoints (users, contacts, tags, etc.) and link to the official docs when you need fields not covered here.
