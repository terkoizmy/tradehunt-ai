# CLAUDE.md — tradehunt-ai

## Project
AI trading hunter agent with quant persona + agent trading arena platform.
Built for Mantle Turing Test Hackathon 2026 Phase 2 (Alpha & Data Track, Path B).

## Stack
- **Agent Engine**: Python 3.12, pybit v5.16.0, numpy, pandas
- **LLM**: Ollama Cloud API (structured JSON output)
- **Smart Contracts**: Solidity (Foundry), deployed on Mantle Sepolia Testnet (chain 5003)
- **Backend**: FastAPI + SQLAlchemy async + asyncpg + Alembic
- **Database**: Postgres 16 (Docker)
- **Frontend**: React 18 + Vite + TypeScript + wagmi + viem + React Router
- **Data**: Pyth oracles, Bybit WebSocket, Covalent API
- **Identity**: ERC-8004 agent NFT standard

## Environment
Always activate conda env before working:
```bash
conda activate tradehunt-ai
```

## Project Layout
```
tradehunt-ai/
├── agents/          # Python AI agent engine (personas, strategies, execution, LLM, backtesting)
├── contracts/       # Solidity contracts (Foundry) — AgentIdentity, TradeRegistry, ArenaLeaderboard, ReputationFeed
├── api/             # FastAPI backend — routes, services, DB, WebSocket
├── frontend/        # React + Vite + TypeScript — arena dashboard, leaderboard, agent profiles
├── docs/            # Project documentation per package
├── docker-compose.yml  # Postgres 16 + pgAdmin
└── .env             # Environment variables (from .env.example)
```

## Working on Issues
Before starting any issue, always read the relevant docs in `docs/` for context and direction. Each package has its own explanation doc:
- `docs/agents/` — agent engine architecture and tech stack
- `docs/contracts/` — smart contract specs and deployment
- `docs/frontend/` — frontend components and design system
- `docs/api/` — backend API and database schema
- `docs/architecture/` — full system architecture and data flow
- `docs/MEMORY.md` — key decisions and project context
- `docs/WORKFLOW.md` — day-to-day development workflow

## Dev Workflow
1. `conda activate tradehunt-ai`
2. `docker-compose up -d` (start Postgres)
3. `cd api && uvicorn src.main:app --reload` (backend on :8000)
4. `cd frontend && npm run dev` (frontend on :5173)
5. Run agent: `cd agents && python -m src.main --persona aggressive`

## Contract Dev
```bash
cd contracts
forge build
forge test
forge script script/Deploy.s.sol --rpc-url $MANTLE_SEPOLIA_RPC_URL --broadcast
```

## Key Conventions
- Python: type hints everywhere, Pydantic models for data, async where possible
- Solidity: events over storage, Foundry test patterns
- Frontend: functional components, custom hooks for WebSocket/contracts
- Git: feature branches, descriptive commits in English. Commit every completed feature immediately — do not batch unrelated changes. Each feature/fix gets its own commit with a clear message about what was done and why.
- All trading on Bybit testnet — no real funds
- All contracts on Mantle Sepolia testnet — no mainnet
