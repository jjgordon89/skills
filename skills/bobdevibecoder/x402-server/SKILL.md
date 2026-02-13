---
name: x402-server
description: Monetized API server using x402 payment protocol. Charges USDC on Base for AI agent services.
metadata:
  clawdbot:
    emoji: "💰"
    requires:
      bins: ["node"]
---

# x402 Monetized API Server

Build a paid API that charges other AI agents USDC per request using the x402 payment protocol on Base.

## Features

- 4 paid endpoints (crypto research, market scan, content gen, agent status)
- x402 payment gating (HTTP 402 responses with payment requirements)
- Gasless USDC payments on Base
- Compatible with Coinbase Agentic Wallet

## Setup

1. Install: npm install express x402-express
2. Set PAY_TO address to your wallet
3. Run: node index.js

## Endpoints

| Endpoint | Price | Description |
|----------|-------|-------------|
| GET /api/crypto-research | \/usr/bin/bash.05 | Token research and analysis |
| GET /api/market-scan | \/usr/bin/bash.02 | Trending tokens scanner |
| POST /api/content-generate | \/usr/bin/bash.10 | AI content generation |
| GET /api/agent-status | \/usr/bin/bash.01 | Agent status and capabilities |
| GET /health | Free | Health check |
| GET /api/services | Free | Service directory |
