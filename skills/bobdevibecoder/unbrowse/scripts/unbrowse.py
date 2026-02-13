#!/usr/bin/env python3
"""Unbrowse CLI - Auto-generate OpenClaw skills from API traffic."""

import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from lib.har_parser import load_har_file, parse_har, group_by_host, summarize_patterns
from lib.skill_generator import generate_skill, _sanitize_name


def cmd_analyze(har_path: str, as_json: bool = False):
    """Analyze a HAR file and show API patterns."""
    data = load_har_file(har_path)
    endpoints = parse_har(data)
    patterns = group_by_host(endpoints)

    if as_json:
        output = []
        for p in patterns:
            output.append({
                "host": p.host,
                "base_url": p.base_url,
                "auth_type": p.auth_type,
                "endpoint_count": len(p.endpoints),
                "endpoints": [
                    {
                        "method": ep.method,
                        "path": ep.path,
                        "query_params": [q.name for q in ep.query_params],
                        "has_body": ep.request_body is not None,
                        "response_status": ep.response.status if ep.response else None,
                        "calls": ep.count,
                    }
                    for ep in p.endpoints
                ],
            })
        print(json.dumps(output, indent=2))
    else:
        print(f"Analyzed {har_path}")
        print(f"Found {sum(len(p.endpoints) for p in patterns)} unique API endpoints across {len(patterns)} hosts")
        print(summarize_patterns(patterns))


def cmd_generate(har_path: str, name: str, output_dir: str, description: str = ""):
    """Generate an OpenClaw skill from a HAR file."""
    data = load_har_file(har_path)
    endpoints = parse_har(data)
    patterns = group_by_host(endpoints)

    if not patterns:
        print("No API patterns found in HAR file. Make sure it contains JSON API calls.")
        return

    if not description:
        hosts = ', '.join(p.host for p in patterns)
        total_eps = sum(len(p.endpoints) for p in patterns)
        description = f"Auto-generated skill for {hosts} ({total_eps} endpoints)."

    out_path = Path(output_dir) / _sanitize_name(name)
    files = generate_skill(name, description, patterns, str(out_path))

    print(f"Generated skill '{name}' at {out_path}")
    print(f"Files created:")
    for fname in sorted(files.keys()):
        fpath = out_path / fname
        size = fpath.stat().st_size if fpath.exists() else 0
        print(f"  {fname} ({size} bytes)")

    print(f"\nTo use:")
    print(f"  1. Copy {out_path} to /home/node/.openclaw/workspace/skills/{_sanitize_name(name)}/")
    print(f"  2. Set environment variables from .env.example")
    print(f"  3. Run: python3 scripts/{_sanitize_name(name)}.py --help")


def cmd_list(skills_dir: str):
    """List generated skills."""
    skills_path = Path(skills_dir)
    if not skills_path.exists():
        print(f"Skills directory not found: {skills_dir}")
        return

    skills = []
    for d in sorted(skills_path.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            # Count endpoints by reading the API client
            api_client = d / "lib" / "api_client.py"
            ep_count = 0
            if api_client.exists():
                content = api_client.read_text()
                ep_count = content.count("async def ")
            skills.append({
                "name": d.name,
                "path": str(d),
                "endpoints": ep_count,
                "has_env": (d / ".env.example").exists(),
            })

    if not skills:
        print("No generated skills found.")
        return

    print(f"Generated skills ({len(skills)}):\n")
    for s in skills:
        print(f"  {s['name']:30s}  {s['endpoints']} endpoints  {s['path']}")


def cmd_capture(url: str, output: str):
    """Capture HTTP traffic from a URL (requires playwright)."""
    try:
        from lib.capture import capture_traffic
        asyncio.run(capture_traffic(url, output))
    except ImportError:
        print("Traffic capture requires playwright. Install with:")
        print("  pip3 install playwright && playwright install chromium")
        print("")
        print("Alternatively, capture HAR manually:")
        print("  1. Open Chrome DevTools (F12)")
        print("  2. Go to Network tab")
        print("  3. Navigate to the URL")
        print("  4. Right-click in Network tab -> 'Save all as HAR'")
        print(f"  5. Run: unbrowse analyze <saved-file.har>")


def main():
    parser = argparse.ArgumentParser(
        description="Unbrowse - Auto-generate OpenClaw skills from API traffic"
    )
    subparsers = parser.add_subparsers(dest="command")

    # analyze
    analyze_p = subparsers.add_parser("analyze", help="Analyze a HAR file")
    analyze_p.add_argument("har_file", type=str, help="Path to HAR file")
    analyze_p.add_argument("--json", action="store_true", help="JSON output")

    # generate
    gen_p = subparsers.add_parser("generate", help="Generate skill from HAR")
    gen_p.add_argument("har_file", type=str, help="Path to HAR file")
    gen_p.add_argument("--name", type=str, required=True, help="Skill name")
    gen_p.add_argument("--description", type=str, default="", help="Skill description")
    gen_p.add_argument("--output-dir", type=str, default="./generated-skills", help="Output directory")

    # list
    list_p = subparsers.add_parser("list", help="List generated skills")
    list_p.add_argument("--dir", type=str, default="./generated-skills", help="Skills directory")

    # capture
    cap_p = subparsers.add_parser("capture", help="Capture HTTP traffic from URL")
    cap_p.add_argument("url", type=str, help="URL to capture traffic from")
    cap_p.add_argument("--output", type=str, default="capture.har", help="Output HAR file path")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args.har_file, getattr(args, "json", False))
    elif args.command == "generate":
        cmd_generate(args.har_file, args.name, args.output_dir, args.description)
    elif args.command == "list":
        cmd_list(args.dir)
    elif args.command == "capture":
        cmd_capture(args.url, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
