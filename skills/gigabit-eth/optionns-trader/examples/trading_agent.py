"""
Complete example of how to use the Optionns Trader skill in your agent.

This shows the full flow from registration to executing trades with on-chain settlement.

⚠️ DEVNET ONLY: This skill operates on Solana Devnet with mock USDC.
   NEVER use mainnet wallets or real funds with this code.

On-chain signing:
   This example calls scripts/signer.py as a CLI subprocess for transaction
   signing. See scripts/signer.py for the full signing implementation.
"""
import json
import subprocess
import requests
from pathlib import Path


class OptionnsTradingAgent:
    """Example agent that trades sports options via Optionns API.
    
    ⚠️ SECURITY WARNING:
    - Only use with throwaway/devnet keypairs
    - Verify API endpoint independently before trusting
    - Never point at mainnet wallet or use real funds
    """
    
    def __init__(self, api_key: str, keypair_path: str, rpc_url: str = "https://api.devnet.solana.com"):
        self.api_key = api_key
        self.keypair_path = Path(keypair_path).expanduser()
        self.api_base = "https://api.optionns.com"
        self.rpc_url = rpc_url
        self.signer_script = Path(__file__).parent.parent / 'scripts' / 'signer.py'
        
        # Verify devnet usage
        if "devnet" not in rpc_url.lower():
            raise ValueError("⚠️ DEVNET ONLY: This example only works with Solana Devnet RPC")
    
    def _api_call(self, method: str, endpoint: str, data: dict = None):
        """Make authenticated API call."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_base}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def _sign_and_submit(self, instructions: list) -> str:
        """Sign and submit a transaction by calling signer.py as a subprocess.
        
        This avoids sys.path manipulation by using the CLI interface of signer.py.
        """
        result = subprocess.run(
            [
                "python3",
                str(self.signer_script),
                str(self.keypair_path),
                json.dumps(instructions),
                self.rpc_url
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Signing failed: {result.stderr.strip()}")
        
        return result.stdout.strip()
    
    def get_live_games(self, sport: str = "NBA"):
        """Fetch live games."""
        return self._api_call("GET", f"/v1/sports/events?sport={sport}")
    
    def get_quote(self, token_id: str, underlying: float, strike: float, 
                  quantity: int = 5, expiry_minutes: int = 5):
        """Get option quote."""
        return self._api_call("POST", "/v1/vault/quote", {
            "token_id": token_id,
            "underlying_price": underlying,
            "strike": strike,
            "option_type": "call",
            "sport": "nba",
            "quantity": quantity,
            "expiry_minutes": expiry_minutes
        })
    
    def execute_trade(self, quote_id: str, game_id: str, game_title: str,
                      token_id: str, underlying: float, strike: float,
                      quantity: int, wallet: str, user_ata: str = None):
        """
        Execute a trade and settle on-chain using the instructions format.
        
        Args:
            quote_id: Quote ID from get_quote()
            game_id: Game ID
            game_title: Human-readable game title
            token_id: Token identifier
            underlying: Underlying price (0-1)
            strike: Strike price (0-1)
            quantity: Number of contracts
            wallet: Your Solana wallet public key
            user_ata: Your USDC ATA (optional, can be auto-derived)
        
        Returns:
            dict with tx_signature, position_id, and other trade details
        """
        # Step 1: Call buy endpoint (returns Solana instructions)
        buy_response = self._api_call("POST", "/v1/vault/buy", {
            "quote_id": quote_id,
            "token_id": token_id,
            "game_id": game_id,
            "game_title": game_title,
            "sport": "nba",
            "underlying_price": underlying,
            "strike": strike,
            "option_type": "call",
            "quantity": quantity,
            "expiry_minutes": 5,
            "barrier_type": "lead_margin_home",
            "barrier_target": 10,
            "barrier_direction": "above",
            "user_pubkey": wallet,
            "user_ata": user_ata or wallet  # Can auto-derive if omitted
        })
        
        # Check if we got instructions back
        if "instructions" not in buy_response:
            raise ValueError(f"API error: {buy_response.get('error', 'No instructions returned')}")
        
        # Step 2: Sign and submit via signer.py CLI (no path manipulation needed)
        tx_signature = self._sign_and_submit(buy_response['instructions'])
        
        return {
            "tx_signature": tx_signature,
            "position_id": buy_response.get('position_id'),
            "outcome_position_pda": buy_response.get('outcome_position_pda'),
            "barrier_registered": buy_response.get('barrier_registered', False),
            "explorer_url": f"https://explorer.solana.com/tx/{tx_signature}?cluster=devnet"
        }
    
    def get_positions(self):
        """Fetch your active positions."""
        return self._api_call("GET", "/v1/vault/positions")


def main():
    """Example usage.
    
    ⚠️ BEFORE RUNNING:
    1. Create a DEVNET-ONLY keypair: solana-keygen new -o ~/.config/optionns/devnet_test.json
    2. Fund it with devnet SOL: solana airdrop 2 <YOUR_DEVNET_WALLET>
    3. Register for API key: ./scripts/optionns.sh register your_agent_name
    4. Replace YOUR_API_KEY and YOUR_SOLANA_WALLET below
    """
    # Initialize agent
    agent = OptionnsTradingAgent(
        api_key="YOUR_API_KEY",  # From ~/.config/optionns/credentials.json
        keypair_path="~/.config/optionns/agent_keypair.json",  # DEVNET keypair only!
        rpc_url="https://api.devnet.solana.com"  # MUST be devnet
    )
    
    # 1. Find live games
    games = agent.get_live_games("NBA")
    print(f"Found {len(games.get('data', {}).get('live', []))} live games")
    
    if not games.get('data', {}).get('live'):
        print("No live games available. Try again during NBA game hours.")
        return
    
    # 2. Get a quote
    quote = agent.get_quote(
        token_id="token_401584123",
        underlying=0.55,
        strike=0.50,
        quantity=5
    )
    print(f"Quote: {quote.get('total_premium', quote.get('premium', 0))} USDC premium")
    
    # 3. Execute trade (DEVNET ONLY!)
    result = agent.execute_trade(
        quote_id=quote['quote_id'],
        game_id="401584123",
        game_title="Lakers vs Celtics",
        token_id="token_401584123",
        underlying=0.55,
        strike=0.50,
        quantity=5,
        wallet="YOUR_SOLANA_WALLET"  # Your DEVNET wallet address
    )
    
    print(f"✅ Trade executed!")
    print(f"Position ID: {result['position_id']}")
    print(f"Tx Signature: {result['tx_signature']}")
    print(f"Barrier Registered: {result['barrier_registered']}")
    print(f"Explorer: {result['explorer_url']}")
    
    # 4. Check positions
    positions = agent.get_positions()
    print(f"Active positions: {len(positions.get('positions', []))}")


if __name__ == "__main__":
    print("⚠️  DEVNET ONLY - Do NOT use mainnet wallets or real funds!")
    print()
    main()
