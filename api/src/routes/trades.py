"""Trade history and leaderboard routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.database import get_db
from api.src.db.models import ArenaScore, Trade

router = APIRouter(tags=["trades", "leaderboard"])


@router.get("/api/trades")
async def list_trades(
    agent_id: uuid.UUID | None = None,
    symbol: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(Trade).order_by(Trade.created_at.desc())
    if agent_id:
        stmt = stmt.where(Trade.agent_id == agent_id)
    if symbol:
        stmt = stmt.where(Trade.symbol == symbol)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    trades = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "agent_id": str(t.agent_id),
            "symbol": t.symbol,
            "side": t.side,
            "price": float(t.price),
            "quantity": float(t.quantity),
            "pnl": float(t.pnl) if t.pnl else None,
            "confidence": float(t.confidence) if t.confidence else None,
            "reasoning": t.reasoning,
            "tx_hash": t.tx_hash,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trades
    ]


@router.get("/api/leaderboard/{session_id}")
async def get_leaderboard(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(ArenaScore)
        .where(ArenaScore.session_id == session_id)
        .order_by(ArenaScore.total_pnl.desc())
    )
    scores = result.scalars().all()

    ranked = []
    for i, s in enumerate(scores):
        ranked.append({
            "rank": i + 1,
            "agent_id": str(s.agent_id),
            "total_pnl": float(s.total_pnl),
            "sharpe_ratio": float(s.sharpe_ratio) if s.sharpe_ratio else None,
            "win_rate": float(s.win_rate) if s.win_rate else None,
            "trade_count": s.trade_count,
        })
    return ranked
