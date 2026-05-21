# MEMORY.md — tradehunt-ai Project Memory

## Project Origin
Started May 21, 2026 for the Mantle Turing Test Hackathon 2026 Phase 2.
Deadline: June 15, 2026 (25 days).

## Key Decisions

### Testnet-Only Strategy
**Decision**: All development and demo on testnets (Mantle Sepolia, Bybit testnet).
**Why**: Zero cost, no real funds at risk, hackathon only requires demo.
**Implication**: All private keys, API keys are testnet — no need for hardware wallets or multisig.

### Ollama Over Claude API for Agent Decisions
**Decision**: Use Ollama Cloud API instead of Anthropic Claude API for the agent's trading brain.
**Why**: Cost-effective for high-frequency LLM calls during trading, open-source models, structured output support.
**Implication**: May need prompt engineering tuning for trading-specific reasoning.

### Postgres from Day 1
**Decision**: Use Postgres 16 in Docker instead of SQLite even for development.
**Why**: Production-grade from start, no migration surprises, hackathon shows "real" infrastructure.
**Implication**: Docker required for local dev, Alembic migrations from first model.

### React + Vite Over Next.js
**Decision**: Use Vite SPA instead of Next.js.
**Why**: Dashboard is a SPA, no SSR needed, lighter setup, faster HMR.
**Implication**: Client-side routing only (React Router), no API routes in frontend.

### Conda Environment
**Decision**: Use conda env `tradehunt-ai` with Python 3.12.
**Why**: Standard in quant/data science, isolated, reproducible.
**Implication**: All terminal sessions must start with `conda activate tradehunt-ai`.

## Architecture Notes
- Agent engine is separate from API server — agents can run independently via CLI
- Contract bridge (api → contracts) logs trades on-chain after execution
- WebSocket broadcasts trade events to frontend in real-time
- ERC-8004 identity is the anchor tying agent off-chain persona to on-chain reputation

## Known Unknowns
- ERC-8004 contract address on Mantle Sepolia (need to verify deployment)
- Ollama model selection for trading (need to benchmark qwen2.5 vs llama3.1)
- Bybit testnet API rate limits (need to test with concurrent agents)
