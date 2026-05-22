# Trading Strategies

## Overview
Each strategy takes OHLCV data as a pandas DataFrame and returns a `Signal` indicating whether to buy, sell, or hold. Strategies are stateless — they analyze the current market state and return a signal without memory of past calls.

## Signal Format
```python
@dataclass
class Signal:
    action: str           # "buy" | "sell" | "hold"
    symbol: str           # e.g., "BTCUSDT"
    confidence: Decimal   # 0.0 to 1.0
    price: Decimal        # current price at signal time
    reasoning: str        # human-readable explanation
    metadata: dict        # optional: indicator values, crossover flags, etc.
```

Defined in `agents/src/data/market_data.py`. All strategies import from this shared definition.

## Shared Indicators
Common indicator calculations live in `agents/src/strategies/indicators.py`:

- **`calc_rsi(prices, period=14)`** — Wilder's smoothing RSI. Used by both Momentum and MeanReversion strategies.

## Built-in Strategies

### MomentumStrategy
**File:** `agents/src/strategies/momentum.py`
**Best for:** Trending markets with clear directional moves.

| Indicator | Default | Purpose |
|-----------|---------|---------|
| RSI | period=14 | Momentum confirmation |
| EMA fast | span=12 | Short-term trend |
| EMA slow | span=26 | Long-term trend |
| MACD signal | span=9 | MACD signal line |

**Signal priority (highest to lowest confidence):**

1. **EMA + MACD combined crossover** (0.90) — Both fast EMA crossing slow EMA AND MACD crossing signal line in the same direction.
2. **EMA crossover alone** (0.75) — Fast EMA crosses slow EMA.
3. **MACD crossover alone** (0.70) — MACD line crosses signal line.
4. **RSI overbought/oversold** (0.55) — RSI above 70 (sell) or below 30 (buy).

**Parameters:**
```python
MomentumStrategy(
    rsi_period=14,
    ema_fast=12,
    ema_slow=26,
    macd_signal=9,
    rsi_overbought=70,
    rsi_oversold=30,
)
```

### MeanReversionStrategy
**File:** `agents/src/strategies/mean_reversion.py`
**Best for:** Ranging markets with price extremes.

| Indicator | Default | Purpose |
|-----------|---------|---------|
| Bollinger Bands | period=20, std=2.0 | Price extremes detection |
| RSI | period=14 | Oversold/overbought confirmation |

**Signal logic:**

1. **BB + RSI dual confirmation** (0.70–0.90) — Price below lower BB AND RSI oversold → buy. Price above upper BB AND RSI overbought → sell. Confidence scales with RSI extremity.
2. **BB touch without RSI** (0.55) — Price breaks band but RSI not at extreme. Weaker signal.

**Confidence scaling:** Uses `_confidence_from_rsi()` to map RSI extremity to confidence:
- Oversold RSI near 0 → higher buy confidence (up to 0.90)
- Overbought RSI near 100 → higher sell confidence (up to 0.90)

**Parameters:**
```python
MeanReversionStrategy(
    bb_period=20,
    bb_std=2.0,
    rsi_period=14,
    rsi_oversold=30,
    rsi_overbought=70,
)
```

### MacroSwingStrategy
**File:** `agents/src/strategies/macro_swing.py`
**Best for:** Higher timeframe trend alignment. Requires 200+ bars of data.

Uses weighted SMA alignment across 3 timeframes:
- Short (SMA 20, weight 0.3)
- Medium (SMA 50, weight 0.3)
- Long (SMA 200, weight 0.4)

Price above SMA → +weight, below → -weight. Total score > 0.3 → buy, < -0.3 → sell.

### GridTradingStrategy
**File:** `agents/src/strategies/grid_trading.py`
**Status:** Stub — always returns hold. Grid logic is handled by the execution layer.

## How to Add a New Strategy

1. Create `agents/src/strategies/your_strategy.py`:
```python
from decimal import Decimal
import pandas as pd
from agents.src.data.market_data import Signal

class YourStrategy:
    def __init__(self, param1: int = 14) -> None:
        self.param1 = param1

    def analyze(self, df: pd.DataFrame, symbol: str) -> Signal:
        if len(df) < self.param1:
            return Signal("hold", symbol, Decimal("0"), Decimal("0"), "Insufficient data")

        # Your indicator logic here
        # ...
        return Signal("buy", symbol, Decimal("0.75"), price, "Your reasoning")
```

2. Import and register in `agents/src/strategies/__init__.py`.

3. Add to the `STRATEGIES` dict in `agents/src/main.py` to map a persona to your strategy.

4. Add tests in `agents/tests/test_strategies.py`.

## Parameter Tuning

Run backtests to calibrate parameters:
```python
from agents.src.backtesting.engine import BacktestEngine
from agents.src.strategies.momentum import MomentumStrategy
from agents.src.personas.aggressive import AggressivePersona

engine = BacktestEngine(initial_capital=Decimal("10000"))
strategy = MomentumStrategy(rsi_period=14, ema_fast=12, ema_slow=26)
persona = AggressivePersona()
result = engine.run(df, strategy, "BTCUSDT", persona=persona)

print(f"Sharpe: {result.sharpe_ratio}")
print(f"Max DD: {result.max_drawdown_pct}")
print(f"Win rate: {result.win_rate}")
print(f"Profit factor: {result.profit_factor}")
```

Adjust strategy parameters and compare backtest results across personas.