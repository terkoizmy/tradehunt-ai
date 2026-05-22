"""Contract bridge — logs trades on-chain via TradeRegistry.

Uses web3.py to interact with the TradeRegistry contract on Mantle Sepolia.
The deployer wallet is the contract owner and must be linked to each agentId
before it can call logTrade on behalf of that agent.
"""

from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from functools import lru_cache
from typing import Any

from web3 import Web3

from api.src.config import get_settings

logger = logging.getLogger("tradehunt.contract_bridge")

TRADE_REGISTRY_ABI = json.dumps(
    [
        {
            "inputs": [
                {"internalType": "uint256", "name": "agentId", "type": "uint256"},
                {"internalType": "address", "name": "agentWallet", "type": "address"},
            ],
            "name": "linkAgent",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "agentId", "type": "uint256"},
                {"internalType": "string", "name": "symbol", "type": "string"},
                {"internalType": "string", "name": "side", "type": "string"},
                {"internalType": "uint256", "name": "price", "type": "uint256"},
                {"internalType": "uint256", "name": "quantity", "type": "uint256"},
                {"internalType": "int256", "name": "pnl", "type": "int256"},
            ],
            "name": "logTrade",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "uint256", "name": "agentId", "type": "uint256"}],
            "name": "getAgentStats",
            "outputs": [
                {"internalType": "uint256", "name": "totalTrades", "type": "uint256"},
                {"internalType": "int256", "name": "totalPnl", "type": "int256"},
                {"internalType": "uint256", "name": "winCount", "type": "uint256"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "totalTrades",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "agentId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "wallet", "type": "address"},
            ],
            "name": "AgentLinked",
            "type": "event",
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "agentId", "type": "uint256"},
                {"internalType": "string", "name": "symbol", "type": "string"},
                {"internalType": "string", "name": "side", "type": "string"},
                {"internalType": "uint256", "name": "price", "type": "uint256"},
                {"internalType": "uint256", "name": "quantity", "type": "uint256"},
                {"internalType": "int256", "name": "pnl", "type": "int256"},
                {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            ],
            "name": "TradeExecuted",
            "type": "event",
        },
    ]
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Mantle Sepolia uses legacy tx format (no EIP-1559 support)
GAS_PRICE_GWEI = 0.05  # Mantle Sepolia gas price in gwei
GAS_LIMIT_LOG_TRADE = 300_000
GAS_LIMIT_LINK_AGENT = 100_000


class ContractBridge:
    """Logs agent trades on-chain via TradeRegistry."""

    def __init__(self) -> None:
        settings = get_settings()
        self.w3 = Web3(Web3.HTTPProvider(settings.mantle_sepolia_rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to {settings.mantle_sepolia_rpc_url}")

        self.account = self.w3.eth.account.from_key(settings.private_key)
        self.address = self.account.address

        self.registry_address = settings.trade_registry_address
        if not self.registry_address:
            raise ValueError("TRADE_REGISTRY_ADDRESS not set in .env")

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.registry_address),
            abi=json.loads(TRADE_REGISTRY_ABI),
        )

        logger.info(
            "ContractBridge ready | address=%s | registry=%s",
            self.address,
            self.registry_address,
        )

    # ─── Link agent ─────────────────────────────────────────────────────────

    async def link_agent(self, agent_id: int, agent_wallet: str) -> str:
        """Link an agentId to a wallet so logTrade can be called by that wallet.

        Must be called once per agent before logging trades.
        Only the contract owner can call this.
        """
        tx_hash = await self._send_with_retry(
            self.contract.functions.linkAgent(agent_id, Web3.to_checksum_address(agent_wallet)),
            gas_limit=GAS_LIMIT_LINK_AGENT,
        )
        logger.info("Linked agent %s to wallet %s | tx=%s", agent_id, agent_wallet, tx_hash)
        return tx_hash

    # ─── Log trade ────────────────────────────────────────────────────────────

    async def log_trade(
        self,
        agent_id: int,
        symbol: str,
        side: str,
        price: Decimal,
        quantity: Decimal,
        pnl: Decimal,
    ) -> str:
        """Log a single trade on-chain. Returns tx hash."""
        # Scale: contract expects raw uint256 (no decimals for hackathon)
        price_int = int(price)
        quantity_int = int(quantity)
        pnl_int = int(pnl)

        tx_hash = await self._send_with_retry(
            self.contract.functions.logTrade(
                agent_id,
                symbol,
                side,
                price_int,
                quantity_int,
                pnl_int,
            ),
            gas_limit=GAS_LIMIT_LOG_TRADE,
        )
        logger.info(
            "Logged trade on-chain | agent=%s | %s %s | price=%s | qty=%s | pnl=%s | tx=%s",
            agent_id,
            side,
            symbol,
            price_int,
            quantity_int,
            pnl_int,
            tx_hash,
        )
        return tx_hash

    # ─── Read stats ─────────────────────────────────────────────────────────

    async def get_agent_stats(self, agent_id: int) -> dict[str, Any]:
        """Read on-chain stats for an agent."""
        total_trades, total_pnl, win_count = await asyncio.to_thread(
            self.contract.functions.getAgentStats(agent_id).call
        )
        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_count": win_count,
        }

    # ─── Internal: send tx with retry ───────────────────────────────────────

    async def _send_with_retry(self, contract_func, gas_limit: int) -> str:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self._send_tx(contract_func, gas_limit)
            except Exception as exc:
                last_error = exc
                logger.warning("Tx attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise last_error or RuntimeError("All tx attempts failed")

    async def _send_tx(self, contract_func, gas_limit: int) -> str:
        # Fetch fresh nonce before each tx to avoid collisions
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


@lru_cache
def get_contract_bridge() -> ContractBridge:
    """Return a singleton ContractBridge instance."""
    return ContractBridge()
