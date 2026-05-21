"""Backtesting engine for persona/strategy validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pandas as pd


@dataclass
class BacktestResult:
    total_trades: int = 0
    win_count: int = 0
    win_rate: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    equity_curve: list[Decimal] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)


class BacktestEngine:
    """Replays historical kline data through a strategy to measure performance."""

    def __init__(self, initial_capital: Decimal = Decimal("10000")) -> None:
        self.initial_capital = initial_capital

    def run(
        self,
        df: pd.DataFrame,
        strategy,
        symbol: str,
    ) -> BacktestResult:
        result = BacktestResult()
        capital = self.initial_capital
        position: Decimal | None = None
        entry_price: Decimal | None = None
        peak_capital = capital
        pnl_series: list[Decimal] = []

        for i in range(200, len(df)):
            window = df.iloc[: i + 1]
            signal = strategy.analyze(window, symbol)
            current_price = Decimal(str(window.iloc[-1]["close"]))

            if signal.action == "buy" and position is None:
                entry_price = current_price
                position = capital / current_price
                capital = Decimal("0")

            elif signal.action == "sell" and position is not None:
                capital = position * current_price
                pnl = capital - self.initial_capital
                position = None
                entry_price = None

                result.total_trades += 1
                if pnl > 0:
                    result.win_count += 1
                result.total_pnl += pnl
                result.trades.append({
                    "symbol": symbol,
                    "pnl": float(pnl),
                    "entry": float(entry_price or 0),
                    "exit": float(current_price),
                })

            current_total = capital if position is None else position * current_price
            peak_capital = max(peak_capital, current_total)
            drawdown = (peak_capital - current_total) / peak_capital if peak_capital > 0 else Decimal("0")
            result.max_drawdown = max(result.max_drawdown, drawdown)
            pnl_series.append(current_total - self.initial_capital)

        result.equity_curve = pnl_series
        if result.total_trades > 0:
            result.win_rate = Decimal(str(result.win_count / result.total_trades))

        if len(pnl_series) > 1 and position is not None:
            # Close position at last price
            last_price = Decimal(str(df.iloc[-1]["close"]))
            capital = position * last_price

        result.total_pnl = capital - self.initial_capital

        if pnl_series and len(pnl_series) > 1:
            returns = [
                float(pnl_series[i] - pnl_series[i - 1])
                for i in range(1, len(pnl_series))
            ]
            if returns:
                mean_ret = sum(returns) / len(returns)
                std_ret = (
                    (sum((r - mean_ret) ** 2 for r in returns) / len(returns)) ** 0.5
                )
                if std_ret > 0:
                    result.sharpe_ratio = Decimal(str(mean_ret / std_ret))

        return result
