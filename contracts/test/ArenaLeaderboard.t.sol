// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "forge-std/Test.sol";
import {ArenaLeaderboard} from "../src/ArenaLeaderboard.sol";

contract ArenaLeaderboardTest is Test {
    ArenaLeaderboard public board;
    address public owner = address(0x1);
    uint256 public constant AGENT_1 = 1;
    uint256 public constant AGENT_2 = 2;

    function setUp() public {
        vm.prank(owner);
        board = new ArenaLeaderboard();
    }

    function test_CreateSession() public {
        vm.prank(owner);
        uint256 id = board.createSession("Test Round", 1 hours);
        assertEq(id, 1);
        (string memory name, uint256 start, uint256 end, bool active) = board.sessions(id);
        assertEq(name, "Test Round");
        assertTrue(active);
        assertEq(end, start + 1 hours);
    }

    function test_SubmitScore() public {
        vm.prank(owner);
        uint256 sessionId = board.createSession("Round 1", 1 hours);

        vm.prank(owner);
        board.submitScore(sessionId, AGENT_1, 10000, 1500000, 7500, 42);

        (uint256 scoreAgentId, int256 totalPnl, int256 sharpeRatio, uint256 winRate, uint256 tradeCount,) = board.scores(sessionId, AGENT_1);
        assertEq(totalPnl, 10000);
        assertEq(sharpeRatio, 1500000);
        assertEq(winRate, 7500);
        assertEq(tradeCount, 42);
    }

    function test_GetLeaderboard() public {
        vm.startPrank(owner);
        uint256 sessionId = board.createSession("Round 1", 1 hours);
        board.submitScore(sessionId, AGENT_1, 10000, 1500000, 7500, 42);
        board.submitScore(sessionId, AGENT_2, 5000, 1200000, 6500, 30);
        vm.stopPrank();

        ArenaLeaderboard.AgentScore[] memory scores = board.getLeaderboard(sessionId);
        assertEq(scores.length, 2);
    }

    function test_EndSession() public {
        vm.startPrank(owner);
        uint256 sessionId = board.createSession("Round 1", 1 hours);
        board.endSession(sessionId);
        (, , , bool active) = board.sessions(sessionId);
        assertFalse(active);
    }

    function test_RevertIfEndSessionTwice() public {
        vm.startPrank(owner);
        uint256 sessionId = board.createSession("Round 1", 1 hours);
        board.endSession(sessionId);
        vm.expectRevert("Session already ended");
        board.endSession(sessionId);
        vm.stopPrank();
    }
}
