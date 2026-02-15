# Optionns API Reference

Base URL: `https://api.optionns.com`

Authentication: `X-API-Key` header
```
X-API-Key: YOUR_API_KEY
```

---

## Endpoints

### 1. Faucet (Devnet Only)

Fund your devnet wallet with cmUSDC.

```http
POST /api/faucet
Content-Type: application/json

{
  "wallet_address": "YourSolanaWallet...",
  "amount": 1000.0
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "5xK9...",
  "amount": 1000.0,
  "message": "Faucet request processed"
}
```

---

### 2. List Live Games

Get all currently live games with available betting markets.

```http
GET /v1/sports/events?sport=NBA
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**
- `sport` (string): NBA, NFL, MLB, etc (primary filter)

**Response:**
```json
{
  "success": true,
  "data": {
    "live": [
      {
        "id": "401584123",
        "title": "Lakers vs Celtics",
        "sport": "basketball",
        "league": "NBA",
        "status": "live",
        "score": "45-42",
        "period": 2,
        "clock": "8:34",
        "outcomes": [
          {
            "token_id": "0x1234abcd",
            "label": "Lakers +10",
            "outcome_type": "lead_margin_home"
          }
        ]
      }
    ],
    "upcoming": [],
    "total": 1
  },
  "error": null
}
```

---

### 3. Get Quote

Get pricing for a potential trade.

```http
POST /v1/vault/quote
X-API-Key: YOUR_API_KEY
Content-Type: application/json

{
  "token_id": "0x1234abcd",
  "underlying_price": 0.50,
  "strike": 0.65,
  "option_type": "call",
  "sport": "nba",
  "quantity": 5,
  "expiry_minutes": 5
}
```

**Response:**
```json
{
  "success": true,
  "premium": 2.50,
  "max_payout": 10.00,
  "quote_id": "q_abc123",
  "valid_until": "2026-02-05T18:45:00Z",
  "implied_odds": 4.0,
  "break_even": 0.25
}
```

---

### 4. Execute Trade

Place a bet with automatic barrier registration.

```http
POST /v1/vault/buy
X-API-Key: YOUR_API_KEY
Content-Type: application/json

{
  "quote_id": "q_abc123",
  "token_id": "0x1234abcd",
  "game_id": "401584123",
  "game_title": "Lakers vs Celtics",
  "sport": "nba",
  "underlying_price": 0.50,
  "strike": 0.65,
  "option_type": "call",
  "quantity": 5,
  "expiry_minutes": 5,
  "barrier_type": "lead_margin_home",
  "barrier_target": 10.0,
  "barrier_direction": "above",
  "user_pubkey": "HN7c...",
  "user_ata": "9uW2..."
}
```

**Barrier Types:**
- `lead_margin_home`: Home team leads by X points
- `lead_margin_away`: Away team leads by X points
- `total_points`: Combined score reaches X
- `home_score`: Home team reaches X points
- `away_score`: Away team reaches X points

**Response:**
```json
{
  "success": true,
  "position_id": "pos_xyz789",
  "premium_paid": 2.50,
  "max_payout": 10.00,
  "expires_at": "2026-02-05T18:50:00Z",
  "barrier_registered": true,
  "barrier_level": 10.0,
  "barrier_type": "lead_margin_home",
  "outcome_id": "a1b2c3d4...",
  "unsigned_tx": "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAQAHEAv...",
  "blockhash": "FwRYtTPRk5N4wUeNj9pw6YQ4tNyVQfJkVfGVr2nczLFC",
  "position_pda": "8xQ7K...",
  "event_pool_pda": "9yR8L...",
  "status": "active"
}
```

> **Note:** The API returns an **unsigned transaction** that you must sign with your own keypair and submit to Solana. This ensures the API never holds agent private keys. Use the provided `signer.py` helper to sign and submit the transaction.

---

### 5. List Positions

Get your open and closed positions.

```http
GET /v1/vault/positions
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**
- `status` (string): open, closed, all
- `game_id` (string): Filter by specific game

**Response:**
```json
{
  "success": true,
  "positions": [
    {
      "position_id": "pos_xyz789",
      "token_id": "token_401584123",
      "game_id": "401584123",
      "game_title": "Lakers vs Celtics",
      "sport": "nba",
      "option_type": "call",
      "strike": 0.65,
      "quantity": 5.0,
      "premium_collected": 2.50,
      "entry_underlying_price": 0.50,
      "entry_delta": 0.85,
      "entry_gamma": 0.24,
      "max_payout": 10.00,
      "barrier_level": 10.0,
      "barrier_type": "lead_margin_home",
      "expiry_time": "2026-02-05T18:50:00Z",
      "status": "open",
      "created_at": "2026-02-05T18:45:00Z",
      "settled_at": null,
      "settlement_price": null,
      "payout": null,
      "vault_source": "nba"
    }
  ]
}
```

---

### 6. WebSocket Feed

Real-time updates on game events and barrier touches.

```javascript
// Connect
const ws = new WebSocket('wss://api.optionns.com/ws?api_key=YOUR_KEY');

// Subscribe to games
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    gameIds: ['401584123', '401584124']
  }));
};

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'barrier_touched':
      console.log('Barrier hit!', data);
      break;
    case 'game_update':
      console.log('Score update', data);
      break;
    case 'trade_filled':
      console.log('Trade confirmed', data);
      break;
  }
};
```

**Message Types:**

**barrier_touched:**
```json
{
  "type": "barrier_touched",
  "game_id": "401584123",
  "position_id": "pos_xyz789",
  "outcome_id": "a1b2c3d4...",
  "result": "WIN",
  "payout": 10.00,
  "tx_hash": "5xK9...",
  "message": "🔥 Lakers hit +10! You won $10.00"
}
```

**game_update:**
```json
{
  "type": "game_update",
  "game_id": "401584123",
  "home_score": 55,
  "away_score": 48,
  "quarter": 2,
  "time_remaining": "6:42",
  "event": "3-pointer by LeBron James"
}
```

---

## Error Codes

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `INVALID_API_KEY` | 401 | Authentication failed | Check your API key |
| `INSUFFICIENT_FUNDS` | 400 | Wallet balance too low | Fund wallet via faucet |
| `INSUFFICIENT_LIQUIDITY` | 400 | Pool can't cover payout | Try smaller amount |
| `MARKET_CLOSED` | 400 | Game has ended | Find another game |
| `INVALID_QUOTE` | 400 | Quote expired or invalid | Get new quote |
| `RATE_LIMITED` | 429 | Too many requests | Wait 60 seconds |
| `BARRIER_NOT_FOUND` | 404 | Invalid barrier type | Check barrier_type value |

---

## Rate Limits

- Quote requests: 60/minute
- Trade execution: 30/minute
- Game listings: 120/minute
- WebSocket: 1 connection per API key

---

## Network Details

**Network:** Solana Devnet
**Program ID:** `7kHCtJrAuHAg8aQPtkf2ijjWyEEZ2fUYWaCT7sXVwMSn`
**Token:** cmUSDC (devnet USDC)

**Explorer URLs:**
- Devnet: https://explorer.solana.com/?cluster=devnet
- Transaction: https://explorer.solana.com/tx/{tx_hash}?cluster=devnet

---

## SDK Examples

### Python
```python
import requests

API_KEY = 'your_key'
BASE_URL = 'https://api.optionns.com'

headers = {'X-API-Key': API_KEY}

# Get games
r = requests.get(f'{BASE_URL}/v1/sports/events?sport=NBA', headers=headers)
games = r.json()['data']['live']

# Place trade
quote = requests.post(f'{BASE_URL}/v1/vault/quote', 
    headers=headers,
    json={'token_id': 'abc', 'quantity': 5}
).json()

trade = requests.post(f'{BASE_URL}/v1/vault/buy',
    headers=headers,
    json={'quote_id': quote['quote_id'], ...}
).json()
```

### JavaScript
```javascript
// Using fetch
const response = await fetch('https://api.optionns.com/v1/vault/buy', {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    token_id: 'abc',
    quantity: 5,
    ...
  })
});

const result = await response.json();
```

---

**Built for the USDC Hackathon - Agentic Commerce Track**