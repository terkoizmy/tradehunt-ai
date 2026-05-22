"""Agent entrypoint — CLI for running a quant persona agent."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd

from agents.src.api.client import APIClient
from agents.src.data.market_data import MarketData
from agents.src.execution.bybit_client import BybitClient
from agents.src.execution.bybit_mcp import BybitMCP
from agents.src.execution.risk_manager import RiskConfig, RiskManager
from agents.src.llm.decision_engine import DecisionEngine
from agents.src.personas.aggressive import AggressivePersona
from agents.src.personas.arbitrageur import ArbitrageurPersona
from agents.src.personas.base import BasePersona
from agents.src.personas.conservative import ConservativePersona
from agents.src.personas.sentiment import SentimentPersona
from agents.src.strategies.mean_reversion import MeanReversionStrategy
from agents.src.strategies.momentum import MomentumStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tradehunt")

PERSONAS: dict[str, type[BasePersona]] = {
    "aggressive": AggressivePersona,
    "conservative": ConservativePersona,
    "sentiment": SentimentPersona,
    "arbitrageur": ArbitrageurPersona,
}

STRATEGIES: dict[str, type] = {
    "aggressive": MomentumStrategy,
    "conservative": MeanReversionStrategy,
    "sentiment": MomentumStrategy,
    "arbitrageur": MeanReversionStrategy,
}

# Track last seen closed-PnL IDs to avoid double-counting
_closed_pnl_ids: set[str] = set()


def get_persona(name: str) -> BasePersona:
    persona_cls = PERSONAS.get(name)
    if persona_cls is None:
        raise ValueError(f"Unknown persona: {name}. Options: {list(PERSONAS.keys())}")
    return persona_cls()


def get_strategy(persona_name: str):
    strat_cls = STRATEGIES.get(persona_name, MomentumStrategy)
    return strat_cls()


async def run_agent(
    persona_name: str,
    symbol: str,
    capital: Decimal,
    interval: str = "15",
    loop_seconds: int = 60,
    api_url: str | None = None,
) -> None:
    """Main agent loop: observe → decide → act → log."""
    persona = get_persona(persona_name)
    strategy = get_strategy(persona_name)
    client = BybitClient()
    mcp = BybitMCP()
    engine = DecisionEngine()
    risk = RiskManager(persona=persona, capital=capital, config=RiskConfig())
    api = APIClient(base_url=api_url) if api_url else None

    # Register with backend if API URL provided
    if api:
        try:
            await api.register(
                name=persona.config.name,
                persona=persona_name,
                wallet_address="0x0000000000000000000000000000000000000000",  # TODO: real wallet
                capital=capital,
                symbol=symbol,
                persona_config=persona.config.__dict__,
            )
            logger.info("Registered agent with backend: %s", api.agent_id)
        except Exception as e:
            logger.warning("Failed to register with backend: %s", e)
            api = None

    # Sync open positions on startup
    try:
        positions = client.get_positions(symbol=symbol)
        open_count = len([p for p in positions if float(p.get("size", 0)) != 0])
        risk.sync_open_positions(open_count)
        logger.info("Synced %d open positions from Bybit", open_count)
    except Exception as e:
        logger.warning("Could not sync positions: %s", e)

    logger.info(
        "[%s] Starting on %s with $%s | interval=%s | loop=%ss",
        persona.config.name,
        symbol,
        capital,
        interval,
        loop_seconds,
    )
    logger.info("  Voice: %s", persona.voice)

    shutdown_event = asyncio.Event()

    def _signal_handler(_sig: int, _frame) -> None:
        logger.info("Shutdown signal received, exiting gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    while not shutdown_event.is_set():
        try:
            # Observe
            snapshot = client.get_market_snapshot(symbol)
            klines_raw = client.get_klines(symbol, interval=interval, limit=100)

            df = pd.DataFrame(
                klines_raw,
                columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"],
            )
            df = df.iloc[::-1]  # reverse to chronological
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col])

            mcp_ctx = mcp.analyze_market(symbol, klines=klines_raw)

            market_data = MarketData(
                symbol=symbol,
                last_price=snapshot.last_price,
                bid=snapshot.bid,
                ask=snapshot.ask,
                volume_24h=snapshot.volume_24h,
                high_24h=snapshot.high_24h,
                low_24h=snapshot.low_24h,
                klines=klines_raw,
                mcp_context=mcp_ctx,
            )

            # Decide: strategy → signal → LLM (with persona confidence threshold)
            signal = strategy.analyze(df, symbol)
            decision = await engine.decide_with_threshold(
                persona.system_prompt,
                market_data.to_context_string(),
                signal,
                persona.config.confidence_threshold,
            )

            # Risk check
            risk_decision = risk.evaluate(
                action=decision.get("action", "hold"),
                price=snapshot.last_price,
                confidence=Decimal(str(decision.get("confidence", 0))),
                signal_strength=signal.confidence,
            )

            # Report decision to backend
            if api:
                try:
                    await api.report_decision({
                        "action": decision.get("action", "hold"),
                        "symbol": symbol,
                        "confidence": decision.get("confidence", 0),
                        "reasoning": decision.get("reasoning", ""),
                        "signal_action": signal.action,
                        "signal_confidence": signal.confidence,
                        "risk_allowed": risk_decision.allowed,
                        "risk_reason": risk_decision.reason if not risk_decision.allowed else None,
                    })
                except Exception as e:
                    logger.debug("Decision report failed: %s", e)

            # Act
            if risk_decision.allowed and decision.get("action") in ("buy", "sell"):
                qty = risk_decision.position_size / snapshot.last_price
                result = client.place_order(
                    symbol=symbol,
                    side=decision["action"],
                    qty=str(qty),
                    stop_loss=str(risk_decision.stop_loss_price) if risk_decision.stop_loss_price else None,
                    take_profit=str(risk_decision.take_profit_price) if risk_decision.take_profit_price else None,
                )
                if result.success:
                    risk.increment_open()
                    status = f"EXECUTED {result.order_id}"
                    logger.info(
                        "[%s] %s | Confidence: %.2f | %s | Qty: %.6f | SL: %s | TP: %s",
                        persona.config.name,
                        decision.get("action", "hold").upper(),
                        decision.get("confidence", 0),
                        status,
                        float(qty),
                        risk_decision.stop_loss_price,
                        risk_decision.take_profit_price,
                    )

                    # Report trade to backend
                    if api:
                        try:
                            await api.report_trade({
                                "action": decision["action"],
                                "symbol": symbol,
                                "side": decision["action"],
                                "price": float(snapshot.last_price),
                                "quantity": float(qty),
                                "stop_loss": float(risk_decision.stop_loss_price) if risk_decision.stop_loss_price else None,
                                "take_profit": float(risk_decision.take_profit_price) if risk_decision.take_profit_price else None,
                                "confidence": decision.get("confidence", 0),
                                "reasoning": decision.get("reasoning", ""),
                                "order_id": result.order_id,
                                "executed_at": datetime.now(timezone.utc).isoformat(),
                            })
                        except Exception as e:
                            logger.debug("Trade report failed: %s", e)
                else:
                    status = f"FAILED: {result.error}"
                    logger.warning("[%s] Order failed: %s", persona.config.name, status)
            else:
                status = f"HOLD — {risk_decision.reason}"
                logger.info(
                    "[%s] %s | Confidence: %.2f | %s",
                    persona.config.name,
                    decision.get("action", "hold").upper(),
                    decision.get("confidence", 0),
                    status,
                )

            logger.info("  Reasoning: %s", decision.get("reasoning", "N/A"))

            # Sync positions + PnL after every iteration
            _sync_positions_and_pnl(client, risk, symbol)

            # Heartbeat
            if api:
                try:
                    await api.heartbeat()
                except Exception as e:
                    logger.debug("Heartbeat failed: %s", e)

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=loop_seconds)
            except asyncio.TimeoutError:
                pass

        except Exception as e:
            logger.exception("[%s] Error in agent loop: %s", persona.config.name, e)
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=loop_seconds)
            except asyncio.TimeoutError:
                pass

    logger.info("[%s] Agent loop exited.", persona.config.name)

    if api:
        try:
            await api.set_offline()
        except Exception as e:
            logger.warning("Failed to set offline: %s", e)
        finally:
            await api.close()

    client.close()


def _sync_positions_and_pnl(
    client: BybitClient,
    risk: RiskManager,
    symbol: str,
) -> None:
    """Sync open-position count and feed realized PnL into risk manager."""
    try:
        positions = client.get_positions(symbol=symbol)
        open_count = len([p for p in positions if float(p.get("size", 0)) != 0])
        risk.sync_open_positions(open_count)
    except Exception as e:
        logger.warning("Could not sync positions: %s", e)

    try:
        for record in client.get_closed_pnl(symbol=symbol, limit=50):
            order_id = record.get("orderId", "")
            if order_id and order_id not in _closed_pnl_ids:
                _closed_pnl_ids.add(order_id)
                pnl = Decimal(str(record.get("closedPnl", "0")))
                if pnl != 0:
                    risk.update_pnl(pnl)
                    logger.info("Realized PnL recorded: %s", pnl)
    except Exception as e:
        logger.warning("Could not sync closed PnL: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tradehunt AI Agent")
    parser.add_argument(
        "--persona",
        type=str,
        default="conservative",
        choices=list(PERSONAS.keys()),
        help="Quant persona to run",
    )
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--capital", type=float, default=10000)
    parser.add_argument(
        "--interval",
        type=str,
        default="15",
        help="Kline interval in minutes (1, 5, 15, 60, etc.)",
    )
    parser.add_argument(
        "--loop",
        type=int,
        default=60,
        help="Seconds between trading loops",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Backend API URL for reporting (e.g. http://localhost:8000)",
    )
    args = parser.parse_args()

    asyncio.run(
        run_agent(
            args.persona,
            args.symbol,
            Decimal(str(args.capital)),
            interval=args.interval,
            loop_seconds=args.loop,
            api_url=args.api_url,
        )
    )


if __name__ == "__main__":
    main()
