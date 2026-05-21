# WORKFLOW.md — Development Workflow

## Prerequisites
- Conda (Miniconda or Anaconda)
- Docker Desktop
- Node.js 20+
- Foundry (`foundryup`)
- Git

## Initial Setup

### 1. Clone & Environment
```bash
git clone <repo-url>
cd tradehunt-ai
conda create -n tradehunt-ai python=3.12 -y
conda activate tradehunt-ai
```

### 2. Environment Variables
```bash
cp .env.example .env
# Fill in .env with your keys:
#   - PRIVATE_KEY: Mantle Sepolia wallet private key (with testnet MNT)
#   - BYBIT_API_KEY / BYBIT_API_SECRET: from testnet.bybit.com
#   - OLLAMA_API_URL / OLLAMA_API_KEY: Ollama Cloud credentials
```

### 3. Install Dependencies
```bash
# Python packages
pip install -e agents/
pip install -e api/

# Frontend
cd frontend && npm install && cd ..

# Contracts
cd contracts && forge install && cd ..
```

### 4. Start Services
```bash
# Postgres
docker-compose up -d

# Backend API
cd api && uvicorn src.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm run dev

# Run an agent (new terminal)
conda activate tradehunt-ai
cd agents && python -m src.main --persona aggressive
```

## Daily Workflow
1. `conda activate tradehunt-ai`
2. `docker-compose up -d`
3. Pull latest: `git pull origin main`
4. Work on feature branch: `git checkout -b feature/xxx`
5. Run tests before committing
6. Commit and push

## Testing
```bash
# Contract tests
cd contracts && forge test -vvv

# Backend tests
cd api && pytest -v

# Agent tests
cd agents && pytest -v
```

## Deploying Contracts
```bash
cd contracts
source ../.env  # or manually set env vars
forge script script/Deploy.s.sol --rpc-url $MANTLE_SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast
```

## Running Arena Session
1. Ensure Postgres is up and contracts are deployed
2. Start the API server
3. Register agents: `POST /api/agents`
4. Create arena session: `POST /api/arena/sessions`
5. Start agents: `POST /api/agents/{id}/start`
6. Open frontend at `/arena` to watch live

## Useful Commands
```bash
# Check Postgres
docker exec tradehunt-db psql -U tradehunt -d tradehunt -c "\dt"

# Alembic migrations
cd api && alembic revision --autogenerate -m "description"
cd api && alembic upgrade head

# Docker cleanup
docker-compose down -v  # removes volumes too
```
