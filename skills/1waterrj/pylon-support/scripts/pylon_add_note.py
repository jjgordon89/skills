#!/usr/bin/env python3
"""Add an internal or external message to a Pylon issue."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pylon_client import api_request


def load_body(text: str | None, file_path: str | None) -> str:
    if text and file_path:
        raise SystemExit("Specify either --text or --file, not both")
    if text:
        return text
    if file_path:
        return Path(file_path).read_text()
    raise SystemExit("Provide --text or --file with the message contents")


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a note or reply to an issue")
    parser.add_argument("issue_id", help="Issue ID or number")
    parser.add_argument(
        "--text",
        help="Message body (plain text). Use markdown-style newlines; will be wrapped in <p> tags.",
    )
    parser.add_argument(
        "--file",
        help="Path to a file containing the message HTML fragment",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Mark as an internal/private note (default: customer-visible)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Treat --text/--file contents as HTML; otherwise simple paragraph wrapping",
    )
    args = parser.parse_args()

    body_raw = load_body(args.text, args.file)
    if args.html:
        message_html = body_raw
    else:
        escaped = body_raw.replace("\n", "<br>")
        message_html = f"<p>{escaped}</p>"

    payload = {
        "message_html": message_html,
        "is_private": args.private,
    }
    issue_path = f"/issues/{args.issue_id}/messages"
    resp = api_request(issue_path, method="POST", data=payload)
    print(json.dumps(resp, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
