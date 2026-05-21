"""Arena session management service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.db.models import ArenaSession


async def create_arena_session(
    name: str,
    duration_seconds: int,
    db: AsyncSession,
) -> ArenaSession:
    now = datetime.now(timezone.utc)
    session = ArenaSession(
        id=uuid.uuid4(),
        name=name,
        status="pending",
        start_time=now,
        end_time=datetime.fromtimestamp(
            now.timestamp() + duration_seconds, tz=timezone.utc
        ),
    )
    db.add(session)
    await db.flush()
    return session


async def end_session(session_id: uuid.UUID, db: AsyncSession) -> None:
    from sqlalchemy import select

    result = await db.execute(select(ArenaSession).where(ArenaSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.status = "completed"
        session.end_time = datetime.now(timezone.utc)
        await db.flush()
