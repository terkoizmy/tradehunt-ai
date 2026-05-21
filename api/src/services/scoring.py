"""PnL and performance scoring service."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.models import ArenaScore, Trade


async def calculate_scores(
    session_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """Calculate per-agent scores for an arena session from trade history."""
    # Get all trades, grouped by agent
    result = await db.execute(
        select(
            Trade.agent_id,
            func.count(Trade.id).label("trade_count"),
            func.sum(Trade.pnl).label("total_pnl"),
            func.avg(Trade.pnl).label("avg_pnl"),
            func.stddev(Trade.pnl).label("std_pnl"),
        )
        .where(Trade.pnl.isnot(None))
        .group_by(Trade.agent_id)
    )
    rows = result.all()

    scores_data = []
    for row in rows:
        trade_count = row.trade_count
        total_pnl = row.total_pnl or Decimal("0")
        avg_pnl = row.avg_pnl or Decimal("0")
        std_pnl = row.std_pnl or Decimal("0")

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
    return scores_data
