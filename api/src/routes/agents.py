"""Agent management routes — heartbeat, trade reporting, decisions."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.database import get_db
from api.src.db.models import Agent, Decision, Trade
from api.src.ws.manager import manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ─── Auth dependency ────────────────────────────────────────────────────────

async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    result = await db.execute(select(Agent).where(Agent.api_key == x_api_key))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent


# ─── Pydantic schemas ───────────────────────────────────────────────────────

class AgentRegister(BaseModel):
    name: str
    persona: str
    wallet_address: str
    capital: float = Field(default=10000.0, ge=0)
    symbol: str = "BTCUSDT"
    persona_config: dict[str, Any] | None = None
    agent_uri: str | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    persona: str
    wallet_address: str
    status: str
    symbol: str | None
    capital: float | None
    last_heartbeat: str | None
    onchain_id: int | None
    created_at: str

    model_config = {"from_attributes": True}


class HeartbeatResponse(BaseModel):
    status: str
    agent_id: str
    timestamp: str


class TradeReport(BaseModel):
    action: str
    symbol: str
    side: str
    price: float
    quantity: float
    pnl: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    confidence: float | None = None
    reasoning: str | None = None
    order_id: str | None = None
    tx_hash: str | None = None
    executed_at: str | None = None


class DecisionReport(BaseModel):
    action: str
    symbol: str
    confidence: float | None = None
    reasoning: str | None = None
    signal_action: str | None = None
    signal_confidence: float | None = None
    risk_allowed: bool = True
    risk_reason: str | None = None


class TradeResponse(BaseModel):
    id: uuid.UUID
    action: str
    symbol: str
    side: str
    price: float
    quantity: float
    pnl: float | None
    confidence: float | None
    reasoning: str | None
    order_id: str | None
    executed_at: str | None
    created_at: str | None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=dict)
async def register_agent(body: AgentRegister, db: AsyncSession = Depends(get_db)) -> dict:
    api_key = secrets.token_urlsafe(32)
    agent = Agent(
        id=uuid.uuid4(),
        api_key=api_key,
        name=body.name,
        persona=body.persona,
        persona_config=body.persona_config,
        wallet_address=body.wallet_address,
        agent_uri=body.agent_uri,
        status="idle",
        capital=Decimal(str(body.capital)),
        symbol=body.symbol,
    )
    db.add(agent)
    await db.flush()

    await manager.broadcast(
        "trades",
        {
            "type": "agent_registered",
            "agent_id": str(agent.id),
            "name": agent.name,
            "persona": agent.persona,
        },
    )

    return {
        "agent_id": str(agent.id),
        "api_key": api_key,
        "name": agent.name,
        "persona": agent.persona,
        "status": agent.status,
    }


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    persona: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AgentResponse]:
    stmt = select(Agent)
    if persona:
        stmt = stmt.where(Agent.persona == persona)
    if status:
        stmt = stmt.where(Agent.status == status)
    result = await db.execute(stmt)
    agents = result.scalars().all()
    return [
        AgentResponse(
            id=a.id,
            name=a.name,
            persona=a.persona,
            wallet_address=a.wallet_address,
            status=a.status,
            symbol=a.symbol,
            capital=float(a.capital) if a.capital else None,
            last_heartbeat=a.last_heartbeat.isoformat() if a.last_heartbeat else None,
            onchain_id=a.onchain_id,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        persona=agent.persona,
        wallet_address=agent.wallet_address,
        status=agent.status,
        symbol=agent.symbol,
        capital=float(agent.capital) if agent.capital else None,
        last_heartbeat=agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
        onchain_id=agent.onchain_id,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
    )


@router.post("/{agent_id}/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    agent_id: uuid.UUID,
    agent: Agent = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> HeartbeatResponse:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")

    now = datetime.now(timezone.utc)
    agent.status = "online"
    agent.last_heartbeat = now
    await db.flush()

    await manager.broadcast(
        "trades",
        {
            "type": "agent_status",
            "agent_id": str(agent.id),
            "status": "online",
            "timestamp": now.isoformat(),
        },
    )

    return HeartbeatResponse(
        status="online",
        agent_id=str(agent.id),
        timestamp=now.isoformat(),
    )


@router.post("/{agent_id}/trades", response_model=TradeResponse)
async def report_trade(
    agent_id: uuid.UUID,
    body: TradeReport,
    agent: Agent = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> TradeResponse:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")

    trade = Trade(
        id=uuid.uuid4(),
        agent_id=agent.id,
        action=body.action,
        symbol=body.symbol,
        side=body.side,
        price=Decimal(str(body.price)),
        quantity=Decimal(str(body.quantity)),
        pnl=Decimal(str(body.pnl)) if body.pnl is not None else None,
        stop_loss=Decimal(str(body.stop_loss)) if body.stop_loss is not None else None,
        take_profit=Decimal(str(body.take_profit)) if body.take_profit is not None else None,
        confidence=Decimal(str(body.confidence)) if body.confidence is not None else None,
        reasoning=body.reasoning,
        order_id=body.order_id,
        tx_hash=body.tx_hash,
        executed_at=datetime.fromisoformat(body.executed_at) if body.executed_at else None,
    )
    db.add(trade)
    await db.flush()

    await manager.broadcast(
        "trades",
        {
            "type": "trade",
            "agent_id": str(agent.id),
            "action": body.action,
            "symbol": body.symbol,
            "side": body.side,
            "price": body.price,
            "quantity": body.quantity,
            "pnl": body.pnl,
        },
    )

    return TradeResponse(
        id=trade.id,
        action=trade.action,
        symbol=trade.symbol,
        side=trade.side,
        price=float(trade.price),
        quantity=float(trade.quantity),
        pnl=float(trade.pnl) if trade.pnl else None,
        confidence=float(trade.confidence) if trade.confidence else None,
        reasoning=trade.reasoning,
        order_id=trade.order_id,
        executed_at=trade.executed_at.isoformat() if trade.executed_at else None,
        created_at=trade.created_at.isoformat() if trade.created_at else None,
    )


@router.post("/{agent_id}/decisions")
async def report_decision(
    agent_id: uuid.UUID,
    body: DecisionReport,
    agent: Agent = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")

    decision = Decision(
        id=uuid.uuid4(),
        agent_id=agent.id,
        action=body.action,
        symbol=body.symbol,
        confidence=Decimal(str(body.confidence)) if body.confidence is not None else None,
        reasoning=body.reasoning,
        signal_action=body.signal_action,
        signal_confidence=Decimal(str(body.signal_confidence)) if body.signal_confidence is not None else None,
        risk_allowed=body.risk_allowed,
        risk_reason=body.risk_reason,
    )
    db.add(decision)
    await db.flush()

    await manager.broadcast(
        "trades",
        {
            "type": "decision",
            "agent_id": str(agent.id),
            "action": body.action,
            "symbol": body.symbol,
            "confidence": body.confidence,
            "reasoning": body.reasoning,
            "risk_allowed": body.risk_allowed,
        },
    )

    return {"id": str(decision.id), "agent_id": str(agent.id), "status": "recorded"}


@router.post("/{agent_id}/offline")
async def set_offline(
    agent_id: uuid.UUID,
    agent: Agent = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")

    agent.status = "stopped"
    await db.flush()

    await manager.broadcast(
        "trades",
        {
            "type": "agent_status",
            "agent_id": str(agent.id),
            "status": "stopped",
        },
    )

    return {"status": "stopped", "agent_id": str(agent.id)}


@router.get("/{agent_id}/trades", response_model=list[TradeResponse])
async def get_agent_trades(
    agent_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[TradeResponse]:
    result = await db.execute(
        select(Trade)
        .where(Trade.agent_id == agent_id)
        .order_by(Trade.created_at.desc())
        .limit(limit)
    )
    trades = result.scalars().all()
    return [
        TradeResponse(
            id=t.id,
            action=t.action,
            symbol=t.symbol,
            side=t.side,
            price=float(t.price),
            quantity=float(t.quantity),
            pnl=float(t.pnl) if t.pnl else None,
            confidence=float(t.confidence) if t.confidence else None,
            reasoning=t.reasoning,
            order_id=t.order_id,
            executed_at=t.executed_at.isoformat() if t.executed_at else None,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in trades
    ]
