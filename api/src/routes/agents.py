"""Agent management routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.database import get_db
from api.src.db.models import Agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    persona: str
    wallet_address: str
    agent_uri: str | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    persona: str
    wallet_address: str
    status: str
    onchain_id: int | None
    created_at: str

    class Config:
        from_attributes = True


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
            onchain_id=a.onchain_id,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in agents
    ]


@router.post("", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    agent = Agent(
        id=uuid.uuid4(),
        name=body.name,
        persona=body.persona,
        wallet_address=body.wallet_address,
        agent_uri=body.agent_uri,
        status="idle",
    )
    db.add(agent)
    await db.flush()
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        persona=agent.persona,
        wallet_address=agent.wallet_address,
        status=agent.status,
        onchain_id=agent.onchain_id,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
    )


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
        onchain_id=agent.onchain_id,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
    )


@router.post("/{agent_id}/start")
async def start_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "running"
    await db.flush()
    return {"status": "running", "agent_id": str(agent_id)}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "stopped"
    await db.flush()
    return {"status": "stopped", "agent_id": str(agent_id)}
