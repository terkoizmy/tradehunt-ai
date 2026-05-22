# Quant Personas

## Overview
Personas define the trading personality of each agent. Each persona has a risk profile, system prompt for the LLM, and configurable parameters that feed into the risk manager and strategy selection.

## Architecture
```
PersonaConfig (dataclass)
├── name: str
├── risk_profile: str              # "aggressive" | "moderate" | "conservative"
├── description: str
├── max_drawdown: Decimal          # Max acceptable portfolio drawdown (e.g., 0.25 = 25%)
├── preferred_timeframes: list[str] # e.g., ["5", "15", "60"]
├── max_leverage: Decimal          # Maximum leverage multiplier (1 = no leverage)
├── position_size_pct: Decimal     # % of capital per trade (e.g., 0.15 = 15%)
├── stop_loss_pct: Decimal         # Stop-loss % from entry price
├── take_profit_pct: Decimal       # Take-profit % from entry price
└── confidence_threshold: Decimal   # Minimum LLM confidence to execute a trade

BasePersona (ABC)
├── config: PersonaConfig
├── system_prompt: str             # Injected into LLM as system message
├── voice: str                    # Short tagline for arena display
├── get_position_size(capital, signal_strength) → Decimal
└── format_market_context(market_data_str, signal_str) → str
```

## Built-in Personas

### Aggressive Momentum Hunter
| Parameter | Value |
|-----------|-------|
| risk_profile | aggressive |
| max_drawdown | 25% |
| max_leverage | 5x |
| position_size_pct | 15% |
| stop_loss_pct | 4% |
| take_profit_pct | 12% |
| confidence_threshold | 0.55 |
| voice | "Alpha-seeking missile. Volatility is opportunity." |

### Conservative Value Seeker
| Parameter | Value |
|-----------|-------|
| risk_profile | conservative |
| max_drawdown | 10% |
| max_leverage | 1x (no leverage) |
| position_size_pct | 5% |
| stop_loss_pct | 1.5% |
| take_profit_pct | 4% |
| confidence_threshold | 0.75 |
| voice | "Patient value hunter. Discipline over dopamine." |

### Sentiment Oracle
| Parameter | Value |
|-----------|-------|
| risk_profile | moderate |
| max_drawdown | 15% |
| max_leverage | 2x |
| position_size_pct | 10% |
| stop_loss_pct | 2.5% |
| take_profit_pct | 6% |
| confidence_threshold | 0.65 |
| voice | "Narrative navigator. Reading the crowd's mind." |

### Arbitrage Hunter
| Parameter | Value |
|-----------|-------|
| risk_profile | moderate |
| max_drawdown | 5% |
| max_leverage | 1x (no leverage) |
| position_size_pct | 20% |
| stop_loss_pct | 0.5% |
| take_profit_pct | 1.5% |
| confidence_threshold | 0.80 |
| voice | "Spread sniper. Inefficiency is my alpha." |

## How Personas Feed Into the Agent Loop

1. **Strategy selection** — The `STRATEGIES` dict in `main.py` maps each persona to its default strategy.
2. **LLM prompt** — `persona.system_prompt` is sent as the system message to Ollama, giving the LLM its trading personality.
3. **Confidence threshold** — `DecisionEngine.decide_with_threshold()` rejects trades below `persona.config.confidence_threshold`.
4. **Risk management** — `RiskManager` reads SL/TP percentages, position sizing, and leverage from `persona.config` instead of hardcoded defaults.
5. **Position sizing** — `BasePersona.get_position_size()` computes `capital * position_size_pct * signal_strength * max_leverage`.

## How to Add a New Persona

1. Create `agents/src/personas/your_persona.py`:
```python
from decimal import Decimal
from agents.src.personas.base import BasePersona, PersonaConfig

class YourPersona(BasePersona):
    def __init__(self) -> None:
        super().__init__(PersonaConfig(
            name="Your Persona Name",
            risk_profile="moderate",
            description="Short description.",
            max_drawdown=Decimal("0.15"),
            preferred_timeframes=["15", "60"],
            max_leverage=Decimal("2"),
            position_size_pct=Decimal("0.10"),
            stop_loss_pct=Decimal("0.02"),
            take_profit_pct=Decimal("0.05"),
            confidence_threshold=Decimal("0.65"),
        ))

    @property
    def system_prompt(self) -> str:
        return "You are a... (trading personality description)"

    @property
    def voice(self) -> str:
        return "Short tagline."
```

2. Register in `agents/src/personas/__init__.py`:
```python
from agents.src.personas.your_persona import YourPersona
__all__ = [..., "YourPersona"]
```

3. Add to `PERSONAS` and `STRATEGIES` dicts in `agents/src/main.py`.

4. Add tests in `agents/tests/test_personas.py`.