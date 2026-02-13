"""HAR (HTTP Archive) file parser - extracts API patterns from recorded traffic."""

import json
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, parse_qs


@dataclass
class Header:
    name: str
    value: str


@dataclass
class QueryParam:
    name: str
    value: str
    example: str


@dataclass
class RequestBody:
    mime_type: str
    text: Optional[str] = None
    schema: Optional[dict] = None


@dataclass
class ResponseBody:
    status: int
    mime_type: str
    size: int
    text: Optional[str] = None
    schema: Optional[dict] = None


@dataclass
class APIEndpoint:
    method: str
    url: str
    path: str
    host: str
    query_params: list[QueryParam] = field(default_factory=list)
    request_headers: list[Header] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    response: Optional[ResponseBody] = None
    auth_type: Optional[str] = None  # bearer, api_key, cookie, basic, custom
    auth_header: Optional[str] = None
    count: int = 1  # how many times this endpoint was called


@dataclass
class APIPattern:
    """Grouped pattern for an API host."""
    host: str
    base_url: str
    auth_type: Optional[str] = None
    auth_header: Optional[str] = None
    endpoints: list[APIEndpoint] = field(default_factory=list)
    common_headers: list[Header] = field(default_factory=list)
    rate_limit_hints: dict = field(default_factory=dict)


# Static/non-API content types to skip
SKIP_CONTENT_TYPES = {
    "text/html", "text/css", "text/javascript", "application/javascript",
    "image/png", "image/jpeg", "image/gif", "image/svg+xml", "image/webp",
    "font/woff", "font/woff2", "application/font-woff",
    "application/octet-stream",
}

# Static file extensions to skip
SKIP_EXTENSIONS = {
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".webp",
}

# Headers that are just noise
SKIP_HEADERS = {
    "accept-encoding", "accept-language", "cache-control", "connection",
    "host", "origin", "referer", "sec-ch-ua", "sec-ch-ua-mobile",
    "sec-ch-ua-platform", "sec-fetch-dest", "sec-fetch-mode",
    "sec-fetch-site", "upgrade-insecure-requests", "user-agent",
    "pragma", "dnt", "te", "if-none-match", "if-modified-since",
}


def _infer_schema(obj, max_depth: int = 3) -> dict:
    """Infer a JSON schema from a sample object."""
    if max_depth <= 0:
        return {"type": "any"}
    if obj is None:
        return {"type": "null"}
    if isinstance(obj, bool):
        return {"type": "boolean"}
    if isinstance(obj, int):
        return {"type": "integer"}
    if isinstance(obj, float):
        return {"type": "number"}
    if isinstance(obj, str):
        return {"type": "string"}
    if isinstance(obj, list):
        if len(obj) == 0:
            return {"type": "array", "items": {"type": "any"}}
        return {"type": "array", "items": _infer_schema(obj[0], max_depth - 1)}
    if isinstance(obj, dict):
        properties = {}
        for k, v in list(obj.items())[:20]:  # limit to 20 fields
            properties[k] = _infer_schema(v, max_depth - 1)
        return {"type": "object", "properties": properties}
    return {"type": "any"}


def _detect_auth(headers: list[dict]) -> tuple[Optional[str], Optional[str]]:
    """Detect authentication type from request headers."""
    for h in headers:
        name = h.get("name", "").lower()
        value = h.get("value", "")
        if name == "authorization":
            if value.lower().startswith("bearer "):
                return "bearer", "Authorization"
            elif value.lower().startswith("basic "):
                return "basic", "Authorization"
            else:
                return "custom", "Authorization"
        if name == "x-api-key":
            return "api_key", "X-API-Key"
        if name in ("x-auth-token", "x-access-token"):
            return "api_key", h.get("name", "")
    # Check for cookie-based auth
    for h in headers:
        if h.get("name", "").lower() == "cookie":
            cookie_val = h.get("value", "")
            if any(k in cookie_val for k in ["session", "token", "auth", "sid"]):
                return "cookie", "Cookie"
    return None, None


def _should_skip_entry(entry: dict) -> bool:
    """Check if a HAR entry should be skipped (static assets, etc.)."""
    request = entry.get("request", {})
    response = entry.get("response", {})
    url = request.get("url", "")
    parsed = urlparse(url)

    # Skip static file extensions
    path_lower = parsed.path.lower()
    for ext in SKIP_EXTENSIONS:
        if path_lower.endswith(ext):
            return True

    # Skip based on response content type
    resp_content = response.get("content", {})
    mime = resp_content.get("mimeType", "").split(";")[0].strip()
    if mime in SKIP_CONTENT_TYPES:
        return True

    # Skip non-2xx responses (except 3xx redirects which might be interesting)
    status = response.get("status", 0)
    if status < 200 or status >= 400:
        return True

    return False


def _normalize_path(path: str) -> str:
    """Normalize path by replacing likely IDs with placeholders."""
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        # UUID pattern
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', part, re.I):
            normalized.append("{id}")
        # Numeric ID
        elif re.match(r'^\d+$', part) and len(part) > 2:
            normalized.append("{id}")
        # Long hex string (hash/token)
        elif re.match(r'^[0-9a-f]{16,}$', part, re.I):
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


def parse_har(har_data: dict) -> list[APIEndpoint]:
    """Parse a HAR file and extract API endpoints."""
    entries = har_data.get("log", {}).get("entries", [])
    endpoints = []

    for entry in entries:
        if _should_skip_entry(entry):
            continue

        request = entry.get("request", {})
        response = entry.get("response", {})
        url = request.get("url", "")
        parsed = urlparse(url)
        method = request.get("method", "GET").upper()

        # Only care about API-like requests
        resp_content = response.get("content", {})
        resp_mime = resp_content.get("mimeType", "").split(";")[0].strip()
        if resp_mime not in ("application/json", "text/json", "application/xml", "text/xml", "text/plain", ""):
            continue

        # Extract query params
        query_params = []
        for qp in request.get("queryString", []):
            query_params.append(QueryParam(
                name=qp.get("name", ""),
                value=qp.get("value", ""),
                example=qp.get("value", ""),
            ))

        # Extract meaningful headers
        req_headers = []
        for h in request.get("headers", []):
            if h.get("name", "").lower() not in SKIP_HEADERS:
                req_headers.append(Header(name=h["name"], value=h.get("value", "")))

        # Detect auth
        auth_type, auth_header = _detect_auth(request.get("headers", []))

        # Request body
        req_body = None
        post_data = request.get("postData")
        if post_data:
            text = post_data.get("text", "")
            schema = None
            if text:
                try:
                    parsed_body = json.loads(text)
                    schema = _infer_schema(parsed_body)
                except (json.JSONDecodeError, ValueError):
                    pass
            req_body = RequestBody(
                mime_type=post_data.get("mimeType", ""),
                text=text[:500] if text else None,
                schema=schema,
            )

        # Response body
        resp_body = None
        resp_text = resp_content.get("text", "")
        resp_schema = None
        if resp_text and resp_mime in ("application/json", "text/json"):
            try:
                parsed_resp = json.loads(resp_text)
                resp_schema = _infer_schema(parsed_resp)
            except (json.JSONDecodeError, ValueError):
                pass
        resp_body = ResponseBody(
            status=response.get("status", 0),
            mime_type=resp_mime,
            size=resp_content.get("size", 0),
            text=resp_text[:500] if resp_text else None,
            schema=resp_schema,
        )

        path = _normalize_path(parsed.path)
        endpoints.append(APIEndpoint(
            method=method,
            url=url,
            path=path,
            host=parsed.netloc,
            query_params=query_params,
            request_headers=req_headers,
            request_body=req_body,
            response=resp_body,
            auth_type=auth_type,
            auth_header=auth_header,
        ))

    return _deduplicate_endpoints(endpoints)


def _deduplicate_endpoints(endpoints: list[APIEndpoint]) -> list[APIEndpoint]:
    """Merge duplicate endpoint calls (same method+path)."""
    seen: dict[str, APIEndpoint] = {}
    for ep in endpoints:
        key = f"{ep.method}:{ep.host}:{ep.path}"
        if key in seen:
            seen[key].count += 1
        else:
            seen[key] = ep
    return list(seen.values())


def group_by_host(endpoints: list[APIEndpoint]) -> list[APIPattern]:
    """Group endpoints by host into API patterns."""
    host_map: dict[str, list[APIEndpoint]] = {}
    for ep in endpoints:
        if ep.host not in host_map:
            host_map[ep.host] = []
        host_map[ep.host].append(ep)

    patterns = []
    for host, eps in host_map.items():
        # Detect common auth across endpoints
        auth_types = [ep.auth_type for ep in eps if ep.auth_type]
        auth_headers = [ep.auth_header for ep in eps if ep.auth_header]
        common_auth = max(set(auth_types), key=auth_types.count) if auth_types else None
        common_auth_header = max(set(auth_headers), key=auth_headers.count) if auth_headers else None

        # Find common headers
        if len(eps) > 1:
            header_counts: dict[str, int] = {}
            header_values: dict[str, str] = {}
            for ep in eps:
                for h in ep.request_headers:
                    hkey = h.name.lower()
                    header_counts[hkey] = header_counts.get(hkey, 0) + 1
                    header_values[hkey] = h.value
            common_headers = [
                Header(name=k, value=header_values[k])
                for k, count in header_counts.items()
                if count >= len(eps) * 0.8  # present in 80%+ of requests
                and k.lower() not in ("authorization", "cookie", "content-type")
            ]
        else:
            common_headers = []

        # Detect rate limit hints from response headers
        rate_hints = {}
        for ep in eps:
            if ep.response:
                # Check common rate limit response patterns
                pass  # Would need response headers in HAR

        # Determine base URL
        schemes = set()
        for ep in eps:
            parsed = urlparse(ep.url)
            schemes.add(parsed.scheme)
        scheme = "https" if "https" in schemes else "http"

        patterns.append(APIPattern(
            host=host,
            base_url=f"{scheme}://{host}",
            auth_type=common_auth,
            auth_header=common_auth_header,
            endpoints=eps,
            common_headers=common_headers,
            rate_limit_hints=rate_hints,
        ))

    return patterns


def load_har_file(path: str) -> dict:
    """Load and validate a HAR file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "log" not in data:
        raise ValueError(f"Invalid HAR file: missing 'log' key in {path}")
    if "entries" not in data["log"]:
        raise ValueError(f"Invalid HAR file: missing 'log.entries' in {path}")
    return data


def summarize_patterns(patterns: list[APIPattern]) -> str:
    """Generate a human-readable summary of API patterns."""
    lines = []
    for p in patterns:
        lines.append(f"\n=== {p.host} ({len(p.endpoints)} endpoints) ===")
        lines.append(f"Base URL: {p.base_url}")
        if p.auth_type:
            lines.append(f"Auth: {p.auth_type} via {p.auth_header}")
        if p.common_headers:
            lines.append(f"Common headers: {', '.join(h.name for h in p.common_headers)}")
        lines.append("")
        for ep in sorted(p.endpoints, key=lambda e: (e.path, e.method)):
            params = ""
            if ep.query_params:
                params = f" ?{'&'.join(q.name for q in ep.query_params)}"
            body = ""
            if ep.request_body and ep.request_body.schema:
                fields = list(ep.request_body.schema.get("properties", {}).keys())[:5]
                body = f" body={{{', '.join(fields)}}}"
            resp = ""
            if ep.response:
                resp = f" -> {ep.response.status}"
                if ep.response.schema and ep.response.schema.get("type") == "object":
                    fields = list(ep.response.schema.get("properties", {}).keys())[:5]
                    resp += f" {{{', '.join(fields)}}}"
            calls = f" (x{ep.count})" if ep.count > 1 else ""
            lines.append(f"  {ep.method:6s} {ep.path}{params}{body}{resp}{calls}")
    return "\n".join(lines)
