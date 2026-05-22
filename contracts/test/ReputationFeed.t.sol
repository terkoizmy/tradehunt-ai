// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "forge-std/Test.sol";
import {ReputationFeed} from "../src/ReputationFeed.sol";

contract ReputationFeedTest is Test {
    ReputationFeed public feed;
    address public owner = address(0x1);
    uint256 public constant AGENT_1 = 1;
    uint256 public constant AGENT_2 = 2;

    function setUp() public {
        vm.prank(owner);
        feed = new ReputationFeed();
    }

    function test_SubmitFeedback() public {
        vm.prank(owner);
        feed.submitFeedback(AGENT_1, 85000, "pnl");

        (uint256 agentId, address client, int256 score, string memory tag, uint256 timestamp) = feed.agentFeedback(AGENT_1, 0);
        assertEq(agentId, AGENT_1);
        assertEq(score, 85000);
        assertEq(tag, "pnl");
        assertEq(client, owner);
    }

    function test_AggregateRollingAverage() public {
        vm.startPrank(owner);
        feed.submitFeedback(AGENT_1, 100000, "sharpe"); // 10.0
        feed.submitFeedback(AGENT_1, 50000, "sharpe");  // 5.0 → avg = 7.5
        vm.stopPrank();

        int256 agg = feed.aggregateScores(AGENT_1, "sharpe");
        assertEq(agg, 75000); // 7.5 scaled by 1e4
    }

    function test_GetAgentReputationMultipleTags() public {
        vm.startPrank(owner);
        feed.submitFeedback(AGENT_1, 90000, "pnl");
        feed.submitFeedback(AGENT_1, 80000, "winrate");
        vm.stopPrank();

        string[] memory tags = new string[](2);
        tags[0] = "pnl";
        tags[1] = "winrate";

        (int256[] memory scores, uint256[] memory counts) = feed.getAgentReputation(AGENT_1, tags);
        assertEq(scores.length, 2);
        assertEq(scores[0], 90000);
        assertEq(scores[1], 80000);
        assertEq(counts[0], 1);
        assertEq(counts[1], 1);
    }

    function test_NonOwnerCannotSubmit() public {
        vm.expectRevert();
        feed.submitFeedback(AGENT_1, 50000, "pnl");
    }

    function test_MultipleAgentsIndependent() public {
        vm.startPrank(owner);
        feed.submitFeedback(AGENT_1, 100000, "pnl");
        feed.submitFeedback(AGENT_2, 200000, "pnl");
        vm.stopPrank();

        assertEq(feed.aggregateScores(AGENT_1, "pnl"), 100000);
        assertEq(feed.aggregateScores(AGENT_2, "pnl"), 200000);
    }
}
