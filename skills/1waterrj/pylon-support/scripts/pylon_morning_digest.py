#!/usr/bin/env python3
"""Generate a markdown-ready morning digest for Jordan + team."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Sequence

from pylon_client import api_request
from pylon_utils import (
    compute_time_window,
    get_user_id,
    get_window_days,
    humanize_timesince,
)

DEFAULT_TEAM = {
    "kody": "d6488264-6c04-4024-885b-241a549eb4d8",
    "phil": "dd27ec5f-946f-49a1-9380-19af42af274d",
    "skyler": "c3669447-14b6-4d7e-a664-69816eff4a48",
    "jacob": "c7024596-5593-44cf-8cb9-856fa06625c6",
    "lindsay": "6f9fdc21-f7f0-49c7-904c-88e329cf4de2",
}


def fetch_issues(assignee_ids: Sequence[str], start: str, end: str, limit: int) -> List[dict]:
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


def summarize_user(issues: List[dict], stale_cutoff: datetime) -> str:
    counts = Counter((issue.get("state") or "unknown").lower() for issue in issues)
    waiting = [i for i in issues if (i.get("state") or "").lower() == "waiting_on_you"]
    stale: List[dict] = []
    for issue in issues:
        latest = issue.get("latest_message_time") or issue.get("updated_at")
        dt = parse_time(latest)
        if not dt or dt < stale_cutoff:
            stale.append(issue)

    body = []
    if counts:
        totals = ", ".join(f"{state}:{count}" for state, count in counts.items())
        body.append(f"- Totals: {totals}")
    if waiting:
        body.append("- Waiting on you:")
        for issue in waiting[:5]:
            number = issue.get("number")
            title = issue.get("title", "(no title)")
            ago = humanize_timesince(issue.get("latest_message_time") or issue.get("updated_at"))
            link = issue.get("link") or f"https://app.usepylon.com/issues?issueNumber={number}"
            body.append(f"  - #{number}: {title} (updated {ago}) · {link}")
    if stale:
        body.append("- Stale:")
        for issue in stale[:5]:
            number = issue.get("number")
            title = issue.get("title", "(no title)")
            ago = humanize_timesince(issue.get("latest_message_time") or issue.get("updated_at"))
            state = (issue.get("state") or "").lower()
            link = issue.get("link") or f"https://app.usepylon.com/issues?issueNumber={number}"
            body.append(f"  - #{number} [{state}] {title} (updated {ago}) · {link}")
    if not body:
        body.append("- No active issues in window.")

    return "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Morning digest")
    parser.add_argument(
        "--team",
        action="append",
        metavar="NAME=ID",
        help="Override/add team members",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        help="Lookback window (default config or 30)",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=2,
        help="Consider tickets stale after this many days (default 2)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max issues to fetch (default 1000)",
    )
    args = parser.parse_args()

    team = dict(DEFAULT_TEAM)
    if args.team:
        for entry in args.team:
            if "=" not in entry:
                raise SystemExit(f"Invalid --team entry: {entry}")
            name, uid = entry.split("=", 1)
            team[name.strip()] = uid.strip()

    me = get_user_id()
    window_days = get_window_days(args.window_days)
    start, end = compute_time_window(window_days)
    issues = fetch_issues([me] + list(team.values()), start, end, args.limit)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=args.stale_days)

    # Split issues
    my_issues = [i for i in issues if ((i.get("assignee") or {}).get("id")) == me]
    team_issues = defaultdict(list)
    for issue in issues:
        assignee = ((issue.get("assignee") or {}).get("id"))
        for name, uid in team.items():
            if assignee == uid:
                team_issues[name].append(issue)
                break

    print(f"# Daily Digest ({datetime.now().strftime('%Y-%m-%d')})\n")
    print(f"Window: last {window_days} days ({start} → {end}); stale>{args.stale_days}d\n")

    print("## Jordan")
    summary = summarize_user(my_issues, stale_cutoff)
    print(summary)
    print("")

    print("## Team")
    for name, uid in team.items():
        issues_for_user = team_issues.get(name, [])
        counts = Counter((issue.get("state") or "unknown").lower() for issue in issues_for_user)
        stale = []
        for issue in issues_for_user:
            latest = issue.get("latest_message_time") or issue.get("updated_at")
            dt = parse_time(latest)
            if not dt or dt < stale_cutoff:
                stale.append(issue)
        count_line = ", ".join(f"{state}:{count}" for state, count in counts.items()) or "no issues"
        print(f"### {name} ({count_line})")
        if stale:
            for issue in stale[:3]:
                number = issue.get("number")
                title = issue.get("title", "(no title)")
                ago = humanize_timesince(issue.get("latest_message_time") or issue.get("updated_at"))
                state = (issue.get("state") or "").lower()
                link = issue.get("link") or f"https://app.usepylon.com/issues?issueNumber={number}"
                print(f"- #{number} [{state}] {title} (updated {ago}) · {link}")
        else:
            print("- No stale issues.")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
