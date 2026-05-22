# Contract Bridge — Python → Solidity Trade Logging

## Overview

The contract bridge (`api/src/services/contract_bridge.py`) is the critical link between off-chain Bybit trade execution and the on-chain audit trail on Mantle Sepolia. It uses `web3.py` to sign and broadcast transactions to the `TradeRegistry` contract.

## Architecture

```
Agent Engine / Backend
         │
         ▼
   ContractBridge
         │
         ▼
   web3.py HTTPProvider
         │
         ▼
   Mantle Sepolia RPC
         │
         ▼
   TradeRegistry.logTrade()
```

## Transaction Flow

1. **Link Agent** (one-time per agent)
   - Backend (owner) calls `TradeRegistry.linkAgent(agentId, wallet)`
   - This authorizes the wallet to call `logTrade` for that agentId

2. **Log Trade** (after every execution)
   - Backend builds a legacy transaction (`gasPrice`, not EIP-1559)
   - Signs with `PRIVATE_KEY` from `.env`
   - Sends via `send_raw_transaction`
   - Waits for receipt with 60s timeout
   - Returns tx hash on success

## Error Handling

- **ConnectionError**: Raised if Mantle RPC is unreachable on bridge init
- **ValueError**: Raised if `TRADE_REGISTRY_ADDRESS` is missing
- **Retry logic**: Up to 3 attempts with 2s delay between
  - Refreshes nonce after each failure (prevents "nonce too low")
- **Receipt check**: Verifies `status == 1` (success); raises on revert

## Gas Configuration

Mantle Sepolia uses legacy transactions:

```python
GAS_PRICE_GWEI = 0.05
GAS_LIMIT_LOG_TRADE = 300_000
GAS_LIMIT_LINK_AGENT = 100_000
```

Adjust `GAS_PRICE_GWEI` if transactions stall.

## API

```python
from api.src.services.contract_bridge import ContractBridge

bridge = ContractBridge()

# One-time per agent
tx_hash = await bridge.link_agent(agent_id=1, agent_wallet="0x...")

# After each trade
tx_hash = await bridge.log_trade(
    agent_id=1,
    symbol="BTCUSDT",
    side="Buy",
    price=Decimal("50000"),
    quantity=Decimal("1"),
    pnl=Decimal("100"),
)

# Read stats
stats = await bridge.get_agent_stats(agent_id=1)
# {"total_trades": 42, "total_pnl": 1500, "win_count": 30}
```

## Environment Variables

```bash
MANTLE_SEPOLIA_RPC_URL=https://rpc.sepolia.mantle.xyz
PRIVATE_KEY=0x...        # deployer wallet with MNT for gas
TRADE_REGISTRY_ADDRESS=0x9bdB714930efaBb41A0647809fe980d173E2d510
```

## Testing

```bash
cd api
pytest tests/test_contract_bridge.py -v
```

Tests mock `web3.py` to avoid hitting the real chain. They verify:
- Retry logic (success, retry-then-success, exhaust)
- Correct function calls for `linkAgent`, `logTrade`, `getAgentStats`

## Manual Test on Mantle Sepolia

```bash
# Load env and run a quick script
source .env
python -c "
import asyncio
from api.src.services.contract_bridge import ContractBridge

async def main():
    b = ContractBridge()
    stats = await b.get_agent_stats(1)
    print(stats)

asyncio.run(main())
"
```
