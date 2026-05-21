"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.src.config import get_settings
from api.src.routes import agents, arena, trades
from api.src.ws.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Tradehunt API starting on {settings.api_host}:{settings.api_port}")
    yield
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
