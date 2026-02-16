# OpenClaw Solana Connect v2.0

> The missing link between OpenClaw agents and Solana blockchain
> **Now using @solana/kit (Solana Web3.js v2)**

A purpose-built toolkit that enables autonomous AI agents running on OpenClaw to interact seamlessly with the Solana blockchain.

## 🛡️ Security First

### Private Key Protection

**IMPORTANT:** This toolkit **NEVER returns private keys** to the agent. Private keys are handled internally for signing only.

- `connectWallet()` returns only the address
- `generateWallet()` returns only the address  
- Transactions are signed internally without exposing the raw private key

This prevents prompt injection attacks where a compromised agent could exfiltrate private keys.

### Always Use Testnet First

```bash
# Set testnet RPC for development (RECOMMENDED)
export SOLANA_RPC_URL=https://api.testnet.solana.com

# Only switch to mainnet after thorough testing
export SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### Best Practices

1. **Use a Dedicated Wallet** — Never use your main wallet. Create a separate wallet with limited funds for agent trading.

2. **Set Spending Limits** — Configure maximum transaction amounts:
   ```bash
   export MAX_SOL_PER_TX=10      # Max 10 SOL per transaction
   export MAX_TOKENS_PER_TX=1000 # Max 1000 tokens per transaction
   ```

3. **Enable Dry Run Mode** — Test transactions before sending:
   ```javascript
   const result = await sendSol(wallet, toAddress, amount, { dryRun: true });
   ```

4. **Store Private Keys Securely** — Use environment variables, never hardcode:
   ```javascript
   // ✅ Good
   const wallet = await connectWallet(process.env.AGENT_PRIVATE_KEY);
   
   // ❌ Bad - never do this
   const wallet = await connectWallet('your-private-key-here');
   ```

5. **Monitor Activity** — Regularly review transaction history and wallet balances.

---

## Features

- 🧠 **AI-First Design** — Built for autonomous agents
- 🔄 **OpenClaw Native** — Works out of the box with OpenClaw skills
- 🤖 **Agent-Friendly** — Natural language inputs, automatic validation
- 🛡️ **Secure by Default** — Sandboxed transactions, amount limits, dry-run mode

### Wallet Operations
- Generate new wallets
- Connect existing wallets
- Check balances (SOL, tokens, NFTs)
- Transaction history

### Transaction Operations
- Send SOL
- Send SPL tokens
- Dry-run mode (simulate before send)

### Token Operations
- Get token balances
- Get NFT holdings
- Token metadata

---

## Installation

```bash
# Install via ClawHub
clawhub install solana-connect

# Or clone manually
git clone https://github.com/Seenfinity/openclaw-solana-connect.git
cd solana-connect
npm install
```

---

## Quick Start

```javascript
const { connectWallet, getBalance, sendSol } = require('./scripts/solana.js');

// Connect with a private key
const wallet = await connectWallet(process.env.AGENT_PRIVATE_KEY);

// Check balance
const balance = await getBalance(wallet.address);

// Send SOL (with dry-run first!)
const result = await sendSol(wallet.privateKey, toAddress, 1.0, { dryRun: true });
console.log('Simulation:', result);

// If OK, send for real
const tx = await sendSol(wallet.privateKey, toAddress, 1.0);
console.log('Transaction:', tx.signature);
```

---

## Configuration

```bash
# Required: RPC endpoint
export SOLANA_RPC_URL=https://api.testnet.solana.com

# Optional: Security limits
export MAX_SOL_PER_TX=10
export MAX_TOKENS_PER_TX=1000
```

---

## Testing

```bash
npm install
node test.js
```

All tests pass:
- ✅ Generate wallet
- ✅ Connect to Solana RPC
- ✅ Get balance
- ✅ Get token accounts
- ✅ Get transactions

---

## Documentation

See [SKILL.md](./SKILL.md) for full documentation.

---

## GitHub

[github.com/Seenfinity/openclaw-solana-connect](https://github.com/Seenfinity/openclaw-solana-connect)

---

## License

MIT © 2026 Seenfinity

---

*Built for OpenClaw agents. Powered by Solana.*
