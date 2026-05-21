"""Arena session routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.database import get_db
from api.src.db.models import ArenaScore, ArenaSession

router = APIRouter(prefix="/api/arena", tags=["arena"])


class SessionCreate(BaseModel):
    name: str
    duration_seconds: int = 3600


class SessionResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    start_time: str | None
    end_time: str | None
    onchain_id: int | None


class ScoreResponse(BaseModel):
    agent_id: uuid.UUID
    total_pnl: float
    sharpe_ratio: float | None
    win_rate: float | None
    trade_count: int
    rank: int | None


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
) -> list[SessionResponse]:
    result = await db.execute(select(ArenaSession).order_by(ArenaSession.created_at.desc()))
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=s.id,
            name=s.name,
            status=s.status,
            start_time=s.start_time.isoformat() if s.start_time else None,
            end_time=s.end_time.isoformat() if s.end_time else None,
            onchain_id=s.onchain_id,
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    now = datetime.now(timezone.utc)
    session = ArenaSession(
        id=uuid.uuid4(),
        name=body.name,
        status="active",
        start_time=now,
        end_time=datetime.fromtimestamp(
            now.timestamp() + body.duration_seconds, tz=timezone.utc
        ),
    )
    db.add(session)
    await db.flush()
    return SessionResponse(
        id=session.id,
        name=session.name,
        status=session.status,
        start_time=session.start_time.isoformat() if session.start_time else None,
        end_time=session.end_time.isoformat() if session.end_time else None,
        onchain_id=session.onchain_id,
    )


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ArenaSession).where(ArenaSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    scores_result = await db.execute(
        select(ArenaScore).where(ArenaScore.session_id == session_id).order_by(ArenaScore.rank)
    )
    scores = scores_result.scalars().all()

    return {
        "id": str(session.id),
        "name": session.name,
        "status": session.status,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "scores": [
            {
                "agent_id": str(s.agent_id),
                "total_pnl": float(s.total_pnl),
                "sharpe_ratio": float(s.sharpe_ratio) if s.sharpe_ratio else None,
                "win_rate": float(s.win_rate) if s.win_rate else None,
                "trade_count": s.trade_count,
                "rank": s.rank,
            }
            for s in scores
        ],
    }
