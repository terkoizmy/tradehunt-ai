"""PnL and performance scoring service."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.models import ArenaScore, ArenaSession, Trade
from api.src.ws.manager import manager


async def calculate_scores(
    session_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """Calculate per-agent scores for an arena session from trade history.

    Updates arena_scores table and broadcasts rank changes via WebSocket.
    Only includes trades whose execution time falls within the session window.
    """
    # Resolve session time bounds
    session_result = await db.execute(
        select(ArenaSession).where(ArenaSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    start_time = session.start_time
    end_time = session.end_time or datetime.now(timezone.utc)

    # Normalize bounds to naive UTC for consistent cross-DB comparison
    def _naive_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    start_naive = _naive_utc(start_time)
    end_naive = _naive_utc(end_time)

    # Fetch all trades with pnl for this session in a single query (no time filter in SQL)
    trades_result = await db.execute(
        select(Trade.agent_id, Trade.pnl, Trade.executed_at, Trade.created_at)
        .where(Trade.pnl.isnot(None))
    )

    # Group and filter in Python to avoid SQLite/PostgreSQL datetime comparison quirks
    agent_pnls: dict[uuid.UUID, list[Decimal]] = defaultdict(list)
    for aid, pnl, executed_at, created_at in trades_result.all():
        trade_time = executed_at or created_at
        if trade_time is None:
            continue
        # Normalize trade time to naive UTC
        if trade_time.tzinfo:
            trade_time = trade_time.astimezone(timezone.utc).replace(tzinfo=None)
        if start_naive and trade_time < start_naive:
            continue
        if end_naive and trade_time > end_naive:
            continue
        agent_pnls[aid].append(Decimal(str(pnl)))

    scores_data = []
    for aid, pnls in agent_pnls.items():
        trade_count = len(pnls)
        total_pnl = sum(pnls, Decimal("0"))
        avg_pnl = total_pnl / trade_count if trade_count > 0 else Decimal("0")
        win_count = sum(1 for p in pnls if p > 0)

        # Compute stddev manually (SQLite compatible)
        if len(pnls) > 1:
            mean = sum(pnls) / len(pnls)
            variance = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
            std_pnl = variance.sqrt()
        else:
            std_pnl = Decimal("0")

        win_rate = Decimal(str(win_count / trade_count)) if trade_count > 0 else Decimal("0")

        # Sharpe ratio (simplified)
        sharpe = (avg_pnl / std_pnl) if std_pnl > 0 else Decimal("0")

        scores_data.append({
            "agent_id": aid,
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
