"""Agent entrypoint — CLI for running a quant persona agent."""

from __future__ import annotations

import argparse
import asyncio
import os
from decimal import Decimal

import pandas as pd

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

PERSONAS = {
    "aggressive": AggressivePersona,
    "conservative": ConservativePersona,
    "sentiment": SentimentPersona,
    "arbitrageur": ArbitrageurPersona,
}


def get_persona(name: str) -> BasePersona:
    persona_cls = PERSONAS.get(name)
    if persona_cls is None:
        raise ValueError(f"Unknown persona: {name}. Options: {list(PERSONAS.keys())}")
    return persona_cls()


async def run_agent(persona_name: str, symbol: str, capital: Decimal) -> None:
    """Main agent loop: observe → decide → act → log."""
    persona = get_persona(persona_name)
    client = BybitClient()
    mcp = BybitMCP()
    engine = DecisionEngine()
    risk = RiskManager(capital)
    momentum = MomentumStrategy()
    mean_rev = MeanReversionStrategy()

    print(f"[{persona.config.name}] Starting on {symbol} with ${capital}")
    print(f"  Voice: {persona.voice}")

    while True:
        try:
            # Observe: gather market data
            snapshot = client.get_market_snapshot(symbol)
            klines_raw = client.get_klines(symbol, interval="15", limit=100)

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

            # Decide: strategy → signal → LLM
            if persona_name == "conservative":
                signal = mean_rev.analyze(df, symbol)
            else:
                signal = momentum.analyze(df, symbol)

            decision = await engine.decide(
                persona.system_prompt,
                market_data.to_context_string(),
                f"Action: {signal.action}, Confidence: {signal.confidence}, "
                f"Reasoning: {signal.reasoning}",
            )

            # Risk check
            risk_decision = risk.evaluate(
                action=decision.get("action", "hold"),
                price=snapshot.last_price,
                confidence=Decimal(str(decision.get("confidence", 0))),
                side=decision.get("action", "buy"),
            )

            # Act
            if risk_decision.allowed and decision.get("action") in ("buy", "sell"):
                result = client.place_order(
                    symbol=symbol,
                    side=decision["action"],
                    qty=str(risk_decision.position_size / snapshot.last_price),
                    stop_loss=str(risk_decision.stop_loss_price) if risk_decision.stop_loss_price else None,
                    take_profit=str(risk_decision.take_profit_price) if risk_decision.take_profit_price else None,
                )
                status = "EXECUTED" if result.success else f"FAILED: {result.error}"
            else:
                status = f"HOLD — {risk_decision.reason}"

            print(
                f"[{persona.config.name}] {decision.get('action', 'hold').upper()} "
                f"| Confidence: {decision.get('confidence', 0):.2f} "
                f"| {status}"
            )
            print(f"  Reasoning: {decision.get('reasoning', 'N/A')}")

            await asyncio.sleep(60)  # 1-minute loop

        except Exception as e:
            print(f"[{persona.config.name}] Error: {e}")
            await asyncio.sleep(60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tradehunt AI Agent")
    parser.add_argument(
        "--persona", type=str, default="conservative",
        choices=list(PERSONAS.keys()),
        help="Quant persona to run",
    )
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--capital", type=float, default=10000)
    args = parser.parse_args()

    asyncio.run(run_agent(args.persona, args.symbol, Decimal(str(args.capital))))


if __name__ == "__main__":
    main()
