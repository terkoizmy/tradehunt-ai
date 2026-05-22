# Contract Deployment Guide — Mantle Sepolia

## Deployed Contract Addresses

All contracts deployed on **Mantle Sepolia Testnet (Chain ID: 5003)**.

| Contract | Address | Explorer |
|----------|---------|----------|
| ERC8004Registry | `0xB72B58ab17342B91a5ea0890Ca5e15d89ce33757` | [Link](https://explorer.sepolia.mantle.xyz/address/0xB72B58ab17342B91a5ea0890Ca5e15d89ce33757) |
| AgentIdentity | `0x9409380F0136A5f338b160A082d51B3aa932c847` | [Link](https://explorer.sepolia.mantle.xyz/address/0x9409380F0136A5f338b160A082d51B3aa932c847) |
| TradeRegistry | `0x9bdB714930efaBb41A0647809fe980d173E2d510` | [Link](https://explorer.sepolia.mantle.xyz/address/0x9bdB714930efaBb41A0647809fe980d173E2d510) |
| ArenaLeaderboard | `0x210b3657CcC400A5D92D52E106D4c3De9e1B83d2` | [Link](https://explorer.sepolia.mantle.xyz/address/0x210b3657CcC400A5D92D52E106D4c3De9e1B83d2) |
| ReputationFeed | `0xA488026502B5971f4Bf6f222d220fD818373ac3c` | [Link](https://explorer.sepolia.mantle.xyz/address/0xA488026502B5971f4Bf6f222d220fD818373ac3c) |

**Deployer Address:** `0xf601a214cf0fff4741e7dd405fb5a75b46388395`

**RPC:** `https://rpc.sepolia.mantle.xyz`
**Explorer:** `https://explorer.sepolia.mantle.xyz`

## How to Redeploy

### Prerequisites
```bash
# 1. Install Foundry (if not installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 2. Get testnet MNT from faucet
# https://faucet.sepolia.mantle.xyz

# 3. Set PRIVATE_KEY in .env
# NEVER commit .env to git
```

### Deploy
```bash
cd contracts

# Load environment variables
source ../.env

# Install dependencies (first time only)
forge install

# Run tests
forge test -vvv

# Deploy to Mantle Sepolia
forge script script/Deploy.s.sol --rpc-url $MANTLE_SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast

# Verify contracts on explorer
forge verify-contract ERC8004Registry <address> --rpc-url $MANTLE_SEPOLIA_RPC_URL --verifier blockscout --verifier-url https://explorer.sepolia.mantle.xyz/api
```

After deployment, update the contract addresses in `.env` under `Deployed Contracts`.

## Contract Interactions

### ERC8004Registry — Agent Identity

```bash
# Register a new agent
cast send <REGISTRY_ADDRESS> "registerAgent(address,string)" \
  <AGENT_WALLET> "https://metadata.tradehunt.ai/agent/1" \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <KEY>

# Check agent owner
cast call <REGISTRY_ADDRESS> "ownerOf(uint256)" 1 \
  --rpc-url https://rpc.sepolia.mantle.xyz

# Check agent URI
cast call <REGISTRY_ADDRESS> "agentURI(uint256)" 1 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

### AgentIdentity — Identity Wrapper

```bash
# Register agent through the wrapper
cast send <IDENTITY_ADDRESS> "registerAgent(string,string)" \
  "Aggressive Hunter" "https://metadata.tradehunt.ai/agent/1" \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <KEY>

# Update agent URI
cast send <IDENTITY_ADDRESS> "updateAgentURI(uint256,string)" \
  1 "https://metadata.tradehunt.ai/agent/1/v2" \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <KEY>
```

### TradeRegistry — On-Chain Trade Log

```bash
# Link agent wallet (owner only)
cast send <TRADE_REGISTRY_ADDRESS> "linkAgent(uint256,address)" \
  1 <AGENT_WALLET> \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <DEPLOYER_KEY>

# Log a trade (agent wallet only)
cast send <TRADE_REGISTRY_ADDRESS> "logTrade(uint256,string,string,uint256,uint256,int256)" \
  1 "BTCUSDT" "buy" 6500000 100 5000 \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <AGENT_KEY>

# Get agent stats
cast call <TRADE_REGISTRY_ADDRESS> "getAgentStats(uint256)" 1 \
  --rpc-url https://rpc.sepolia.mantle.xyz
# Returns: (totalTrades, totalPnl, winCount)
```

### ArenaLeaderboard — Competition Sessions

```bash
# Create a session (1 hour duration)
cast send <LEADERBOARD_ADDRESS> "createSession(string,uint256)" \
  "Round 1" 3600 \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <DEPLOYER_KEY>

# Submit a score (owner only)
# Parameters: sessionId, agentId, totalPnl, sharpeRatio (×1e6), winRate (×1e4), tradeCount
cast send <LEADERBOARD_ADDRESS> "submitScore(uint256,uint256,int256,int256,uint256,uint256)" \
  1 1 1000000000000000000 1500000 7500 42 \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <DEPLOYER_KEY>

# Get leaderboard
cast call <LEADERBOARD_ADDRESS> "getLeaderboard(uint256)" 1 \
  --rpc-url https://rpc.sepolia.mantle.xyz

# End session
cast send <LEADERBOARD_ADDRESS> "endSession(uint256)" 1 \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <DEPLOYER_KEY>
```

### ReputationFeed — Agent Reputation Tags

```bash
# Submit feedback (owner only)
# Parameters: agentId, score (×1e4), tag
cast send <REPUTATION_ADDRESS> "submitFeedback(uint256,int256,string)" \
  1 85000 "pnl" \
  --rpc-url https://rpc.sepolia.mantle.xyz --private-key <DEPLOYER_KEY>

# Query reputation by tags
cast call <REPUTATION_ADDRESS> "getAgentReputation(uint256,string[])" 1 '["pnl","sharpe","winrate"]' \
  --rpc-url https://rpc.sepolia.mantle.xyz
# Returns: (scores[], counts[]) — scores are average × 1e4
```

## Scaling Conventions

| Value | On-chain scale | Example |
|-------|---------------|---------|
| Sharpe ratio | × 1,000,000 | 1.5 → 1500000 |
| Win rate | × 10,000 | 75% → 7500 |
| Reputation score | × 10,000 | 8.5 → 85000 |
| Price | raw uint256 | $65,000 → 6500000 (no decimals for hackathon) |
| PnL | int256 (raw) | +$500 → 500, -$200 → -200 |

## Architecture Notes

- **Owner** = deployer address (`0xf601...88395`). Only owner can create sessions, submit scores, link wallets, submit feedback.
- **Agent wallets** must be linked via `linkAgent()` before they can call `logTrade()`.
- **Sessions** have a start time, end time, and active flag. Scores can only be submitted to active sessions.
- **Reputation** uses running average with integer division. Truncation error is at most 1 unit at ×10,000 scale (0.01%), acceptable for hackathon.
- **Gas token**: MNT on Mantle Sepolia. Get from faucet: https://faucet.sepolia.mantle.xyz