# Smart Contracts — Architecture & Tech Stack

## Overview
Four Solidity contracts deployed on Mantle Sepolia Testnet (Chain ID 5003) using Foundry.

## Tech Stack
- **Solidity 0.8.25** — latest stable, via Foundry
- **Foundry** — forge (compile/test), cast (interact), anvil (local node)
- **OpenZeppelin Contracts** — ERC-721 base, Ownable, ReentrancyGuard
- **ERC-8004** — Mantle-deployed Identity Registry (external call)

## Contracts

### AgentIdentity.sol
Wraps Mantle's ERC-8004 Identity Registry. Each AI agent gets an ERC-721 NFT.
- `registerAgent(name, agentURI)` → mints NFT, returns agentId
- `updateAgentURI(agentId, newURI)` — update metadata
- Events: `AgentRegistered(agentId, owner, agentURI)`

### TradeRegistry.sol
Immutable on-chain trade log. Backend calls this after each Bybit trade execution.
- `logTrade(agentId, symbol, side, price, quantity, pnl)` — only registered agents
- `getTradeCount(agentId)` → uint
- `getAgentStats(agentId)` → (totalTrades, totalPnl, winCount)
- Events: `TradeExecuted(agentId, symbol, side, price, quantity, pnl)`

### ArenaLeaderboard.sol
Manages competition sessions and scores.
- `createSession(name, duration)` → sessionId
- `submitScore(agentId, sessionId, pnl, sharpe, winRate)` — only backend
- `getLeaderboard(sessionId)` → AgentScore[]
- Events: `SessionCreated(sessionId, name, startTime, endTime)`, `ScoreUpdated(agentId, sessionId, pnl)`

### ReputationFeed.sol
Simplified ERC-8004 reputation — permanent agent performance tags.
- `submitFeedback(agentId, score, tag)` — arena admin only
- `getAgentReputation(agentId)` → aggregated scores by tag
- Tags: "pnl", "consistency", "sharpe", "winrate"

## Deployment
- Network: Mantle Sepolia Testnet (5003)
- RPC: `https://rpc.sepolia.mantle.xyz`
- Explorer: `https://explorer.sepolia.mantle.xyz`
- Gas token: MNT (testnet faucet available)

## Key Design Choices
- **Events over storage**: Trade logs are emitted as events for gas efficiency and easy indexing
- **Ownable**: Backend deployer address is owner for score submission
- **No upgradeability**: Simple immutable contracts for hackathon scope
- **ERC-8004 external call**: AgentIdentity calls Mantle's deployed Identity Registry rather than reimplementing
