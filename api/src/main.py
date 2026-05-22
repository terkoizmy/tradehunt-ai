"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.config import get_settings
from api.src.db.database import async_session
from api.src.db.models import Agent, ArenaSession
from api.src.routes import agents, arena, trades
from api.src.services.scoring import calculate_scores
from api.src.ws.manager import manager

logger = logging.getLogger("tradehunt.main")

HEARTBEAT_OFFLINE_SECONDS = 90
HEARTBEAT_IDLE_MINUTES = 5
ARENA_SCORING_INTERVAL_SECONDS = 60


async def _heartbeat_monitor() -> None:
    """Background task: mark agents offline/idle based on heartbeat age."""
    while True:
        await asyncio.sleep(30)
        now = datetime.now(timezone.utc)
        async with async_session() as db:
            result = await db.execute(select(Agent))
            agents_list = result.scalars().all()
            for agent in agents_list:
                if agent.status in ("stopped", "error"):
                    continue

                if agent.last_heartbeat is None:
                    continue

                age_seconds = (now - agent.last_heartbeat).total_seconds()

                # Mark offline after 90s without heartbeat
                if age_seconds > HEARTBEAT_OFFLINE_SECONDS and agent.status != "offline":
                    agent.status = "offline"
                    await manager.broadcast(
                        "trades",
                        {
                            "type": "agent_status",
                            "agent_id": str(agent.id),
                            "status": "offline",
                        },
                    )
                    continue

                # Mark idle after 5 min without trades
                # (simplified: check last heartbeat age vs 5 minutes)
                if agent.status == "online" and age_seconds > (HEARTBEAT_IDLE_MINUTES * 60):
                    agent.status = "idle"
                    await manager.broadcast(
                        "trades",
                        {
                            "type": "agent_status",
                            "agent_id": str(agent.id),
                            "status": "idle",
                        },
                    )

            await db.commit()


async def _arena_scoring_monitor() -> None:
    """Background task: periodically calculate scores for active arena sessions."""
    while True:
        await asyncio.sleep(ARENA_SCORING_INTERVAL_SECONDS)
        now = datetime.now(timezone.utc)
        async with async_session() as db:
            result = await db.execute(
                select(ArenaSession).where(ArenaSession.status == "active")
            )
            sessions = result.scalars().all()
            for session in sessions:
                if session.end_time and now > session.end_time:
                    continue
                try:
                    await calculate_scores(session.id, db)
                    await db.commit()
                except Exception:
                    logger.exception("Arena scoring monitor error for session %s", session.id)
                    await db.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Tradehunt API starting on {settings.api_host}:{settings.api_port}")
    heartbeat_task = asyncio.create_task(_heartbeat_monitor())
    scoring_task = asyncio.create_task(_arena_scoring_monitor())
    yield
    heartbeat_task.cancel()
    scoring_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    try:
        await scoring_task
    except asyncio.CancelledError:
        pass
    print("Tradehunt API shutting down")


app = FastAPI(
    title="tradehunt-ai API",
    description="AI trading hunter agent arena platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(arena.router)
app.include_router(trades.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "tradehunt-api"}


@app.websocket("/ws/trades")
async def ws_trades(websocket: WebSocket) -> None:
    await manager.connect("trades", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("trades", websocket)


@app.websocket("/ws/arena/{session_id}")
async def ws_arena(websocket: WebSocket, session_id: str) -> None:
    await manager.connect("arena", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("arena", websocket)
