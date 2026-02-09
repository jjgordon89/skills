---
name: eyebot-walletbot
description: Wallet operations and portfolio management
version: 1.0.0
author: ILL4NE
metadata:
  api_endpoint: http://93.186.255.184:8001
  pricing:
    per_use: $1
    lifetime: $25
  chains: [base, ethereum, polygon, arbitrum]
---

# Eyebot WalletBot 👛

Wallet operations specialist. Manage portfolios, track balances, send transactions, and organize your crypto holdings efficiently.

## API Endpoint
`http://93.186.255.184:8001`

## Usage
```bash
# Request payment
curl -X POST "http://93.186.255.184:8001/a2a/request-payment?agent_id=walletbot&caller_wallet=YOUR_WALLET"

# After payment, verify and execute
curl -X POST "http://93.186.255.184:8001/a2a/verify-payment?request_id=...&tx_hash=..."
```

## Pricing
- Per-use: $1
- Lifetime (unlimited): $25
- All 15 agents bundle: $200

## Capabilities
- Multi-chain balance tracking
- Transaction history analysis
- Token approval management
- Batch transfers
- Portfolio analytics
- P&L tracking
- Address book management
- Gas optimization
- Export for tax reporting
