"""Application configuration loaded from .env."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Mantle
    mantle_sepolia_rpc_url: str = "https://rpc.sepolia.mantle.xyz"
    mantle_chain_id: int = 5003
    private_key: str = ""

    # Bybit
    bybit_testnet: bool = True
    bybit_api_key: str = ""
    bybit_api_secret: str = ""

    # Ollama
    ollama_api_url: str = "http://localhost:11434"
    ollama_api_key: str = ""
    ollama_model: str = "qwen2.5:7b"

    # Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tradehunt"
    postgres_user: str = "tradehunt"
    postgres_password: str = "tradehunt_dev"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Bybit URLs
    bybit_rest_url: str = "https://api-testnet.bybit.com"
    bybit_ws_url: str = "wss://stream-testnet.bybit.com/v5"

    # Deployed Contracts
    deployer_address: str = ""
    erc8004_registry_address: str = ""
    agent_identity_address: str = ""
    trade_registry_address: str = ""
    arena_leaderboard_address: str = ""
    reputation_feed_address: str = ""

    # Covalent
    covalent_api_key: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
