#!/usr/bin/env python3
"""Flag issues that haven't been updated within a threshold."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Sequence

from pylon_client import api_request
from pylon_utils import (
    compute_time_window,
    get_user_id,
    get_window_days,
    humanize_timesince,
)


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
    if not targets:
        return raw
    filtered = []
    for issue in raw:
        assignee = ((issue.get("assignee") or {}).get("id"))
        if assignee and assignee in targets:
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
    parser = argparse.ArgumentParser(description="Find stale issues that need follow-up")
    parser.add_argument(
        "--assignee-id",
        action="append",
        help="Filter to one or more assignee IDs (default: current user)",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        help="Lookback window in days (default: config or 30)",
    )
    parser.add_argument(
        "--threshold-days",
        type=int,
        default=2,
        help="Consider tickets stale if no update in this many days (default 2)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max issues to fetch from the API (default 500)",
    )
    args = parser.parse_args()

    assignees = args.assignee_id or [get_user_id()]
    window_days = get_window_days(args.window_days)
    start, end = compute_time_window(window_days)
    threshold = datetime.now(timezone.utc) - timedelta(days=args.threshold_days)

    issues = fetch_issues(assignees, start, end, args.limit)
    stale = []
    for issue in issues:
        latest_ts = issue.get("latest_message_time") or issue.get("updated_at")
        dt = parse_time(latest_ts)
        if not dt or dt < threshold:
            stale.append(issue)

    print(f"Assignees: {', '.join(assignees)}")
    print(f"Window: last {window_days} days ({start} → {end})")
    print(f"Stale threshold: {args.threshold_days} days")
    print(f"Issues fetched: {len(issues)}; Stale: {len(stale)}\n")

    if not stale:
        print("No stale issues. 🎉")
        return 0

    for issue in sorted(
        stale,
        key=lambda x: (x.get("latest_message_time") or x.get("updated_at") or ""),
    ):
        number = issue.get("number")
        title = issue.get("title", "(no title)")
        latest = issue.get("latest_message_time") or issue.get("updated_at")
        ago = humanize_timesince(latest)
        link = issue.get("link") or f"https://app.usepylon.com/issues?issueNumber={number}"
        state = (issue.get("state") or "").lower()
        print(f"[# {number}] {state}\n    {title}\n    last update {ago} · {link}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
