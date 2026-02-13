"""HTTP traffic capture via Chrome DevTools Protocol (CDP).

Requires playwright: pip3 install playwright && playwright install chromium
Falls back to manual HAR capture instructions if not available.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional


async def capture_traffic(url: str, output_path: str, wait_seconds: int = 10) -> str:
    """Capture HTTP traffic from a URL using headless Chromium.

    Args:
        url: URL to navigate to and capture traffic from
        output_path: Path to save the HAR file
        wait_seconds: How long to wait for network activity (default 10s)

    Returns:
        Path to the saved HAR file
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "playwright is required for traffic capture. Install with:\n"
            "  pip3 install playwright && playwright install chromium"
        )

    entries = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture all network requests and responses
        async def on_response(response):
            try:
                request = response.request
                # Build HAR entry
                entry = {
                    "startedDateTime": "",
                    "request": {
                        "method": request.method,
                        "url": request.url,
                        "headers": [
                            {"name": k, "value": v}
                            for k, v in request.headers.items()
                        ],
                        "queryString": [],
                        "postData": None,
                    },
                    "response": {
                        "status": response.status,
                        "statusText": response.status_text,
                        "headers": [
                            {"name": k, "value": v}
                            for k, v in response.headers.items()
                        ],
                        "content": {
                            "size": 0,
                            "mimeType": response.headers.get("content-type", ""),
                        },
                    },
                }

                # Try to get request body for POST/PUT
                if request.method in ("POST", "PUT", "PATCH"):
                    try:
                        post_data = request.post_data
                        if post_data:
                            entry["request"]["postData"] = {
                                "mimeType": request.headers.get("content-type", ""),
                                "text": post_data,
                            }
                    except Exception:
                        pass

                # Try to get response body
                try:
                    body = await response.text()
                    entry["response"]["content"]["text"] = body
                    entry["response"]["content"]["size"] = len(body)
                except Exception:
                    pass

                entries.append(entry)
            except Exception:
                pass  # Skip entries that fail to capture

        page.on("response", on_response)

        # Navigate and wait
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception:
            # Still try to get what we captured even if nav times out
            pass

        print(f"Waiting {wait_seconds}s for additional network activity...")
        await asyncio.sleep(wait_seconds)

        await browser.close()

    # Build HAR structure
    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "unbrowse", "version": "1.0.0"},
            "entries": entries,
        }
    }

    # Save
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(har, f, indent=2)

    print(f"Captured {len(entries)} requests -> {output_path}")
    return str(out_path)
