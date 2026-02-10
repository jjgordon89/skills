# Bittensor SDK API Reference

Complete API documentation for the Bittensor SDK skill. This file contains detailed method signatures, extended examples, and comprehensive reference material.

## Table of Contents

- [Subtensor Class](#subtensor-class)
- [Wallet Class](#wallet-class)
- [Balance Class](#balance-class)
- [Complete API Methods Summary](#complete-api-methods-summary)
- [Extended Examples](#extended-examples)
- [Quick Reference Card](#quick-reference-card)

---

## Subtensor Class

### Initialization

```python
subtensor = bt.Subtensor(
    network: Optional[str] = None,
    config: Optional[Config] = None,
    log_verbose: bool = False,
    fallback_endpoints: Optional[list[str]] = None,
    retry_forever: bool = False,
    archive_endpoints: Optional[list[str]] = None,
    mock: bool = False
)
```

### Core Methods

| Method | Description |
|--------|-------------|
| `get_all_subnets_netuid()` | Get all subnet netuids |
| `get_subnet_info(netuid)` | Get detailed subnet info |
| `get_balance(address)` | Get TAO balance |
| `add_stake(...)` | Stake TAO to hotkey |
| `unstake(...)` | Unstake TAO from hotkey |
| `register(...)` | Register neuron |
| `metagraph(netuid)` | Get subnet metagraph |
| `set_weights(...)` | Set validator weights |
| `get_delegates()` | Get all delegates |
| `delegate(...)` | Delegate to validator |
| `undelegate(...)` | Remove delegation |

### Hyperparameter Methods

| Method | Description |
|--------|-------------|
| `get_subnet_hyperparameters(netuid)` | Get subnet params |
| `difficulty(netuid)` | Get POW difficulty |
| `get_max_uids(netuid)` | Get max neurons |
| `commit_reveal_enabled(netuid)` | Check commit-reveal |

### Emission Methods

| Method | Description |
|--------|-------------|
| `get_total_issuance()` | Total TAO supply |
| `get_emission_value_by_netuid(netuid)` | Subnet emission |
| `get_all_ema_tao_inflow()` | EMA flow per subnet |
| `get_block_emission_value()` | Emission per block |

### Advanced Methods

| Method | Description |
|--------|-------------|
| `add_proxy(...)` | Add proxy relationship |
| `create_pure_proxy(...)` | Create pure proxy |
| `create_crowdloan(...)` | Create crowdloan |
| `contribute_crawdloan(...)` | Contribute to crowdloan |
| `commit_weights(...)` | Commit weight hash |
| `reveal_weights(...)` | Reveal weights |
| `add_liquidity(...)` | Add to liquidity pool |
| `claim_root(...)` | Claim root dividends |

---

## Wallet Class

```python
wallet = bt.Wallet(
    name: Optional[str] = None,
    path: Optional[str] = None,
    hotkey: Optional[str] = None,
    coldkey: Optional[str] = None
)
```

### Properties

| Property | Description |
|----------|-------------|
| `wallet.coldkey` | Coldkey keypair |
| `wallet.hotkey` | Hotkey keypair |
| `wallet.coldkey_balance` | Coldkey TAO balance |
| `wallet.coldkeypub` | Public coldkey address |

---

## Balance Class

```python
balance = bt.Balance.from_tao(amount: float)
balance = bt.Balance.from_rao(amount: int)
```

### Properties

| Property | Description |
|----------|-------------|
| `balance.rao` | Amount in Rao |
| `balance.tao` | Amount in TAO |
| `balance.theta` | Amount in Theta |

---

## Complete API Methods Summary

### Subtensor Methods Summary

| Category | Methods |
|----------|---------|
| **Subnet Info** | `get_all_subnets_netuid`, `get_all_subnets_info`, `get_subnet_info`, `get_subnet_dynamic_info`, `get_subnet_hyperparameters`, `get_subnet_burn_cost`, `get_admin_freeze_window` |
| **Balance** | `get_balance`, `get_balances`, `get_existential_deposit` |
| **Staking** | `add_stake`, `add_stake_multiple`, `unstake`, `unstake_multiple`, `get_stake`, `get_stake_for_hotkey`, `get_stake_for_coldkey_and_hotkey`, `get_stake_info_for_coldkey`, `get_stake_info_for_coldkeys`, `get_minimum_required_stake`, `get_auto_stakes`, `get_stake_add_fee`, `get_stake_movement_fee`, `get_stake_weight` |
| **Registration** | `register`, `burned_register`, `get_difficulty` |
| **Neuron Info** | `get_neuron_for_pubkey`, `get_neuron_for_pubkey_and_subnet`, `get_all_neuron_certificates`, `get_neuron_certificate`, `get_netuids_for_hotkey`, `get_owned_hotkeys`, `does_hotkey_exist`, `get_hotkey_owner`, `metagraph`, `get_metagraph_info` |
| **Weights** | `set_weights`, `commit_weights`, `reveal_weights`, `get_all_commitments`, `get_all_revealed_commitments`, `get_commitment`, `get_commitment_metadata`, `get_revealed_commitment`, `get_revealed_commitment_by_hotkey`, `commit_reveal_enabled` |
| **Emissions** | `get_total_issuance`, `get_emission_value_by_netuid`, `get_all_ema_tao_inflow`, `get_ema_tao_inflow`, `get_block_emission_value` |
| **Delegates** | `get_delegates`, `get_delegate_by_hotkey`, `get_delegated`, `get_delegate_identities`, `get_delegate_take`, `delegate`, `undelegate` |
| **Root Network** | `get_root_network_info`, `claim_root`, `get_root_claim_type`, `get_root_claimable_rate`, `get_root_claimable_stake`, `get_root_claimed`, `get_root_alpha_dividends_per_subnet`, `get_root_claimable_all_rates` |
| **Crowdloans** | `create_crowdloan`, `contribute_crowdloan`, `finalize_crowdloan`, `get_crowdloan_by_id`, `get_crowdloans`, `get_crowdloan_contributions`, `get_crowdloan_next_id`, `get_crowdloan_constants`, `dissolve_crowdloan`, `refund_crowdloan` |
| **Liquidity** | `add_liquidity`, `remove_liquidity`, `get_liquidity_list` |
| **Proxies** | `add_proxy`, `create_pure_proxy`, `get_proxies`, `get_proxies_for_real_account`, `get_proxy_announcements`, `get_proxy_announcement`, `get_proxy_constants`, `announce_proxy`, `proxy_announced`, `reject_proxy_announcement`, `remove_proxy`, `remove_pure_proxy` |
| **MEV Protection** | `get_mev_shield_current_key`, `get_mev_shield_next_key`, `get_mev_shield_submissions`, `get_mev_shield_submission` |
| **Bonds** | `bonds`, `get_last_bonds_reset`, `get_last_commitment_bonds_reset_block` |
| **Child Keys** | `get_children`, `get_children_pending`, `get_parents` |
| **Epoch/Tempo** | `get_next_epoch_start_block`, `blocks_until_next_epoch`, `blocks_since_last_update` |
| **Block Operations** | `get_current_block`, `get_block_info`, `get_block_hash`, `determine_block_hash`, `get_extrinsic_fee` |
| **Transfers** | `transfer`, `get_transferred_events` |
| **Advanced** | `compose_call`, `filter_netuids_by_registered_hotkeys` |
| **Mechanisms** | `get_mechanism_count`, `get_mechanism_emission_split` |
| **Connection** | `close`, `block` property |

---

## Extended Examples

### Example 5: Complete Stake Management

```python
import bittensor as bt
from bittensor import Balance

# Initialize
subtensor = bt.Subtensor(network="finney")
wallet = bt.Wallet()

# Get all stake info for wallet
stake_infos = subtensor.get_stake_info_for_coldkey(
    coldkey_ss58=wallet.coldkey.ss58_address
)

# Display stake summary
print("=== Stake Portfolio ===")
total_stake = Balance(0)
for info in stake_infos:
    print(f"Subnet {info.netuid}:")
    print(f"  Hotkey: {info.hotkey[:10]}...")
    print(f"  Stake: {info.stake.tao} TAO")
    print(f"  Rate: {info.stake_ratio}")
    total_stake += info.stake

print(f"\nTotal Stake: {total_stake.tao} TAO")

# Get minimum required stake
min_stake = subtensor.get_minimum_required_stake()
print(f"Minimum Required Stake: {min_stake.tao} TAO")

# Check if any stake needs consolidation
for info in stake_infos:
    if info.stake < min_stake:
        print(f"\nWarning: Stake on subnet {info.netuid} below minimum!")
```

### Example 6: Validator Performance Monitor

```python
import bittensor as bt
import numpy as np

# Initialize
subtensor = bt.Subtensor(network="finney")

# Get subnet info
subnet_info = subtensor.get_subnet_info(netuid=1)
print(f"=== Subnet 1 Performance ===")
print(f"Tempo: {subnet_info.tempo}")
print(f"Emission: {subnet_info.emission}")
print(f"Immunity Period: {subnet_info.immunity_period}")

# Get metagraph
metagraph = subtensor.metagraph(netuid=1)

# Analyze validator performance
print(f"\n=== Validator Analysis ===")
for i in range(min(10, int(metagraph.n))):  # Top 10 neurons
    if metagraph.validator_permit[i]:
        print(f"UID {metagraph.uids[i]}:")
        print(f"  Stake: {metagraph.S[i].tao:.2f} TAO")
        print(f"  Trust: {metagraph.T[i]:.4f}")
        print(f"  Consensus: {metagraph.C[i]:.4f}")
        print(f"  Incentive: {metagraph.I[i]:.4f}")
        print(f"  Dividends: {metagraph.D[i]:.4f}")
        print(f"  Emission: {metagraph.E[i]:.6f} TAO/block")
```

### Example 7: Root Network Participation

```python
import bittensor as bt
from bittensor import Balance

# Initialize
subtensor = bt.Subtensor(network="finney")
wallet = bt.Wallet(name="root_validator")

# Check root network status
root_info = subtensor.get_root_network_info()
print(f"=== Root Network ===")
print(f"Emission: {root_info.emission}")
print(f"Max UIDs: {root_info.max_allowed_uids}")

# Get root validators
root_metagraph = subtensor.metagraph(netuid=0)
print(f"\nRoot Validators: {int(root_metagraph.n)}")

# Check claimable root dividends
claimable_rates = subtensor.get_root_claimable_all_rates(
    hotkey_ss58=wallet.hotkey.ss58_address
)

print(f"\n=== Claimable Root Dividends ===")
total_claimable = Balance(0)
for netuid, rate in sorted(claimable_rates.items()):
    stake = subtensor.get_root_claimable_stake(
        coldkey_ss58=wallet.coldkey.ss58_address,
        hotkey_ss58=wallet.hotkey.ss58_address,
        netuid=netuid
    )
    if stake.tao > 0:
        print(f"Subnet {netuid}: {stake.tao:.4f} TAO claimable (rate: {rate:.6f})")
        total_claimable += stake

print(f"\nTotal Claimable: {total_claimable.tao:.4f} TAO")

# Claim root dividends if significant
if total_claimable.tao > 0.001:
    result = subtensor.claim_root(
        wallet=wallet,
        netuids=list(claimable_rates.keys())
    )
    print(f"Claim result: {result.success}")
```

### Example 8: MEV Protection Setup

```python
import bittensor as bt
from bittensor import Balance

# Initialize with MEV protection
subtensor = bt.Subtensor(network="finney")
wallet = bt.Wallet()

# Check current MEV keys
current_key = subtensor.get_mev_shield_current_key()
next_key = subtensor.get_mev_shield_next_key()

print(f"=== MEV Shield Status ===")
print(f"Current Key: {current_key[:20]}..." if current_key else "Current Key: None")
print(f"Next Key: {next_key[:20]}..." if next_key else "Next Key: None")

# Get pending submissions
submissions = subtensor.get_mev_shield_submissions()
print(f"\nPending Submissions: {len(submissions)}")

# Example: Protected stake operation
amount = Balance.from_tao(100.0)
result = subtensor.add_stake(
    wallet=wallet,
    netuid=1,
    hotkey_ss58=wallet.hotkey.ss58_address,
    amount=amount,
    mev_protection=True,  # Enable MEV protection
    wait_for_revealed_execution=True,
    wait_for_finalization=True
)

print(f"\nProtected Stake Result:")
print(f"  Success: {result.success}")
if hasattr(result, 'mev_encrypted'):
    print(f"  MEV Encrypted: {result.mev_encrypted}")
```

### Example 9: Child Keys Management

```python
import bittensor as bt

# Initialize
subtensor = bt.Subtensor(network="finney")
validator_wallet = bt.Wallet(name="validator")

# Get validator's children
success, children, error = subtensor.get_children(
    hotkey_ss58=validator_wallet.hotkey.ss58_address,
    netuid=1
)

print(f"=== Validator Children ===")
if success:
    for proportion, child_hotkey in children:
        print(f"Child: {child_hotkey[:10]}..., Proportion: {proportion:.4f}")
else:
    print(f"Error: {error}")

# Get pending children
pending_children, cooldown = subtensor.get_children_pending(
    hotkey_ss58=validator_wallet.hotkey.ss58_address,
    netuid=1
)

print(f"\n=== Pending Children ===")
for child_hotkey, proportion in pending_children:
    print(f"Pending: {child_hotkey[:10]}..., Proportion: {proportion:.4f}")
print(f"Cool-down until block: {cooldown}")

# Get parents of a specific child
parents = subtensor.get_parents(
    hotkey_ss58="5Hx...",  # Child hotkey
    netuid=1
)

print(f"\n=== Parent Relationships ===")
for proportion, parent_hotkey in parents:
    print(f"Parent: {parent_hotkey[:10]}..., Proportion: {proportion:.4f}")
```

### Example 10: Batch Operations

```python
import bittensor as bt
from bittensor import Balance
import time

# Initialize
subtensor = bt.Subtensor(network="finney")
wallet = bt.Wallet()

# Batch get balances for multiple addresses
addresses = [
    "5HxwJ7N8gZ4eCZ6e4",
    "5GrwvaEF5zXb26Fz",
    "5FHneW46xGXgs5m",
    "5F4tQy4yC5JvY3f",
    "5Dv2K2YkN3kCZ7p"
]

print("=== Batch Balance Query ===")
balances = subtensor.get_balances(*addresses)
for addr, balance in balances.items():
    print(f"{addr[:10]}...: {balance.tao:.4f} TAO")

# Batch get stake info
print("\n=== Batch Stake Info ===")
stake_dict = subtensor.get_stake_info_for_coldkeys(
    coldkey_ss58s=addresses[:3]
)
for addr, stake_infos in stake_dict.items():
    print(f"\n{addr[:10]}:")
    for info in stake_infos:
        print(f"  Subnet {info.netuid}: {info.stake.tao:.4f} TAO")

# Rate-limited operations
print("\n=== Rate-Limited Operations ===")
hotkeys = ["5Hx...", "5Grw...", "5FHn...", "5F4t..."]
for i, hotkey in enumerate(hotkeys):
    try:
        owner = subtensor.get_hotkey_owner(hotkey_ss58=hotkey)
        print(f"Hotkey {i+1}: {owner[:10]}...")
    except Exception as e:
        print(f"Hotkey {i+1}: Error - {e}")
    
    # Rate limit: don't spam the network
    if i < len(hotkeys) - 1:
        time.sleep(0.5)  # 500ms delay between requests
```

---

## Quick Reference Card

### Most Common Operations

```python
# Connect to network
subtensor = bt.Subtensor(network="finney")

# Load wallet
wallet = bt.Wallet()

# Check balance
balance = subtensor.get_balance(wallet.coldkey.ss58_address)

# Get all subnets
netuids = subtensor.get_all_subnets_netuid()

# Get subnet info
subnet_info = subtensor.get_subnet_info(netuid=1)

# Get metagraph
metagraph = subtensor.metagraph(netuid=1)

# Register neuron
subtensor.register(wallet=wallet, netuid=1)

# Stake TAO
subtensor.add_stake(wallet=wallet, netuid=1, hotkey_ss58="...", amount=Balance.from_tao(10))

# Unstake TAO
subtensor.unstake(wallet=wallet, netuid=1, hotkey_ss58="...", amount=Balance.from_tao(5))

# Set weights
subtensor.set_weights(wallet=wallet, netuid=1, uids=np.array([0,1,2]), weights=np.array([0.3, 0.4, 0.3]))

# Get delegates
delegates = subtensor.get_delegates()

# Delegate stake
subtensor.delegate(wallet=wallet, delegate_ss58="...", amount=Balance.from_tao(100))

# Close connection
subtensor.close()
```

### Key Metrics to Monitor

- **Total Issuance**: `get_total_issuance()`
- **Subnet Emissions**: `get_emission_value_by_netuid(netuid)`
- **EMA Flow**: `get_all_ema_tao_inflow()`
- **Registration Cost**: `get_subnet_info(netuid).burn_cost`
- **Total Stake**: `metagraph(netuid).S.sum()`
- **Neuron Count**: `metagraph(netuid).n`
- **Validator Count**: `sum(metagraph.validator_permit)`
- **Root Emissions**: `get_root_network_info().emission`

---

## Troubleshooting Reference

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Network issue | Use fallback endpoints, check internet |
| Rate limit exceeded | Too many requests | Add delay between calls |
| Registration failed | Insufficient balance | Add TAO to wallet |
| Transaction rejected | Duplicate transaction | Wait and retry |
| Wallet not found | Wrong path/name | Verify wallet path/name |
| MEV transaction stuck | Validator issues | Disable MEV protection |
| Weights not updating | Commit-reveal period | Wait for reveal phase |
