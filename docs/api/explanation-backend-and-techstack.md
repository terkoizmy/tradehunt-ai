# Backend API — Architecture & Tech Stack

## Overview
FastAPI server that manages agent lifecycle, orchestrates arena competitions, and bridges off-chain trading to on-chain logging.

## Tech Stack
- **FastAPI** — async Python web framework
- **Uvicorn** — ASGI server
- **SQLAlchemy 2.0** — async ORM
- **asyncpg** — PostgreSQL async driver
- **Alembic** — database migrations
- **Pydantic v2** — request/response schemas
- **web3.py** — Ethereum contract interactions
- **WebSocket** — real-time trade streaming

## Database Schema

### agents
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(100) | Agent display name |
| persona | VARCHAR(50) | aggressive/conservative/sentiment/arbitrageur |
| agent_uri | TEXT | ERC-8004 metadata URI |
| onchain_id | INTEGER | ERC-8004 NFT token ID (nullable until registered) |
| wallet_address | VARCHAR(42) | Agent's Mantle address |
| status | VARCHAR(20) | idle/running/stopped |
| config | JSONB | Persona-specific parameters |
| created_at | TIMESTAMP | |

### trades
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| agent_id | UUID FK | Reference to agents |
| symbol | VARCHAR(20) | BTCUSDT, ETHUSDT, etc. |
| side | VARCHAR(4) | buy/sell |
| price | DECIMAL | Execution price |
| quantity | DECIMAL | Order quantity |
| pnl | DECIMAL | Realized PnL (nullable) |
| confidence | DECIMAL | LLM confidence score (0-1) |
| reasoning | TEXT | LLM reasoning text |
| tx_hash | VARCHAR(66) | On-chain TradeRegistry tx |
| created_at | TIMESTAMP | |

### arena_sessions
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(100) | Session name |
| status | VARCHAR(20) | pending/active/completed |
| start_time | TIMESTAMP | |
| end_time | TIMESTAMP | |
| onchain_id | INTEGER | ArenaLeaderboard session ID |
| created_at | TIMESTAMP | |

### arena_scores
| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| session_id | UUID FK | Reference to arena_sessions |
| agent_id | UUID FK | Reference to agents |
| total_pnl | DECIMAL | Cumulative PnL |
| sharpe_ratio | DECIMAL | |
| win_rate | DECIMAL | |
| trade_count | INTEGER | |
| rank | INTEGER | Current rank in session |

## API Endpoints

### Agents
- `GET /api/agents` — list all, filter by status/persona
- `GET /api/agents/{id}` — detail with stats
- `POST /api/agents` — register new agent
- `POST /api/agents/{id}/start` — start trading
- `POST /api/agents/{id}/stop` — stop trading

### Arena
- `GET /api/arena/sessions` — list sessions
- `POST /api/arena/sessions` — create new session
- `GET /api/arena/sessions/{id}` — session detail + scores

### Leaderboard
- `GET /api/leaderboard/{session_id}` — ranked scores
- `GET /api/leaderboard/{session_id}/history` — score snapshots over time

### Trades
- `GET /api/trades` — paginated trade history, filterable by agent/session

### WebSocket
- `WS /ws/trades` — real-time trade events
- `WS /ws/arena/{session_id}` — live score updates

## Scoring Algorithm
After each trade event from TradeRegistry:
1. Query all trades for agent in session window
2. Calculate: total PnL, win rate (pnl > 0 / total), Sharpe (mean(pnl) / std(pnl) * sqrt(trades))
3. Update arena_scores table
4. Submit score on-chain via ArenaLeaderboard.submitScore()
5. Broadcast score update via WebSocket

## Contract Bridge
`services/contract_bridge.py`:
- Loads contract ABIs from contracts/out/
- Uses web3.py with Mantle Sepolia RPC
- Signs transactions with PRIVATE_KEY from .env
- Logs trades, submits scores, registers agents
- Retry logic for tx failures
