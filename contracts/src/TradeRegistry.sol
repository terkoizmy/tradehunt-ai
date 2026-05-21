// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Ownable} from "openzeppelin-contracts/access/Ownable.sol";

contract TradeRegistry is Ownable {
    struct AgentStats {
        uint256 totalTrades;
        int256 totalPnl;
        uint256 winCount;
    }

    mapping(uint256 => AgentStats) public agentStats;
    mapping(address => uint256) public agentWalletToId;

    uint256 public totalTrades;

    event TradeExecuted(
        uint256 indexed agentId,
        string symbol,
        string side,
        uint256 price,
        uint256 quantity,
        int256 pnl,
        uint256 timestamp
    );

    event AgentLinked(uint256 indexed agentId, address indexed wallet);

    constructor() Ownable(msg.sender) {}

    function linkAgent(uint256 agentId, address agentWallet) external onlyOwner {
        agentWalletToId[agentWallet] = agentId;
        emit AgentLinked(agentId, agentWallet);
    }

    function logTrade(
        uint256 agentId,
        string calldata symbol,
        string calldata side,
        uint256 price,
        uint256 quantity,
        int256 pnl
    ) external {
        require(
            agentWalletToId[msg.sender] == agentId,
            "Sender not linked to agent"
        );

        AgentStats storage stats = agentStats[agentId];
        stats.totalTrades++;
        stats.totalPnl += pnl;
        if (pnl > 0) {
            stats.winCount++;
        }
        totalTrades++;

        emit TradeExecuted(
            agentId,
            symbol,
            side,
            price,
            quantity,
            pnl,
            block.timestamp
        );
    }

    function getAgentStats(uint256 agentId)
        external
        view
        returns (uint256 totalTrades_, int256 totalPnl_, uint256 winCount_)
    {
        AgentStats storage stats = agentStats[agentId];
        return (stats.totalTrades, stats.totalPnl, stats.winCount);
    }
}
