// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "forge-std/Test.sol";
import {TradeRegistry} from "../src/TradeRegistry.sol";

contract TradeRegistryTest is Test {
    TradeRegistry public registry;
    address public owner = address(0x1);
    address public agent = address(0x2);
    uint256 public constant AGENT_ID = 1;

    function setUp() public {
        vm.prank(owner);
        registry = new TradeRegistry();
    }

    function test_LinkAgent() public {
        vm.prank(owner);
        registry.linkAgent(AGENT_ID, agent);
        assertEq(registry.agentWalletToId(agent), AGENT_ID);
    }

    function test_LogTrade() public {
        vm.prank(owner);
        registry.linkAgent(AGENT_ID, agent);

        vm.prank(agent);
        registry.logTrade(AGENT_ID, "BTCUSDT", "buy", 6500000, 100, 5000);

        (uint256 trades, int256 pnl, uint256 wins) = registry.getAgentStats(AGENT_ID);
        assertEq(trades, 1);
        assertEq(pnl, 5000);
        assertEq(wins, 1);
        assertEq(registry.totalTrades(), 1);
    }

    function test_RevertIfNotLinked() public {
        vm.prank(agent);
        vm.expectRevert("Sender not linked to agent");
        registry.logTrade(AGENT_ID, "BTCUSDT", "buy", 6500000, 100, 5000);
    }

    function test_LosingTrade() public {
        vm.prank(owner);
        registry.linkAgent(AGENT_ID, agent);

        vm.prank(agent);
        registry.logTrade(AGENT_ID, "ETHUSDT", "sell", 300000, 10, -2000);

        (, int256 pnl, uint256 wins) = registry.getAgentStats(AGENT_ID);
        assertEq(pnl, -2000);
        assertEq(wins, 0);
    }
}
