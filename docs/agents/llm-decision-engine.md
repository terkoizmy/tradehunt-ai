# LLM Decision Engine & Backtesting

## LLM Decision Engine

### Overview
The `DecisionEngine` sends market data + strategy signal + persona prompt to Ollama Cloud API and returns a structured trading decision. It acts as the "brain" that interprets technical signals through the lens of the agent's personality.

### Architecture
```
DecisionEngine
├── decide(persona_prompt, market_context, signal_text) → dict
├── decide_with_threshold(persona_prompt, market_context, signal, threshold) → dict
├── _parse_and_validate(content) → dict
└── _error_response(reason) → dict
```

### Decision Flow
1. Persona system prompt → system message (shapes LLM personality)
2. Market data + strategy signal → user message (provides context)
3. Ollama Cloud API returns JSON: `{action, symbol, confidence, reasoning}`
4. `TradeDecision` Pydantic model validates the response
5. `decide_with_threshold()` rejects trades below persona's confidence threshold

### Configuration
Environment variables:
```bash
OLLAMA_API_URL=http://localhost:11434   # Ollama Cloud API endpoint
OLLAMA_API_KEY=                          # API key (if required)
OLLAMA_MODEL=qwen2.5:7b                  # Model to use
```

Constructor parameters:
```python
DecisionEngine(
    api_url=None,        # Override OLLAMA_API_URL
    api_key=None,        # Override OLLAMA_API_KEY
    model=None,          # Override OLLAMA_MODEL
    max_retries=3,       # Number of retries on HTTP error
    base_delay=1.0,      # Exponential backoff base (seconds)
)
```

### Retry & Error Handling
- Retries up to `max_retries` times with exponential backoff (`base_delay * 2^(attempt-1)`)
- Uses `asyncio.sleep()` (non-blocking) between retries
- On HTTP errors (status, connect, timeout): retry
- On parse/validation errors: return hold
- On exhausted retries: return hold with error message

### Output Format
```python
{
    "action": "buy" | "sell" | "hold",
    "symbol": "BTCUSDT",
    "confidence": 0.85,
    "reasoning": "Strong bullish EMA+MACD crossover with RSI confirmation"
}
```

### TradeDecision Validation
The Pydantic model enforces:
- `action` must match `^(buy|sell|hold)$`
- `confidence` must be between 0.0 and 1.0
- String confidence values are coerced to float

### Confidence Threshold
`decide_with_threshold()` wraps `decide()` with persona-level filtering:
- If LLM confidence < persona's `confidence_threshold`, action is overridden to "hold"
- Reasoning includes the original decision and threshold explanation
- Example: Aggressive persona threshold = 0.55, Conservative = 0.75

### How to Change the Prompt
The LLM prompt is constructed in `decide()`:
1. **System message**: `persona_prompt` (from `BasePersona.system_prompt`)
2. **User message**: `### Market Data\n{market_context}\n\n### Technical Signal\n{signal_text}\n\nRespond ONLY with JSON...`

To change the prompt structure, modify the `user_prompt` string in `decision_engine.py:62-67`.

---

## Backtesting Engine

### Overview
`BacktestEngine` replays historical kline data through a strategy to measure performance. It simulates order fills, stop-loss/take-profit, and tracks equity over time.

### Key Features
- **Long and short positions** — supports both buy and sell entries
- **SL/TP simulation** — uses bar high/low to check if stop-loss or take-profit was hit within each candle
- **Persona-aware** — optional `persona` parameter applies persona-specific SL/TP percentages
- **Equity curve** — tracks absolute equity value at each bar
- **Trade-level detail** — each trade records entry, exit, PnL, side, and exit reason

### Usage
```python
from decimal import Decimal
from agents.src.backtesting.engine import BacktestEngine
from agents.src.strategies.momentum import MomentumStrategy
from agents.src.personas.aggressive import AggressivePersona

engine = BacktestEngine(initial_capital=Decimal("10000"))
strategy = MomentumStrategy()
persona = AggressivePersona()

# df must have columns: timestamp, open, high, low, close, volume
result = engine.run(df, strategy, "BTCUSDT", persona=persona)
```

### BacktestResult Fields
| Field | Type | Description |
|-------|------|-------------|
| `total_trades` | int | Number of completed trades |
| `win_count` | int | Trades with positive PnL |
| `loss_count` | int | Trades with negative PnL |
| `win_rate` | Decimal | win_count / total_trades |
| `total_pnl` | Decimal | Final PnL in dollars |
| `gross_profit` | Decimal | Sum of winning trades' PnL |
| `gross_loss` | Decimal | Sum of losing trades' PnL (negative) |
| `profit_factor` | Decimal | gross_profit / abs(gross_loss) |
| `sharpe_ratio` | Decimal | Mean/StdDev of percentage returns |
| `max_drawdown` | Decimal | Largest dollar drawdown from peak |
| `max_drawdown_pct` | Decimal | Largest drawdown as % of peak equity |
| `equity_curve` | list[Decimal] | Absolute equity value at each bar |
| `trades` | list[dict] | Per-trade details (side, entry, exit, pnl, reason) |

### SL/TP Simulation Logic
For each bar, the engine checks if the bar's high/low would have triggered SL or TP:
- **Long positions**: SL triggers if `low <= stop_loss`, TP triggers if `high >= take_profit`
- **Short positions**: SL triggers if `high >= stop_loss`, TP triggers if `low <= take_profit`

SL is checked before TP (conservative: assume the worst case hits first).

### Exit Reasons in Trade Records
- `"stop_loss"` — stop-loss price was hit
- `"take_profit"` — take-profit price was hit
- `"end_of_data"` — position still open at end of backtest, forced close at last price
- `"sell"` / `"buy"` — strategy signal closed the position (for signal-driven exits)

### Limitations (Known)
- No slippage modeling (fills at bar close or SL/TP price)
- No transaction fees (set Bybit taker fee to 0.055% for realism)
- Sharpe ratio uses population std dev (should use sample std dev for small N)
- Open positions at end are force-closed at last price

### How to Run Backtests from CLI
Currently backtesting is available programmatically only. To run from CLI:
```bash
conda activate tradehunt-ai
cd agents
python -c "
from decimal import Decimal
import pandas as pd
from agents.src.backtesting.engine import BacktestEngine
from agents.src.strategies.momentum import MomentumStrategy
from agents.src.personas.aggressive import AggressivePersona

# Load your OHLCV data into df
# df = pd.read_csv('your_data.csv')

engine = BacktestEngine(Decimal('10000'))
result = engine.run(df, MomentumStrategy(), 'BTCUSDT', AggressivePersona())
print(f'Trades: {result.total_trades}')
print(f'Win rate: {result.win_rate}')
print(f'Sharpe: {result.sharpe_ratio}')
print(f'Max DD: {result.max_drawdown_pct}')
print(f'Profit factor: {result.profit_factor}')
"
```