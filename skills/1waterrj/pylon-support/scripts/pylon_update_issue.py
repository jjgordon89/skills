#!/usr/bin/env python3
"""Update basic fields on a Pylon issue (state, tags, priority, etc.)."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from pylon_client import api_request


def parse_json_arg(value: str | None) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a Pylon issue")
    parser.add_argument("issue_id", help="Issue ID or number")
    parser.add_argument(
        "--state",
        help="New state (e.g., waiting_on_you, waiting_on_customer, on_hold, closed)",
    )
    parser.add_argument(
        "--priority",
        help="Custom field priority value if applicable (e.g., high, medium, low)",
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        help="Replace tags with this list (space separated)",
    )
    parser.add_argument(
        "--custom-fields",
        help="JSON object to merge into custom_fields (e.g., '{\"severity\":{\"value\":\"significant\"}}')",
    )
    parser.add_argument(
        "--assignee-id",
        help="Change assignee to this user id",
    )
    args = parser.parse_args()

    body: Dict[str, Any] = {}
    if args.state:
        body["state"] = args.state
    if args.tags is not None:
        body["tags"] = args.tags
    if args.assignee_id:
        body["assignee_id"] = args.assignee_id

    custom_fields: Dict[str, Any] = {}
    if args.priority:
        custom_fields.setdefault("priority", {})["value"] = args.priority
    custom_fields.update(parse_json_arg(args.custom_fields))
    if custom_fields:
        body["custom_fields"] = custom_fields

    if not body:
        raise SystemExit("No updates specified. Use --state/--tags/etc.")

    issue_path = f"/issues/{args.issue_id}"
    resp = api_request(issue_path, method="PATCH", data=body)
    print(json.dumps(resp, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
