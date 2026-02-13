"""Skill generator - creates OpenClaw skill files from API patterns."""

import json
import os
import re
from pathlib import Path
from typing import Optional

from .har_parser import APIPattern, APIEndpoint


def _sanitize_name(name: str) -> str:
    """Convert a name to a valid Python identifier."""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_').lower()
    if name and name[0].isdigit():
        name = '_' + name
    return name or 'unnamed'


def _path_to_method_name(method: str, path: str) -> str:
    """Convert an HTTP method+path to a Python method name."""
    parts = path.strip('/').split('/')
    has_id = '{id}' in parts
    # Remove ID placeholders
    clean = [p for p in parts if p != '{id}']
    if not clean:
        clean = ['root']
    name_parts = []
    for p in clean[-2:]:  # Use last 2 path segments
        name_parts.append(_sanitize_name(p))
    prefix = method.lower()
    if prefix == 'get':
        prefix = 'get'
    elif prefix == 'post':
        prefix = 'create'
    elif prefix == 'put' or prefix == 'patch':
        prefix = 'update'
    elif prefix == 'delete':
        prefix = 'delete'
    base = f"{prefix}_{'_'.join(name_parts)}"
    # Disambiguate: GET /users vs GET /users/{id}
    if has_id and prefix in ('get', 'update', 'delete'):
        base += '_by_id'
    return base


def _schema_to_type_hint(schema: Optional[dict]) -> str:
    """Convert a JSON schema to a Python type hint string."""
    if not schema:
        return 'Any'
    t = schema.get('type', 'any')
    if t == 'string':
        return 'str'
    elif t == 'integer':
        return 'int'
    elif t == 'number':
        return 'float'
    elif t == 'boolean':
        return 'bool'
    elif t == 'array':
        items = _schema_to_type_hint(schema.get('items'))
        return f'list[{items}]'
    elif t == 'object':
        return 'dict'
    elif t == 'null':
        return 'None'
    return 'Any'


def generate_skill_md(name: str, description: str, patterns: list[APIPattern]) -> str:
    """Generate SKILL.md content for the skill."""
    lines = [f"# {name}", "", description, "", "## Commands", ""]

    for pattern in patterns:
        lines.append(f"### {pattern.host}")
        lines.append("")
        for ep in pattern.endpoints:
            method_name = _path_to_method_name(ep.method, ep.path)
            lines.append(f"#### {method_name}")
            lines.append(f"```")
            lines.append(f"{name} {method_name}")

            # Add query params as CLI args
            for qp in ep.query_params:
                lines.append(f"  --{qp.name} <{qp.name}>")
            # Add body params
            if ep.request_body and ep.request_body.schema:
                props = ep.request_body.schema.get('properties', {})
                for prop_name in list(props.keys())[:10]:
                    lines.append(f"  --{prop_name} <{prop_name}>")
            lines.append(f"```")
            lines.append(f"{ep.method} {ep.path}")
            if ep.response and ep.response.schema:
                resp_type = _schema_to_type_hint(ep.response.schema)
                lines.append(f"Returns: {resp_type}")
            lines.append("")

    # Environment variables
    lines.extend(["## Environment Variables", ""])
    env_vars = set()
    for pattern in patterns:
        skill_prefix = _sanitize_name(name).upper()
        if pattern.auth_type == 'bearer':
            env_vars.add(f"`{skill_prefix}_API_TOKEN` - Bearer token for {pattern.host}")
        elif pattern.auth_type == 'api_key':
            env_vars.add(f"`{skill_prefix}_API_KEY` - API key for {pattern.host}")
        elif pattern.auth_type == 'cookie':
            env_vars.add(f"`{skill_prefix}_COOKIE` - Session cookie for {pattern.host}")
        env_vars.add(f"`{skill_prefix}_BASE_URL` - Base URL override (default: {pattern.base_url})")
    for ev in sorted(env_vars):
        lines.append(f"- {ev}")
    lines.append("")

    return "\n".join(lines)


def generate_api_client(name: str, patterns: list[APIPattern]) -> str:
    """Generate Python API client code from patterns."""
    skill_prefix = _sanitize_name(name).upper()
    lines = [
        f'"""Auto-generated API client for {name}."""',
        '',
        'import os',
        'import httpx',
        'from typing import Any, Optional',
        '',
    ]

    for pattern in patterns:
        class_name = _sanitize_name(pattern.host.split('.')[0]).title() + 'Client'
        lines.extend([
            '',
            f'class {class_name}:',
            f'    """API client for {pattern.host}."""',
            '',
            f'    def __init__(self, base_url: str = "{pattern.base_url}", timeout: float = 30.0):',
            f'        self.base_url = os.getenv("{skill_prefix}_BASE_URL", base_url)',
            f'        self.timeout = timeout',
        ])

        # Auth setup
        if pattern.auth_type == 'bearer':
            lines.extend([
                f'        self.token = os.getenv("{skill_prefix}_API_TOKEN", "")',
                f'        if not self.token:',
                f'            raise ValueError("{skill_prefix}_API_TOKEN not set")',
            ])
        elif pattern.auth_type == 'api_key':
            lines.extend([
                f'        self.api_key = os.getenv("{skill_prefix}_API_KEY", "")',
                f'        if not self.api_key:',
                f'            raise ValueError("{skill_prefix}_API_KEY not set")',
            ])
        elif pattern.auth_type == 'cookie':
            lines.extend([
                f'        self.cookie = os.getenv("{skill_prefix}_COOKIE", "")',
            ])

        lines.append('')

        # _headers method
        lines.extend([
            '    def _headers(self) -> dict:',
            '        headers = {',
        ])
        for h in pattern.common_headers:
            lines.append(f'            "{h.name}": "{h.value}",')
        if pattern.auth_type == 'bearer':
            lines.append(f'            "Authorization": f"Bearer {{self.token}}",')
        elif pattern.auth_type == 'api_key':
            header_name = pattern.auth_header or 'X-API-Key'
            lines.append(f'            "{header_name}": self.api_key,')
        elif pattern.auth_type == 'cookie':
            lines.append(f'            "Cookie": self.cookie,')
        lines.extend([
            '        }',
            '        return headers',
            '',
        ])

        # Generate methods for each endpoint
        for ep in pattern.endpoints:
            method_name = _path_to_method_name(ep.method, ep.path)

            # Build method signature
            params = ['self']
            # Path params
            path_params = re.findall(r'\{(\w+)\}', ep.path)
            for pp in path_params:
                params.append(f'{pp}: str')
            # Query params
            for qp in ep.query_params:
                param_name = _sanitize_name(qp.name)
                params.append(f'{param_name}: Optional[str] = None')
            # Body params
            body_props = []
            if ep.request_body and ep.request_body.schema:
                props = ep.request_body.schema.get('properties', {})
                for prop_name, prop_schema in list(props.items())[:10]:
                    safe_name = _sanitize_name(prop_name)
                    type_hint = _schema_to_type_hint(prop_schema)
                    params.append(f'{safe_name}: Optional[{type_hint}] = None')
                    body_props.append((prop_name, safe_name))

            sig = ', '.join(params)
            return_type = _schema_to_type_hint(ep.response.schema if ep.response else None)

            lines.extend([
                f'    async def {method_name}({sig}) -> {return_type}:',
                f'        """{ep.method} {ep.path}"""',
            ])

            # Build URL
            url_path = ep.path
            for pp in path_params:
                url_path = url_path.replace(f'{{{pp}}}', f'{{{pp}}}')
            lines.append(f'        url = f"{{self.base_url}}{url_path}"')

            # Query params
            if ep.query_params:
                lines.append('        params = {}')
                for qp in ep.query_params:
                    safe = _sanitize_name(qp.name)
                    lines.append(f'        if {safe} is not None:')
                    lines.append(f'            params["{qp.name}"] = {safe}')

            # Body
            if body_props:
                lines.append('        body = {}')
                for orig, safe in body_props:
                    lines.append(f'        if {safe} is not None:')
                    lines.append(f'            body["{orig}"] = {safe}')

            # Make request
            lines.append('        async with httpx.AsyncClient(timeout=self.timeout) as client:')
            http_method = ep.method.lower()
            req_args = ['url', 'headers=self._headers()']
            if ep.query_params:
                req_args.append('params=params')
            if body_props:
                req_args.append('json=body')
            args_str = ', '.join(req_args)
            lines.extend([
                f'            resp = await client.{http_method}({args_str})',
                f'            resp.raise_for_status()',
            ])

            # Return
            if ep.response and ep.response.mime_type in ('application/json', 'text/json'):
                lines.append('            return resp.json()')
            else:
                lines.append('            return resp.text')
            lines.append('')

    return '\n'.join(lines)


def generate_cli_script(name: str, patterns: list[APIPattern]) -> str:
    """Generate CLI entry point script."""
    safe_name = _sanitize_name(name)
    lines = [
        '#!/usr/bin/env python3',
        f'"""Auto-generated CLI for {name}."""',
        '',
        'import sys',
        'import asyncio',
        'import argparse',
        'import json',
        'from pathlib import Path',
        '',
        'sys.path.insert(0, str(Path(__file__).parent.parent))',
        '',
        'from dotenv import load_dotenv',
        'load_dotenv(Path(__file__).parent.parent / ".env")',
        '',
        f'from lib.api_client import *',
        '',
        '',
        'def main():',
        f'    parser = argparse.ArgumentParser(description="{name} - auto-generated API skill")',
        '    subparsers = parser.add_subparsers(dest="command")',
        '',
    ]

    for pattern in patterns:
        class_name = _sanitize_name(pattern.host.split('.')[0]).title() + 'Client'
        for ep in pattern.endpoints:
            method_name = _path_to_method_name(ep.method, ep.path)
            lines.extend([
                f'    # {method_name}',
                f'    p_{method_name} = subparsers.add_parser("{method_name}", help="{ep.method} {ep.path}")',
            ])
            # Path params
            for pp in re.findall(r'\{(\w+)\}', ep.path):
                lines.append(f'    p_{method_name}.add_argument("{pp}", type=str)')
            # Query params as optional
            for qp in ep.query_params:
                lines.append(f'    p_{method_name}.add_argument("--{qp.name}", type=str, default=None)')
            # Body params as optional
            if ep.request_body and ep.request_body.schema:
                for prop_name in list(ep.request_body.schema.get('properties', {}).keys())[:10]:
                    lines.append(f'    p_{method_name}.add_argument("--{prop_name}", type=str, default=None)')
            lines.append(f'    p_{method_name}.add_argument("--json", action="store_true")')
            lines.append('')

    lines.extend([
        '    args = parser.parse_args()',
        '    if not args.command:',
        '        parser.print_help()',
        '        return',
        '',
        '    # Dispatch',
    ])

    for pattern in patterns:
        class_name = _sanitize_name(pattern.host.split('.')[0]).title() + 'Client'
        for ep in pattern.endpoints:
            method_name = _path_to_method_name(ep.method, ep.path)
            lines.extend([
                f'    if args.command == "{method_name}":',
                f'        client = {class_name}()',
            ])
            # Build call args
            call_args = []
            for pp in re.findall(r'\{(\w+)\}', ep.path):
                call_args.append(f'args.{pp}')
            for qp in ep.query_params:
                safe = _sanitize_name(qp.name)
                call_args.append(f'{safe}=args.{qp.name}')
            if ep.request_body and ep.request_body.schema:
                for prop_name in list(ep.request_body.schema.get('properties', {}).keys())[:10]:
                    safe = _sanitize_name(prop_name)
                    call_args.append(f'{safe}=args.{prop_name}')
            args_str = ', '.join(call_args)
            lines.extend([
                f'        result = asyncio.run(client.{method_name}({args_str}))',
                f'        if getattr(args, "json", False):',
                f'            print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)',
                f'        else:',
                f'            print(result)',
                f'        return',
                '',
            ])

    lines.extend([
        '',
        'if __name__ == "__main__":',
        '    main()',
        '',
    ])
    return '\n'.join(lines)


def generate_auth_module(name: str, patterns: list[APIPattern]) -> str:
    """Generate auth handling module."""
    skill_prefix = _sanitize_name(name).upper()
    lines = [
        f'"""Authentication handling for {name}."""',
        '',
        'import os',
        'import json',
        'from pathlib import Path',
        'from typing import Optional',
        '',
        '',
        'def load_credentials(name: str) -> dict:',
        '    """Load credentials from env vars or config file."""',
        '    # Try env vars first',
        f'    prefix = "{skill_prefix}"',
        '    creds = {}',
        '    for key in ("API_TOKEN", "API_KEY", "COOKIE", "USERNAME", "PASSWORD"):',
        '        env_key = f"{prefix}_{key}"',
        '        val = os.getenv(env_key)',
        '        if val:',
        '            creds[key.lower()] = val',
        '    if creds:',
        '        return creds',
        '',
        '    # Try config file',
        '    config_path = Path(__file__).parent.parent / "auth.json"',
        '    if config_path.exists():',
        '        with open(config_path) as f:',
        '            return json.load(f)',
        '',
        '    return {}',
        '',
        '',
        'def save_credentials(creds: dict) -> None:',
        '    """Save credentials to config file."""',
        '    config_path = Path(__file__).parent.parent / "auth.json"',
        '    with open(config_path, "w") as f:',
        '        json.dump(creds, f, indent=2)',
        '    # Restrict permissions',
        '    config_path.chmod(0o600)',
        '',
    ]
    return '\n'.join(lines)


def generate_skill(
    name: str,
    description: str,
    patterns: list[APIPattern],
    output_dir: str,
) -> dict[str, str]:
    """Generate a complete OpenClaw skill and write to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lib").mkdir(exist_ok=True)
    (out / "scripts").mkdir(exist_ok=True)

    files = {}

    # SKILL.md
    skill_md = generate_skill_md(name, description, patterns)
    (out / "SKILL.md").write_text(skill_md)
    files["SKILL.md"] = skill_md

    # lib/__init__.py
    (out / "lib" / "__init__.py").write_text("")
    files["lib/__init__.py"] = ""

    # lib/api_client.py
    api_client = generate_api_client(name, patterns)
    (out / "lib" / "api_client.py").write_text(api_client)
    files["lib/api_client.py"] = api_client

    # lib/auth.py
    auth = generate_auth_module(name, patterns)
    (out / "lib" / "auth.py").write_text(auth)
    files["lib/auth.py"] = auth

    # scripts/<name>.py
    cli = generate_cli_script(name, patterns)
    script_path = out / "scripts" / f"{_sanitize_name(name)}.py"
    script_path.write_text(cli)
    files[f"scripts/{_sanitize_name(name)}.py"] = cli

    # .env template
    env_template_lines = [f"# {name} - Environment Variables", ""]
    for pattern in patterns:
        if pattern.auth_type == 'bearer':
            env_template_lines.append(f'{_sanitize_name(name).upper()}_API_TOKEN=')
        elif pattern.auth_type == 'api_key':
            env_template_lines.append(f'{_sanitize_name(name).upper()}_API_KEY=')
        elif pattern.auth_type == 'cookie':
            env_template_lines.append(f'{_sanitize_name(name).upper()}_COOKIE=')
        env_template_lines.append(f'{_sanitize_name(name).upper()}_BASE_URL={pattern.base_url}')
    env_template = '\n'.join(env_template_lines) + '\n'
    (out / ".env.example").write_text(env_template)
    files[".env.example"] = env_template

    return files
