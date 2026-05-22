"""Backtesting engine for persona/strategy validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pandas as pd

from agents.src.personas.base import BasePersona


@dataclass
class BacktestResult:
    total_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    gross_loss: Decimal = Decimal("0")
    profit_factor: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")
    equity_curve: list[Decimal] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _Position:
    side: str  # "long" | "short"
    qty: Decimal
    entry_price: Decimal
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    entry_bar: int = 0


class BacktestEngine:
    """Replays historical kline data through a strategy to measure performance.

    Simulates stop-loss and take-profit using high/low prices per bar.
    Supports both long and short positions.
    """

    def __init__(self, initial_capital: Decimal = Decimal("10000")) -> None:
        self.initial_capital = initial_capital

    def run(
        self,
        df: pd.DataFrame,
        strategy,
        symbol: str,
        persona: BasePersona | None = None,
    ) -> BacktestResult:
        result = BacktestResult()
        cash = self.initial_capital
        position: _Position | None = None
        peak_equity = self.initial_capital
        equity_curve: list[Decimal] = []

        required = getattr(strategy, "ema_slow", 26) + getattr(strategy, "rsi_period", 14)
        start = max(1, required)

        for i in range(len(df)):
            bar = df.iloc[i]
            high = Decimal(str(bar["high"]))
            low = Decimal(str(bar["low"]))
            close = Decimal(str(bar["close"]))

            # 1. Check SL/TP for existing position using this bar's range
            exit_price, exit_reason = self._check_sl_tp(position, high, low)
            if exit_price is not None:
                cash, trade_pnl = self._close_position(cash, position, exit_price)
                self._record_trade(result, position, exit_price, trade_pnl, exit_reason, symbol)
                position = None

            # 2. Generate signal if we have enough data and flat
            if i >= start and position is None:
                window = df.iloc[: i + 1]
                signal = strategy.analyze(window, symbol)

                if signal.action == "buy":
                    sl = tp = None
                    if persona is not None:
                        sl = close * (Decimal("1") - persona.config.stop_loss_pct)
                        tp = close * (Decimal("1") + persona.config.take_profit_pct)
                    qty = cash / close
                    position = _Position(
                        side="long",
                        qty=qty,
                        entry_price=close,
                        stop_loss=sl,
                        take_profit=tp,
                        entry_bar=i,
                    )
                    cash = Decimal("0")

                elif signal.action == "sell":
                    sl = tp = None
                    if persona is not None:
                        sl = close * (Decimal("1") + persona.config.stop_loss_pct)
                        tp = close * (Decimal("1") - persona.config.take_profit_pct)
                    qty = cash / close
                    position = _Position(
                        side="short",
                        qty=qty,
                        entry_price=close,
                        stop_loss=sl,
                        take_profit=tp,
                        entry_bar=i,
                    )
                    cash = Decimal("0")

            # 3. Record absolute equity
            equity = cash if position is None else self._position_value(position, close)
            equity_curve.append(equity)
            peak_equity = max(peak_equity, equity)

            dd = (peak_equity - equity) / peak_equity if peak_equity > 0 else Decimal("0")
            if dd > result.max_drawdown_pct:
                result.max_drawdown_pct = dd
                result.max_drawdown = peak_equity - equity

        # Close any open position at last close
        if position is not None:
            last_close = Decimal(str(df.iloc[-1]["close"]))
            cash, trade_pnl = self._close_position(cash, position, last_close)
            self._record_trade(result, position, last_close, trade_pnl, "end_of_data", symbol)
            position = None
            equity_curve[-1] = cash

        result.equity_curve = equity_curve
        result.total_pnl = cash - self.initial_capital

        if result.total_trades > 0:
            result.win_rate = Decimal(str(result.win_count / result.total_trades))

        if result.gross_loss != 0:
            result.profit_factor = result.gross_profit / abs(result.gross_loss)

        # Sharpe ratio uses percentage returns, not dollar PnL
        if len(equity_curve) > 1:
            pct_returns = []
            for j in range(1, len(equity_curve)):
                prev = equity_curve[j - 1]
                if prev > 0:
                    pct_returns.append(float((equity_curve[j] - prev) / prev))
            if pct_returns:
                mean_ret = sum(pct_returns) / len(pct_returns)
                var_ret = sum((r - mean_ret) ** 2 for r in pct_returns) / len(pct_returns)
                std_ret = var_ret ** 0.5
                if std_ret > 0:
                    # Annualize assuming ~252 trading days with daily bars;
                    # here bars are arbitrary so we keep it unannualized
                    result.sharpe_ratio = Decimal(str(mean_ret / std_ret))

        return result

    @staticmethod
    def _position_value(position: _Position, price: Decimal) -> Decimal:
        """Current market value of an open position."""
        if position.side == "long":
            return position.qty * price
        # short: unrealized PnL subtracted from notional
        entry_value = position.qty * position.entry_price
        exit_value = position.qty * price
        pnl = entry_value - exit_value
        return entry_value + pnl

    @staticmethod
    def _check_sl_tp(
        position: _Position | None,
        high: Decimal,
        low: Decimal,
    ) -> tuple[Decimal | None, str | None]:
        """Check if SL or TP was hit within this bar's range."""
        if position is None:
            return None, None

        if position.side == "long":
            if position.stop_loss is not None and low <= position.stop_loss:
                return position.stop_loss, "stop_loss"
            if position.take_profit is not None and high >= position.take_profit:
                return position.take_profit, "take_profit"

        elif position.side == "short":
            if position.stop_loss is not None and high >= position.stop_loss:
                return position.stop_loss, "stop_loss"
            if position.take_profit is not None and low <= position.take_profit:
                return position.take_profit, "take_profit"

        return None, None

    @staticmethod
    def _close_position(
        cash: Decimal,
        position: _Position,
        exit_price: Decimal,
    ) -> tuple[Decimal, Decimal]:
        if position.side == "long":
            cash = position.qty * exit_price
            trade_pnl = cash - (position.qty * position.entry_price)
        else:  # short
            entry_value = position.qty * position.entry_price
            exit_value = position.qty * exit_price
            trade_pnl = entry_value - exit_value
            cash = entry_value + trade_pnl
        return cash, trade_pnl

    @staticmethod
    def _record_trade(
        result: BacktestResult,
        position: _Position,
        exit_price: Decimal,
        trade_pnl: Decimal,
        reason: str,
        symbol: str,
    ) -> None:
        result.total_trades += 1
        if trade_pnl > 0:
            result.win_count += 1
            result.gross_profit += trade_pnl
        else:
            result.loss_count += 1
            result.gross_loss += trade_pnl

        result.trades.append({
            "symbol": symbol,
            "side": position.side,
            "entry": float(position.entry_price),
            "exit": float(exit_price),
            "pnl": float(trade_pnl),
            "reason": reason,
        })
