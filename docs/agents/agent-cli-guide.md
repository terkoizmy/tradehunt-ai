# Agent CLI Guide

## Overview
The agent CLI runs a quant persona as a long-lived process that continuously observes the market, generates signals, consults the LLM, validates risk, and executes trades on Bybit testnet.

## Quick Start
```bash
conda activate tradehunt-ai
cd agents

# Run conservative persona on BTCUSDT with $10,000 capital
python -m src.main --persona conservative --symbol BTCUSDT --capital 10000

# Run aggressive persona on ETHUSDT with 5-minute candles
python -m src.main --persona aggressive --symbol ETHUSDT --capital 5000 --interval 5

# Run with custom loop interval (30 seconds)
python -m src.main --persona sentiment --symbol BTCUSDT --capital 10000 --loop 30
```

## CLI Options
| Flag | Default | Description |
|------|---------|-------------|
| `--persona` | conservative | Which quant persona to run. Options: `aggressive`, `conservative`, `sentiment`, `arbitrageur` |
| `--symbol` | BTCUSDT | Trading pair (must match Bybit testnet linear perpetuals) |
| `--capital` | 10000 | Starting capital in USD |
| `--interval` | 15 | Kline interval in minutes (1, 3, 5, 15, 30, 60, 120, 240, 360, 720) |
| `--loop` | 60 | Seconds between trading loop iterations |

## Agent Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│                     STARTUP                              │
│  1. Load persona config                                 │
│  2. Initialize BybitClient, BybitMCP, DecisionEngine    │
│  3. Initialize RiskManager with persona + capital        │
│  4. Sync open positions from Bybit API                  │
│  5. Set up graceful shutdown (SIGINT/SIGTERM)           │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                     LOOP (every N seconds)               │
│                                                          │
│  1. OBSERVE                                              │
│     ├── Fetch market snapshot (price, bid/ask, volume)   │
│     ├── Fetch klines (OHLCV data)                        │
│     └── Analyze market context (trend, volatility)       │
│                                                          │
│  2. DECIDE                                               │
│     ├── Strategy.analyze(df, symbol) → Signal            │
│     ├── DecisionEngine.decide_with_threshold() → dict   │
│     │   ├── Persona system prompt → LLM system message   │
│     │   ├── Market data + signal → LLM user message     │
│     │   ├── Ollama returns JSON decision                 │
│     │   └── Confidence threshold filter applied          │
│     └── RiskManager.evaluate() → RiskDecision            │
│                                                          │
│  3. ACT                                                  │
│     ├── If allowed: BybitClient.place_order()            │
│     ├── Increment open positions on success             │
│     └── Log result (order ID, qty, SL, TP)              │
│                                                          │
│  4. SYNC                                                 │
│     ├── Sync open positions from Bybit API              │
│     ├── Feed realized PnL to RiskManager                │
│     └── Track closed trade IDs to avoid double-counting │
│                                                          │
│  5. SLEEP (loop_seconds) or wait for shutdown signal     │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   SHUTDOWN     │
              │ Close WS/HTTP  │
              │ Log exit       │
              └────────────────┘
```

## Strategy-Persona Mapping
Each persona is mapped to a default strategy:

| Persona | Strategy | Reasoning |
|---------|----------|-----------|
| aggressive | MomentumStrategy | Trend-following, high conviction |
| conservative | MeanReversionStrategy | Wait for extremes, tight stops |
| sentiment | MomentumStrategy | Fallback (no sentiment strategy yet) |
| arbitrageur | MeanReversionStrategy | Fallback (no arbitrage strategy yet) |

## Risk Management Flow

```
Trade Signal → RiskManager.evaluate()
│
├── Action is "hold" → Allow (no position change)
│
├── Confidence < persona threshold → Block
│   "Confidence 0.45 below persona threshold 0.55"
│
├── Open positions >= max (3) → Block
│   "Max open positions (3) reached"
│
├── Daily loss >= max (5% of capital) → Block
│   "Daily loss limit reached"
│
└── All checks pass → Allow
    ├── Position size = capital * position_size_pct * signal_strength * max_leverage
    ├── Stop-loss = price * (1 ± stop_loss_pct)
    └── Take-profit = price * (1 ± take_profit_pct)
```

## Environment Variables
Required in `.env`:
```bash
# Bybit Testnet
BYBIT_API_KEY=your_testnet_api_key
BYBIT_API_SECRET=your_testnet_api_secret
BYBIT_TESTNET=true

# Ollama Cloud API
OLLAMA_API_URL=http://localhost:11434
OLLAMA_API_KEY=                        # Optional
OLLAMA_MODEL=qwen2.5:7b               # Or any Ollama model
```

## Logging
The agent uses Python's `logging` module with logger name `tradehunt`. Output format:
```
2026-05-22 14:30:00 [INFO] [Aggressive Momentum Hunter] BUY | Confidence: 0.85 | EXECUTED abc123 | Qty: 0.001500 | SL: 48000.00 | TP: 52800.00
2026-05-22 14:30:00 [INFO]   Reasoning: Strong bullish EMA+MACD crossover. RSI: 45.2
2026-05-22 14:31:00 [INFO] Realized PnL recorded: 150.00
2026-05-22 14:31:00 [WARNING] Could not sync closed PnL: connection timeout
```

## Graceful Shutdown
Press Ctrl+C or send SIGTERM. The agent:
1. Logs "Shutdown signal received"
2. Finishes current loop iteration (does not interrupt mid-trade)
3. Closes Bybit WebSocket connection
4. Logs "Agent loop exited"

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `BYBIT_API_KEY must be set` | Add keys to `.env` file |
| `Ollama connection refused` | Check `OLLAMA_API_URL` is reachable |
| `Insufficient data` signal | Strategy needs more kline bars (200+ for MACD) |
| All trades show `HOLD — Confidence 0.x below threshold` | LLM confidence is low; try a different model or lower persona threshold |
| `Daily loss limit reached` | Agent hit 5% daily loss cap; it resets at UTC midnight or on restart |