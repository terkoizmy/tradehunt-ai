"""WebSocket manager for real-time trade and arena broadcasts."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {
            "trades": [],
            "arena": [],
        }

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if channel in self._connections:
            self._connections[channel].append(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self._connections:
            self._connections[channel].remove(websocket)

    async def broadcast(self, channel: str, data: dict[str, Any]) -> None:
        if channel not in self._connections:
            return
        payload = json.dumps(data)
        disconnected: list[WebSocket] = []
        for ws in self._connections[channel]:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(channel, ws)


manager = ConnectionManager()
