"""Tests for contract bridge (Issue #6)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from api.src.services.contract_bridge import ContractBridge


@pytest.fixture
def mock_settings():
    with patch("api.src.services.contract_bridge.get_settings") as m:
        settings = MagicMock()
        settings.mantle_sepolia_rpc_url = "https://rpc.sepolia.mantle.xyz"
        settings.private_key = (
            "0x" + "11" * 32
        )  # 64-char hex private key
        settings.trade_registry_address = "0x9bdB714930efaBb41A0647809fe980d173E2d510"
        m.return_value = settings
        yield settings


@pytest.fixture
def mock_web3():
    with patch("api.src.services.contract_bridge.Web3") as MockWeb3:
        w3 = MagicMock()
        w3.is_connected.return_value = True
        w3.eth.chain_id = 5003
        w3.eth.get_transaction_count.return_value = 42
        w3.to_wei.return_value = 50_000_000
        w3.eth.send_raw_transaction.return_value = MagicMock(hex=lambda: "0xabc123")

        receipt = {"status": 1, "transactionHash": "0xabc123"}
        w3.eth.wait_for_transaction_receipt.return_value = receipt

        MockWeb3.HTTPProvider.return_value = MagicMock()
        MockWeb3.return_value = w3
        MockWeb3.to_checksum_address = lambda x: x
        yield MockWeb3, w3


@pytest.fixture
def bridge(mock_settings, mock_web3):
    MockWeb3, w3 = mock_web3
    # Patch eth.account.from_key to avoid real crypto
    with patch.object(
        w3.eth.account,
        "from_key",
        return_value=MagicMock(address="0xDeployer", key=b"key"),
    ):
        with patch.object(w3.eth.account, "sign_transaction", return_value=MagicMock(raw_transaction=b"signed")):
            yield ContractBridge()


@pytest.mark.asyncio
async def test_link_agent(bridge):
    with patch.object(bridge, "_send_with_retry", return_value="0xlinktx") as mock_send:
        tx = await bridge.link_agent(1, "0xAgentWallet")
        assert tx == "0xlinktx"
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_log_trade(bridge):
    with patch.object(bridge, "_send_with_retry", return_value="0xtradetx") as mock_send:
        tx = await bridge.log_trade(
            agent_id=1,
            symbol="BTCUSDT",
            side="Buy",
            price=Decimal("50000"),
            quantity=Decimal("1"),
            pnl=Decimal("100"),
        )
        assert tx == "0xtradetx"
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_get_agent_stats(bridge):
    bridge.contract.functions.getAgentStats.return_value.call.return_value = (10, 500, 7)
    stats = await bridge.get_agent_stats(1)
    assert stats["total_trades"] == 10
    assert stats["total_pnl"] == 500
    assert stats["win_count"] == 7


def test_send_with_retry_succeeds_first_try(bridge):
    bridge._send_tx = MagicMock(return_value="0xok")
    result = bridge._send_with_retry(MagicMock(), 100_000)
    assert result == "0xok"
    assert bridge._send_tx.call_count == 1


def test_send_with_retry_retries_then_succeeds(bridge):
    bridge._send_tx = MagicMock(side_effect=[RuntimeError("fail"), "0xok"])
    with patch("api.src.services.contract_bridge.time.sleep"):
        result = bridge._send_with_retry(MagicMock(), 100_000)
    assert result == "0xok"
    assert bridge._send_tx.call_count == 2


def test_send_with_retry_exhausts(bridge):
    bridge._send_tx = MagicMock(side_effect=RuntimeError("fail"))
    with pytest.raises(RuntimeError), patch("api.src.services.contract_bridge.time.sleep"):
        bridge._send_with_retry(MagicMock(), 100_000)
    assert bridge._send_tx.call_count == 3
