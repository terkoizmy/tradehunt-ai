"""PnL and performance scoring service."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.models import ArenaScore, Trade
from api.src.ws.manager import manager


async def calculate_scores(
    session_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """Calculate per-agent scores for an arena session from trade history.

    Updates arena_scores table and broadcasts rank changes via WebSocket.
    """
    # Get all trades, grouped by agent
    # Note: stddev is not available in SQLite; we compute manually if needed
    result = await db.execute(
        select(
            Trade.agent_id,
            func.count(Trade.id).label("trade_count"),
            func.sum(Trade.pnl).label("total_pnl"),
            func.avg(Trade.pnl).label("avg_pnl"),
        )
        .where(Trade.pnl.isnot(None))
        .group_by(Trade.agent_id)
    )
    rows = result.all()

    scores_data = []
    for row in rows:
        trade_count = row.trade_count
        total_pnl = Decimal(str(row.total_pnl)) if row.total_pnl is not None else Decimal("0")
        avg_pnl = Decimal(str(row.avg_pnl)) if row.avg_pnl is not None else Decimal("0")

        # Compute stddev manually (SQLite compatible)
        trades_result = await db.execute(
            select(Trade.pnl).where(Trade.agent_id == row.agent_id, Trade.pnl.isnot(None))
        )
        pnls = [t[0] for t in trades_result.all()]
        if len(pnls) > 1:
            mean = sum(pnls) / len(pnls)
            variance = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
            std_pnl = variance.sqrt()
        else:
            std_pnl = Decimal("0")

        # Win rate: trades with positive PnL
        win_result = await db.execute(
            select(func.count(Trade.id))
            .where(Trade.agent_id == row.agent_id, Trade.pnl > 0)
        )
        win_count = win_result.scalar() or 0
        win_rate = Decimal(str(win_count / trade_count)) if trade_count > 0 else Decimal("0")

        # Sharpe ratio (simplified)
        sharpe = (avg_pnl / std_pnl) if std_pnl > 0 else Decimal("0")

        scores_data.append({
            "agent_id": row.agent_id,
            "trade_count": trade_count,
            "total_pnl": total_pnl,
            "sharpe_ratio": sharpe,
            "win_rate": win_rate,
        })

    # Rank by total PnL
    scores_data.sort(key=lambda x: x["total_pnl"], reverse=True)
    for i, s in enumerate(scores_data):
        s["rank"] = i + 1

    # Upsert scores
    for s in scores_data:
        existing = await db.execute(
            select(ArenaScore).where(
                ArenaScore.session_id == session_id,
                ArenaScore.agent_id == s["agent_id"],
            )
        )
        score = existing.scalar_one_or_none()
        if score is None:
            score = ArenaScore(
                id=uuid.uuid4(),
                session_id=session_id,
                agent_id=s["agent_id"],
            )
            db.add(score)
        score.total_pnl = s["total_pnl"]
        score.sharpe_ratio = s["sharpe_ratio"]
        score.win_rate = s["win_rate"]
        score.trade_count = s["trade_count"]
        score.rank = s["rank"]

    await db.flush()

    # Broadcast score update to arena WebSocket channel
    await manager.broadcast(
        "arena",
        {
            "type": "score_update",
            "session_id": str(session_id),
            "scores": [
                {
                    "rank": s["rank"],
                    "agent_id": str(s["agent_id"]),
                    "total_pnl": float(s["total_pnl"]),
                    "sharpe_ratio": float(s["sharpe_ratio"]),
                    "win_rate": float(s["win_rate"]),
                    "trade_count": s["trade_count"],
                }
                for s in scores_data
            ],
        },
    )

    return scores_data
