# Unbrowse - API Traffic Skill Generator

Auto-generate OpenClaw skills by capturing and analyzing HTTP API traffic.
Records HAR (HTTP Archive) files, extracts API patterns, and generates
ready-to-use OpenClaw skill definitions.

## Commands

### Capture

```
unbrowse capture <url> [--output <path>]
```
Capture HTTP traffic from a URL using headless browser CDP.
Saves HAR file for analysis.

### Analyze

```
unbrowse analyze <har-file> [--json]
```
Analyze a HAR file to extract API endpoints, auth patterns,
request/response schemas, and rate limits.

### Generate

```
unbrowse generate <har-file> --name <skill-name> [--output-dir <path>]
```
Generate a complete OpenClaw skill from a HAR file:
- SKILL.md with command definitions
- lib/api_client.py with typed API methods
- lib/auth.py with authentication handling
- scripts/<name>.py CLI entry point

### List

```
unbrowse list [--dir <skills-dir>]
```
List all generated skills and their status.

### Publish

```
unbrowse publish <skill-dir> [--price <usdc>] [--registry <url>]
```
Publish a generated skill to ClawHub marketplace.
Supports x402 USDC payments on Base/Solana.

## Environment Variables

- `UNBROWSE_OUTPUT_DIR` - Default output directory for generated skills (default: ./generated-skills)
- `UNBROWSE_CHROME_PATH` - Path to Chrome/Chromium for CDP capture
- `CLAWHUB_API_KEY` - API key for ClawHub marketplace publishing
- `CLAWHUB_WALLET` - USDC wallet address for receiving skill sale payments

## Dependencies

- Python 3.11+
- httpx (HTTP client)
- playwright (optional, for CDP capture)
