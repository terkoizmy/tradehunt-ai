"""Arena session routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.database import get_db

logger = logging.getLogger("tradehunt.arena")
from api.src.db.models import Agent, ArenaScore, ArenaSession, Trade
from api.src.services.arena_contract_bridge import ArenaContractBridge
from api.src.services.scoring import calculate_scores
from api.src.ws.manager import manager

router = APIRouter(prefix="/api/arena", tags=["arena"])


class SessionCreate(BaseModel):
    name: str
    duration_seconds: int = 3600


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ScoreOnChainRequest(BaseModel):
    session_id: uuid.UUID
    submit_onchain: bool = False


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

    # Optionally create session on-chain (best-effort)
    try:
        bridge = ArenaContractBridge()
        onchain_id = await bridge.create_session(body.name, body.duration_seconds)
        session.onchain_id = onchain_id
        await db.flush()
    except Exception as exc:
        logger.warning("On-chain session creation failed (best-effort): %s", exc)

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


@router.post("/sessions/{session_id}/calculate-scores")
async def calculate_and_submit_scores(
    session_id: uuid.UUID,
    submit_onchain: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(select(ArenaSession).where(ArenaSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    scores = await calculate_scores(session_id, db)

    if submit_onchain and session.onchain_id:
        try:
            bridge = ArenaContractBridge()
            for s in scores:
                # Find on-chain agent_id from Agent table
                agent_result = await db.execute(
                    select(Agent).where(Agent.id == s["agent_id"])
                )
                agent = agent_result.scalar_one_or_none()
                if agent and agent.onchain_id:
                    await bridge.submit_score(
                        session_id=session.onchain_id,
                        agent_id=agent.onchain_id,
                        total_pnl=s["total_pnl"],
                        sharpe_ratio=s["sharpe_ratio"],
                        win_rate=s["win_rate"],
                        trade_count=s["trade_count"],
                    )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"On-chain submission failed: {exc}")

    return [
        {
            "rank": s["rank"],
            "agent_id": str(s["agent_id"]),
            "total_pnl": float(s["total_pnl"]),
            "sharpe_ratio": float(s["sharpe_ratio"]),
            "win_rate": float(s["win_rate"]),
            "trade_count": s["trade_count"],
        }
        for s in scores
    ]


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ArenaSession).where(ArenaSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.end_time = datetime.now(timezone.utc)
    await db.flush()

    # End on-chain session (best-effort)
    if session.onchain_id:
        try:
            bridge = ArenaContractBridge()
            await bridge.end_session(session.onchain_id)
        except Exception:
            pass

    await manager.broadcast(
        "arena",
        {
            "type": "session_ended",
            "session_id": str(session_id),
            "onchain_id": session.onchain_id,
        },
    )

    return {"status": "completed", "session_id": str(session_id)}
