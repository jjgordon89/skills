#!/bin/bash

# Danube MCP Setup for OpenClaw
# Adds Danube MCP configuration to OpenClaw config
#
# Security notes:
# - API key is stored ONLY in ~/.openclaw/.env (not in openclaw.json)
# - Config references the env var at runtime via shell expansion
# - mcp-remote is installed explicitly before use (no npx -y auto-install)

set -e

echo "Danube MCP Setup"
echo "================"
echo ""

# Check if DANUBE_API_KEY is set (in env or .env file)
OPENCLAW_ENV_FILE="$HOME/.openclaw/.env"

if [ -z "$DANUBE_API_KEY" ]; then
    # Not in current environment, check if it exists in OpenClaw's .env
    if [ -f "$OPENCLAW_ENV_FILE" ] && grep -q "DANUBE_API_KEY" "$OPENCLAW_ENV_FILE"; then
        echo "[OK] DANUBE_API_KEY found in $OPENCLAW_ENV_FILE"
    else
        echo "[!] DANUBE_API_KEY not found"
        echo ""
        echo "Get your API key from: https://danubeai.com/dashboard -> Settings -> API Keys"
        echo ""
        read -p "Enter your Danube API key: " api_key

        if [ -z "$api_key" ]; then
            echo "[ERROR] API key is required"
            exit 1
        fi

        # Create .openclaw directory if it doesn't exist
        mkdir -p "$HOME/.openclaw"

        # Add to OpenClaw's .env file (key stays here, not in config)
        echo "DANUBE_API_KEY=\"$api_key\"" >> "$OPENCLAW_ENV_FILE"
        echo "[OK] Added DANUBE_API_KEY to $OPENCLAW_ENV_FILE"
    fi
else
    echo "[OK] DANUBE_API_KEY is set in environment"
fi

# Install mcp-remote globally (explicit install, no auto-download at runtime)
echo ""
echo "Installing mcp-remote bridge..."
if command -v mcp-remote &> /dev/null; then
    echo "[OK] mcp-remote is already installed"
else
    echo "Installing mcp-remote via npm..."
    npm install -g mcp-remote
    echo "[OK] mcp-remote installed"
fi

# Check if OpenClaw config exists
CONFIG_FILE="$HOME/.openclaw/openclaw.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "[ERROR] OpenClaw config not found at: $CONFIG_FILE"
    echo "   Please make sure OpenClaw is installed"
    exit 1
fi

echo "[OK] OpenClaw config found"
echo ""

# Backup existing config
cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
echo "Backed up config to: $CONFIG_FILE.backup"

# Add Danube MCP config using Python (to handle JSON properly)
# The config uses "sh -c" with $DANUBE_API_KEY so the key is read
# from the environment at runtime, not stored in the config file.
python3 << 'PYTHON_SCRIPT'
import json
import os
import sys

config_file = os.path.expanduser("~/.openclaw/openclaw.json")

# Read existing config
with open(config_file, 'r') as f:
    config = json.load(f)

# Danube MCP configuration
# Uses sh -c so $DANUBE_API_KEY is resolved from the environment at runtime.
# The API key is NOT stored in this config file - it stays in ~/.openclaw/.env
danube_config = {
    "name": "danube",
    "command": "sh",
    "args": [
        "-c",
        "mcp-remote https://mcp.danubeai.com/mcp --header \"danube-api-key:$DANUBE_API_KEY\""
    ]
}

# Navigate to external skills array
if "agents" not in config:
    config["agents"] = {"list": []}

if len(config["agents"]["list"]) == 0:
    config["agents"]["list"].append({"id": "main", "skills": {"external": []}})

agent = config["agents"]["list"][0]

if "skills" not in agent:
    agent["skills"] = {"external": []}

if "external" not in agent["skills"]:
    agent["skills"]["external"] = []

# Check if Danube is already configured
existing_danube = any(skill.get("name") == "danube" for skill in agent["skills"]["external"])

if existing_danube:
    print("[!] Danube MCP is already configured in OpenClaw")
    sys.exit(0)

# Add Danube config
agent["skills"]["external"].append(danube_config)

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("[OK] Danube MCP added to OpenClaw config")
print("   API key is read from DANUBE_API_KEY environment variable at runtime")
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "Restarting OpenClaw Gateway..."
    openclaw gateway restart
    echo ""
    echo "Setup complete!"
    echo ""
    echo "You can now use Danube tools through OpenClaw. Try:"
    echo "  - 'List available services on Danube'"
    echo "  - 'Search for tools that can send Slack messages'"
    echo "  - 'What's on my calendar today?'"
else
    echo ""
    echo "[ERROR] Setup failed. Restoring backup..."
    mv "$CONFIG_FILE.backup" "$CONFIG_FILE"
    exit 1
fi
