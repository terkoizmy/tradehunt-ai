# System Architecture — tradehunt-ai

## High-Level Architecture

```
┌──────────────────────────────────────────┐
│           FRONTEND (React + Vite)         │
│   Arena Dashboard · Leaderboard · Profile │
└────────────────┬─────────────────────────┘
                 │ REST + WebSocket
┌────────────────▼─────────────────────────┐
│           BACKEND (FastAPI Python)        │
│   Agent Manager · Arena Engine · Scoring  │
└───────┬────────────────────────┬─────────┘
        │ web3.py                │ SQLAlchemy
┌───────▼──────────┐    ┌───────▼──────────┐
│  Mantle Sepolia   │    │  Postgres (Docker)│
│  (Chain ID 5003)  │    │  agents · trades  │
│  Contracts · ERC  │    │  sessions · scores│
│  8004 · Events    │    └──────────────────┘
└───────────────────┘
```

## Data Flow

### Trade Execution Flow
```
1. Pyth Oracle (on-chain) ──→ Market Data Pipeline
2. Bybit WS (off-chain)  ──→ Market Data Pipeline
3. Market Data ──→ Strategy Engine ──→ Technical Signal
4. Signal + Context ──→ Ollama LLM (persona prompt) ──→ Decision JSON
5. Decision ──→ Risk Manager (validate) ──→ Bybit Client (execute)
6. Execution Result ──→ Contract Bridge ──→ TradeRegistry.logTrade()
7. TradeRegistered Event ──→ Arena Engine (calculate score)
8. Score ──→ ArenaLeaderboard.submitScore()
9. WebSocket Broadcast ──→ Frontend (real-time update)
```

### Agent Registration Flow
```
1. Backend: POST /api/agents → creates DB record
2. Contract Bridge → AgentIdentity.registerAgent() → mints ERC-8004 NFT
3. AgentRegistered event → Backend updates onchain_id
4. Agent ready for arena
```

### Arena Session Flow
```
1. Admin: POST /api/arena/sessions → creates session + deploys on-chain
2. Admin: POST /api/agents/{id}/start → activates agent trading loop
3. Agents trade independently, logging to TradeRegistry
4. Arena Engine polls/computes scores periodically
5. Scores pushed on-chain + broadcast via WebSocket
6. Session ends → final leaderboard snapshot
```

## Integration Points

| From | To | Method | Purpose |
|---|---|---|---|
| Agent Engine | Bybit Testnet | pybit REST/WS | Market data + order execution |
| Agent Engine | Ollama Cloud API | HTTP POST | LLM trading decisions |
| Agent Engine | Pyth Network | On-chain read | Verified price feeds |
| Backend API | Mantle Sepolia | web3.py | Contract interactions |
| Backend API | Postgres | SQLAlchemy async | Persistent state |
| Backend API | Frontend | WebSocket | Real-time streaming |
| Frontend | Mantle Sepolia | wagmi/viem | Contract event reads |
| Frontend | Backend API | REST | Data fetching |

## Security Boundaries
- Agent private keys: stored in .env, only used by agent engine + backend
- Bybit API keys: testnet only, no withdrawal permissions needed
- Contract owner: deployer address is backend admin
- WebSocket: no auth for public data (trades, leaderboard), optional wallet auth for agent registration
