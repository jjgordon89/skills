#!/usr/bin/env python3
"""Team queue summary for multiple assignees."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Sequence

from pylon_client import api_request
from pylon_utils import compute_time_window, get_window_days, humanize_timesince


def fetch_issues(
    assignee_ids: Sequence[str],
    start: str,
    end: str,
    limit: int,
) -> List[dict]:
    params = {
        "start_time": start,
        "end_time": end,
        "limit": str(limit),
    }
    resp = api_request("/issues", params=params)
    raw = resp.get("data", [])
    targets = set(assignee_ids)
    filtered = []
    for issue in raw:
        assignee = ((issue.get("assignee") or {}).get("id"))
        if assignee and (not targets or assignee in targets):
            filtered.append(issue)
    return filtered


def parse_time(ts: str | None) -> datetime | None:
    if not ts:
        return None
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Team summary for Pylon queues")
    parser.add_argument(
        "--assignee",
        action="append",
        metavar="NAME=ID",
        help="Name-to-userID mapping (e.g., kody=usr_123). Can repeat.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        help="Lookback window in days (default: config or 30)",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=2,
        help="Flag issues with no update in this many days (default 2)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max issues to fetch (default 500)",
    )
    args = parser.parse_args()

    if not args.assignee:
        raise SystemExit("Provide at least one --assignee NAME=ID entry")

    team = {}
    for entry in args.assignee:
        if "=" not in entry:
            raise SystemExit(f"Invalid --assignee entry: {entry}")
        name, user_id = entry.split("=", 1)
        team[name.strip()] = user_id.strip()

    window_days = get_window_days(args.window_days)
    start, end = compute_time_window(window_days)
    issues = fetch_issues(list(team.values()), start, end, args.limit)

    threshold = datetime.now(timezone.utc) - timedelta(days=args.stale_days)
    issues_by_user: Dict[str, List[dict]] = defaultdict(list)
    for issue in issues:
        assignee = ((issue.get("assignee") or {}).get("id"))
        for name, uid in team.items():
            if assignee == uid:
                issues_by_user[name].append(issue)
                break

    print(f"Team window: last {window_days} days ({start} → {end}), stale>{args.stale_days}d\n")

    for name, uid in team.items():
        user_issues = issues_by_user.get(name, [])
        counts = Counter((issue.get("state") or "unknown").lower() for issue in user_issues)
        stale = []
        for issue in user_issues:
            latest = issue.get("latest_message_time") or issue.get("updated_at")
            dt = parse_time(latest)
            if not dt or dt < threshold:
                stale.append(issue)
        print(f"## {name} ({uid})")
        if not user_issues:
            print("No issues in window.\n")
            continue
        count_line = ", ".join(f"{state}:{count}" for state, count in counts.items())
        print(f"Total {len(user_issues)} · {count_line if count_line else 'no state data'}")
        if stale:
            print("Stale:")
            for issue in stale[:5]:
                number = issue.get("number")
                title = issue.get("title", "(no title)")
                latest = issue.get("latest_message_time") or issue.get("updated_at")
                ago = humanize_timesince(latest)
                link = issue.get("link") or f"https://app.usepylon.com/issues?issueNumber={number}"
                state = (issue.get("state") or "").lower()
                print(f"  - #{number} [{state}] {title} · last update {ago} · {link}")
        else:
            print("No stale issues.")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
