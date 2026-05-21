# Agent Engine — Architecture & Tech Stack

## Overview
The agent engine is the core of tradehunt-ai. Each agent is a Python process with:
- A **quant persona** (personality + risk profile) that shapes decision-making
- **Trading strategies** (momentum, mean reversion, etc.) that generate signals
- An **LLM brain** (Ollama Cloud API) that reasons about market data
- A **Bybit execution layer** that places trades on testnet

## Tech Stack
- **Python 3.12** — async/await, type hints
- **pybit v5.16.0** — Bybit REST + WebSocket (unified_trading)
- **numpy + pandas** — technical indicators, data manipulation
- **httpx** — async HTTP client for Ollama API
- **Pydantic v2** — data validation, settings, structured LLM output

## Architecture

### Persona System
```
Persona (base)
├── name, risk_profile, max_drawdown, system_prompt
├── get_position_size(capital, signal_strength) → float
└── format_market_context(data) → str (for LLM prompt)

AggressivePersona    — 2x leverage, momentum-heavy, high turnover
ConservativePersona  — 1x, mean-reversion, strict stop-loss
SentimentPersona     — news-driven, NLP sentiment scoring
ArbitrageurPersona   — cross-exchange spread hunting
```

### Strategy Engine
Each strategy is a standalone class that takes OHLCV data and returns signals:
```
Strategy (base)
└── analyze(df: pd.DataFrame) → Signal(action, confidence, metadata)

MomentumStrategy     — RSI(14), MACD, EMA crossover
MeanReversionStrategy — Bollinger Bands(20,2), RSI extremes
GridTradingStrategy  — Price grid levels, auto-rebalance
MacroSwingStrategy   — Multi-timeframe EMA alignment
```

### Decision Flow
1. `MarketData` pipeline aggregates Bybit WS + Pyth oracle
2. Strategy produces technical signal
3. Persona formats market context + signal into LLM prompt
4. Ollama Cloud API returns structured decision JSON
5. Risk manager validates position size, stop-loss, exposure
6. `BybitClient` executes order on testnet

### LLM Integration
- Ollama Cloud API endpoint configurable via `OLLAMA_API_URL`
- Model configurable via `OLLAMA_MODEL` (recommended: qwen2.5:7b)
- Structured output mode forces JSON: `{action, symbol, size, confidence, reasoning}`
- Persona system prompt injected as first message
- Reasoning string displayed in arena UI as "agent thought process"

### Backtesting
- Historical kline data from Bybit testnet
- Replay loop: for each candle → strategy → simulate fill → track PnL
- Metrics: Sharpe ratio, max drawdown, win rate, profit factor, equity curve
- Used to calibrate persona parameters (stop-loss %, position sizing, indicator thresholds)
