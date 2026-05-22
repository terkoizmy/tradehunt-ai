"""Arena contract bridge — submits scores to ArenaLeaderboard on-chain."""

from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any

from web3 import Web3

from api.src.config import get_settings

logger = logging.getLogger("tradehunt.arena_bridge")

ARENA_LEADERBOARD_ABI = json.dumps(
    [
        {
            "inputs": [
                {"internalType": "string", "name": "name", "type": "string"},
                {"internalType": "uint256", "name": "duration", "type": "uint256"},
            ],
            "name": "createSession",
            "outputs": [{"internalType": "uint256", "name": "sessionId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "sessionId", "type": "uint256"},
                {"internalType": "uint256", "name": "agentId", "type": "uint256"},
                {"internalType": "int256", "name": "totalPnl", "type": "int256"},
                {"internalType": "int256", "name": "sharpeRatio", "type": "int256"},
                {"internalType": "uint256", "name": "winRate", "type": "uint256"},
                {"internalType": "uint256", "name": "tradeCount", "type": "uint256"},
            ],
            "name": "submitScore",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "sessionId", "type": "uint256"},
            ],
            "name": "endSession",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "sessionId", "type": "uint256"},
            ],
            "name": "getLeaderboard",
            "outputs": [
                {
                    "components": [
                        {"internalType": "uint256", "name": "agentId", "type": "uint256"},
                        {"internalType": "int256", "name": "totalPnl", "type": "int256"},
                        {"internalType": "int256", "name": "sharpeRatio", "type": "int256"},
                        {"internalType": "uint256", "name": "winRate", "type": "uint256"},
                        {"internalType": "uint256", "name": "tradeCount", "type": "uint256"},
                        {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                    ],
                    "internalType": "struct ArenaLeaderboard.AgentScore[]",
                    "name": "",
                    "type": "tuple[]",
                }
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "sessionCount",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "name": "sessions",
            "outputs": [
                {"internalType": "string", "name": "name", "type": "string"},
                {"internalType": "uint256", "name": "startTime", "type": "uint256"},
                {"internalType": "uint256", "name": "endTime", "type": "uint256"},
                {"internalType": "bool", "name": "active", "type": "bool"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
    ]
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
GAS_PRICE_GWEI = 0.05
GAS_LIMIT_CREATE_SESSION = 300_000
GAS_LIMIT_SUBMIT_SCORE = 300_000
GAS_LIMIT_END_SESSION = 200_000


class ArenaContractBridge:
    """Submits arena scores to the ArenaLeaderboard contract on Mantle Sepolia."""

    def __init__(self) -> None:
        settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(settings.mantle_sepolia_rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to {settings.mantle_sepolia_rpc_url}")

        self.account = self.w3.eth.account.from_key(settings.private_key)
        self.address = self.account.address

        addr = settings.arena_leaderboard_address
        if not addr:
            raise ValueError("ARENA_LEADERBOARD_ADDRESS not set in .env")

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(addr),
            abi=json.loads(ARENA_LEADERBOARD_ABI),
        )
        logger.info(
            "ArenaContractBridge ready | address=%s | contract=%s",
            self.address,
            addr,
        )

    async def create_session(self, name: str, duration_seconds: int) -> int:
        """Create a session on-chain. Returns on-chain sessionId."""
        tx_hash = await self._send_with_retry(
            self.contract.functions.createSession(name, duration_seconds),
            gas_limit=GAS_LIMIT_CREATE_SESSION,
        )
        logger.info("Created arena session on-chain | name=%s | tx=%s", name, tx_hash)
        # Extract sessionId from contract state (simplified)
        return await asyncio.to_thread(self.contract.functions.sessionCount().call)

    async def submit_score(
        self,
        session_id: int,
        agent_id: int,
        total_pnl: Decimal,
        sharpe_ratio: Decimal,
        win_rate: Decimal,
        trade_count: int,
    ) -> str:
        """Submit a single agent score on-chain."""
        # Scaling conventions:
        #   sharpe_ratio × 1_000_000 (e.g. 1.5 → 1_500_000)
        #   win_rate × 10_000 (e.g. 0.75 → 7_500)
        sharpe_scaled = int(sharpe_ratio * Decimal("1_000_000"))
        win_rate_scaled = int(win_rate * Decimal("10_000"))
        pnl_int = int(total_pnl)

        tx_hash = await self._send_with_retry(
            self.contract.functions.submitScore(
                session_id,
                agent_id,
                pnl_int,
                sharpe_scaled,
                win_rate_scaled,
                trade_count,
            ),
            gas_limit=GAS_LIMIT_SUBMIT_SCORE,
        )
        logger.info(
            "Submitted score on-chain | session=%s | agent=%s | pnl=%s | tx=%s",
            session_id,
            agent_id,
            pnl_int,
            tx_hash,
        )
        return tx_hash

    async def end_session(self, session_id: int) -> str:
        """End an arena session on-chain."""
        tx_hash = await self._send_with_retry(
            self.contract.functions.endSession(session_id),
            gas_limit=GAS_LIMIT_END_SESSION,
        )
        logger.info("Ended arena session on-chain | session=%s | tx=%s", session_id, tx_hash)
        return tx_hash

    async def get_leaderboard(self, session_id: int) -> list[dict[str, Any]]:
        """Read leaderboard from chain."""
        raw = await asyncio.to_thread(self.contract.functions.getLeaderboard(session_id).call)
        return [
            {
                "agent_id": r[0],
                "total_pnl": r[1],
                "sharpe_ratio": Decimal(r[2]) / Decimal("1_000_000"),
                "win_rate": Decimal(r[3]) / Decimal("10_000"),
                "trade_count": r[4],
                "updated_at": r[5],
            }
            for r in raw
        ]

    # ─── Internal tx helpers ─────────────────────────────────────────────────

    async def _send_with_retry(self, contract_func, gas_limit: int) -> str:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self._send_tx(contract_func, gas_limit)
            except Exception as exc:
                last_error = exc
                logger.warning("Arena tx attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise last_error or RuntimeError("All arena tx attempts failed")

    async def _send_tx(self, contract_func, gas_limit: int) -> str:
        nonce = await asyncio.to_thread(
            self.w3.eth.get_transaction_count, self.address
        )
        gas_price = await asyncio.to_thread(self.w3.to_wei, GAS_PRICE_GWEI, "gwei")

        tx = await asyncio.to_thread(
            contract_func.build_transaction,
            {
                "from": self.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": self.w3.eth.chain_id,
            },
        )
        signed = await asyncio.to_thread(
            self.w3.eth.account.sign_transaction, tx, self.account.key
        )
        tx_hash = await asyncio.to_thread(
            self.w3.eth.send_raw_transaction, signed.raw_transaction
        )
        receipt = await asyncio.to_thread(
            self.w3.eth.wait_for_transaction_receipt, tx_hash, timeout=60
        )
        if receipt["status"] != 1:
            raise RuntimeError(f"Tx reverted: {tx_hash.hex()}")
        return tx_hash.hex()
