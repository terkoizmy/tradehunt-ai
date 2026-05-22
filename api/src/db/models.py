"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DECIMAL, Integer, JSON, String, Text, Uuid

from api.src.db.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    api_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    persona: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_config: Mapped[dict | None] = mapped_column(JSON)
    agent_uri: Mapped[str | None] = mapped_column(Text)
    onchain_id: Mapped[int | None] = mapped_column(Integer)
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="idle")
    capital: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), default=Decimal("0"))
    symbol: Mapped[str | None] = mapped_column(String(20))
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    trades: Mapped[list["Trade"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["Decision"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    pnl: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    stop_loss: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    take_profit: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    confidence: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    reasoning: Mapped[str | None] = mapped_column(Text)
    order_id: Mapped[str | None] = mapped_column(String(50))
    tx_hash: Mapped[str | None] = mapped_column(String(66))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    agent: Mapped["Agent"] = relationship(back_populates="trades")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    reasoning: Mapped[str | None] = mapped_column(Text)
    signal_action: Mapped[str | None] = mapped_column(String(10))
    signal_confidence: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    risk_allowed: Mapped[bool] = mapped_column(default=True)
    risk_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    agent: Mapped["Agent"] = relationship(back_populates="decisions")


class ArenaSession(Base):
    __tablename__ = "arena_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    onchain_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    scores: Mapped[list["ArenaScore"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ArenaScore(Base):
    __tablename__ = "arena_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("arena_sessions.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    total_pnl: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), default=0)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    win_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    trade_count: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["ArenaSession"] = relationship(back_populates="scores")
