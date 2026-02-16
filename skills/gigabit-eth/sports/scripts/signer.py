#!/usr/bin/env python3
"""
signer.py — Helper for OpenClaw agents to sign and submit Solana transactions.

The Optionns API returns instructions array format. This module constructs, signs,
and submits transactions from those instructions.

Usage in agent code:
    from signer import sign_and_submit
    
    tx_sig = sign_and_submit(
        instructions=response['instructions'],
        keypair_path='~/.config/optionns/agent_keypair.json',
        rpc_url='https://api.devnet.solana.com'
    )
"""
import json
import base64
import time
from pathlib import Path
import urllib.request
import urllib.error


def sign_and_submit(
    instructions: list,
    keypair_path: str,
    rpc_url: str = "https://api.devnet.solana.com",
    timeout: int = 30
) -> str:
    """
    Construct, sign, and submit a Solana transaction from instructions array.
    
    Args:
        instructions: List of instruction dicts with programId, keys, data
        keypair_path: Path to Solana keypair JSON file
        rpc_url: Solana RPC endpoint
        timeout: Max seconds to wait for confirmation
        
    Returns:
        Transaction signature on success
        
    Raises:
        Exception: If construction, signing, or submission fails
    """
    try:
        from solders.keypair import Keypair
        from solders.transaction import Transaction
        from solders.message import Message
        from solders.instruction import Instruction, AccountMeta
        from solders.pubkey import Pubkey
        from solders.hash import Hash
    except ImportError:
        raise ImportError(
            "solders library required. Install with: pip install solders"
        )
    
    # Load keypair
    keypair_path = Path(keypair_path).expanduser()
    if not keypair_path.exists():
        raise FileNotFoundError(f"Keypair not found: {keypair_path}")
    
    with open(keypair_path, "r") as f:
        secret = json.load(f)
    
    kp = Keypair.from_bytes(bytes(secret))
    
    # Fetch fresh blockhash
    blockhash_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getLatestBlockhash",
        "params": [{"commitment": "confirmed"}]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        rpc_url,
        data=blockhash_payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            blockhash_result = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise Exception(f"Failed to fetch blockhash: {e}")
    
    if "error" in blockhash_result:
        raise Exception(f"Blockhash RPC error: {blockhash_result['error']}")
    
    blockhash_str = blockhash_result["result"]["value"]["blockhash"]
    blockhash = Hash.from_string(blockhash_str)
    
    # Construct instructions from API response
    solana_instructions = []
    for ix in instructions:
        program_id = Pubkey.from_string(ix["programId"])
        
        accounts = []
        for acc in ix["keys"]:
            accounts.append(AccountMeta(
                pubkey=Pubkey.from_string(acc["pubkey"]),
                is_signer=acc["isSigner"],
                is_writable=acc["isWritable"]
            ))
        
        data = base64.b64decode(ix["data"])
        
        solana_instructions.append(Instruction(
            program_id=program_id,
            accounts=accounts,
            data=data
        ))
    
    # Create message with payer = agent keypair
    msg = Message.new_with_blockhash(
        solana_instructions,
        kp.pubkey(),
        blockhash
    )
    
    # Sign and create transaction
    sig = kp.sign_message(bytes(msg))
    tx = Transaction.populate(msg, [sig])
    
    # Serialize signed tx
    tx_bytes = bytes(tx)
    tx_b64 = base64.b64encode(tx_bytes).decode("ascii")
    
    # Submit via JSON-RPC
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [
            tx_b64,
            {"encoding": "base64", "preflightCommitment": "confirmed"}
        ]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise Exception(f"RPC request failed: {e}")
    
    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")
    
    tx_sig = result.get("result", "")
    
    # Confirm the tx landed
    for _ in range(timeout // 2):
        time.sleep(2)
        confirm_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "getSignatureStatuses",
            "params": [[tx_sig], {"searchTransactionHistory": True}]
        }).encode("utf-8")
        
        confirm_req = urllib.request.Request(
            rpc_url,
            data=confirm_payload,
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(confirm_req, timeout=10) as resp:
                confirm_result = json.loads(resp.read().decode())
            
            statuses = confirm_result.get("result", {}).get("value", [None])
            if statuses and statuses[0] is not None:
                if statuses[0].get("err"):
                    raise Exception(f"Transaction failed on-chain: {statuses[0]['err']}")
                return tx_sig
        except Exception:
            continue
    
    raise Exception(f"Transaction submitted but not confirmed after {timeout}s: {tx_sig}")




if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Sign and submit Solana transactions')
    parser.add_argument('--stdin', action='store_true', required=True,
                        help='Read instructions JSON from stdin')
    parser.add_argument('--keypair', required=True, help='Path to keypair file')
    parser.add_argument('--rpc', default='https://api.devnet.solana.com', help='RPC URL')
    
    args = parser.parse_args()
    
    try:
        instructions_json = sys.stdin.read().strip()
        if not instructions_json:
            print("Error: No instructions provided via stdin", file=sys.stderr)
            sys.exit(1)
        
        # Normalize instructions
        instructions_raw = json.loads(instructions_json)
        instructions = []
        for ix in instructions_raw:
            normalized = {
                'programId': ix.get('programId') or ix.get('program_id'),
                'data': ix.get('data'),
                'keys': []
            }
            # Normalize accounts -> keys
            accounts = ix.get('accounts', ix.get('keys', []))
            for acc in accounts:
                normalized['keys'].append({
                    'pubkey': acc.get('pubkey'),
                    'isSigner': acc.get('is_signer') if acc.get('is_signer') is not None else acc.get('isSigner'),
                    'isWritable': acc.get('is_writable') if acc.get('is_writable') is not None else acc.get('isWritable')
                })
            instructions.append(normalized)
        
        tx_sig = sign_and_submit(
            instructions=instructions,
            keypair_path=args.keypair,
            rpc_url=args.rpc
        )
        print(tx_sig)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

