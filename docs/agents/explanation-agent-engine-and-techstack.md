# Agent Engine — Architecture & Tech Stack

## Overview
The agent engine is the core of tradehunt-ai. Each agent is a Python process with:
- A **quant persona** (personality + risk profile) that shapes decision-making
- **Trading strategies** (momentum, mean reversion, etc.) that generate signals
- An **LLM brain** (Ollama Cloud API) that reasons about market data
- A **risk manager** that validates position size, stop-loss, and exposure limits
- A **Bybit execution layer** that places trades on testnet

**Detailed docs:**
- [Personas](personas.md) — all persona configs, how to add new ones
- [Strategies](strategies.md) — all strategy details, parameters, how to extend
- [LLM Decision Engine & Backtesting](llm-decision-engine.md) — Ollama API, validation, backtest metrics
- [Agent CLI Guide](agent-cli-guide.md) — CLI flags, loop lifecycle, risk flow, troubleshooting

## Tech Stack
- **Python 3.12** — async/await, type hints, Decimal for financial precision
- **pybit v5.16.0** — Bybit REST + WebSocket (unified_trading)
- **numpy + pandas** — technical indicators, data manipulation
- **httpx** — async HTTP client for Ollama API
- **Pydantic v2** — TradeDecision validation, structured LLM output

## Architecture

### Persona System
```
PersonaConfig (dataclass)
├── name, risk_profile, max_drawdown, max_leverage
├── position_size_pct, stop_loss_pct, take_profit_pct
├── confidence_threshold, preferred_timeframes
└── description

BasePersona (ABC)
├── config: PersonaConfig
├── system_prompt: str (injected as LLM system message)
├── voice: str (tagline for arena display)
├── get_position_size(capital, signal_strength) → Decimal
└── format_market_context(market_data_str, signal_str) → str

AggressivePersona    — 5x leverage, 25% dd, momentum, wide stops
ConservativePersona  — 1x (no leverage), 10% dd, mean-reversion, tight stops
SentimentPersona     — 2x leverage, 15% dd, moderate risk
ArbitrageurPersona   — 1x leverage, 5% dd, tight spreads
```

### Strategy Engine
Each strategy is a standalone class that takes OHLCV data and returns signals:
```
Signal (dataclass)
├── action: "buy" | "sell" | "hold"
├── symbol: str
├── confidence: Decimal (0.0–1.0)
├── price: Decimal
├── reasoning: str
└── metadata: dict (indicator values, crossover flags, etc.)

Shared Indicators (agents/src/strategies/indicators.py)
└── calc_rsi(prices, period) → pd.Series

MomentumStrategy     — RSI(14), MACD(12/26/9), EMA crossover
MeanReversionStrategy — Bollinger Bands(20,2), RSI extremes, dynamic confidence
MacroSwingStrategy   — Multi-timeframe SMA alignment (20/50/200)
GridTradingStrategy  — Stub (always returns hold)
```

### Decision Flow
1. **Observe** — `BybitClient` fetches market snapshot + klines; `BybitMCP` enriches with trend/volatility/volume context
2. **Signal** — Strategy produces technical signal with confidence and metadata
3. **Decide** — `DecisionEngine` sends persona system prompt + market data + signal to Ollama; returns validated `TradeDecision`; `decide_with_threshold()` filters by persona confidence
4. **Risk check** — `RiskManager` validates against persona risk params (SL/TP, position size, daily loss limit, open positions)
5. **Act** — `BybitClient.place_order()` executes on testnet; `increment_open()` on success
6. **Sync** — Poll `get_positions()` + `get_closed_pnl()` to sync open position count and feed realized PnL to risk manager

### LLM Integration
- Ollama Cloud API endpoint configurable via `OLLAMA_API_URL`
- Model configurable via `OLLAMA_MODEL` (recommended: qwen2.5:7b)
- Structured output mode forces JSON: `{action, symbol, confidence, reasoning}`
- Persona system prompt sent as **system message** (not user message)
- Market data + signal sent as **user message**
- `TradeDecision` Pydantic model validates: action regex, confidence bounds, type coercion
- Exponential backoff on HTTP errors (3 retries, base 1s delay)
- Falls back to `{action: "hold", confidence: 0.0}` on any failure

### Risk Management
```
RiskManager(persona, capital, config)
├── evaluate(action, price, confidence, signal_strength) → RiskDecision
│   ├── Check confidence >= persona.confidence_threshold
│   ├── Check open positions < max (default 3)
│   ├── Check daily loss < max (default 5%)
│   ├── Position size = capital * persona.position_size_pct * signal_strength * persona.max_leverage
│   ├── Stop-loss = price * (1 ± persona.stop_loss_pct)
│   └── Take-profit = price * (1 ± persona.take_profit_pct)
├── increment_open() — called after successful order
├── decrement_open() — called when position closes (via sync)
├── update_pnl(pnl) — called from closed PnL sync
├── sync_open_positions(count) — sync with Bybit API
└── reset_daily() — reset daily PnL tracker
```

### Backtesting
- Historical kline data from Bybit testnet
- Replay loop: for each candle → strategy → simulate fill → track equity
- Supports long and short positions with SL/TP simulation using bar high/low
- Persona-aware: applies persona-specific SL/TP percentages
- Metrics: Sharpe ratio (pct returns), max drawdown, win rate, profit factor, equity curve
- Trade records: entry, exit, PnL, side, exit reason (stop_loss/take_profit/end_of_data)
- See [LLM Decision Engine & Backtesting](llm-decision-engine.md) for full details
