// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Ownable} from "openzeppelin-contracts/access/Ownable.sol";

contract ArenaLeaderboard is Ownable {
    struct AgentScore {
        uint256 agentId;
        int256 totalPnl;
        int256 sharpeRatio; // scaled by 1e6
        uint256 winRate;    // scaled by 1e4 (e.g. 7500 = 75%)
        uint256 tradeCount;
        uint256 updatedAt;
    }

    struct Session {
        string name;
        uint256 startTime;
        uint256 endTime;
        bool active;
    }

    uint256 public sessionCount;
    mapping(uint256 => Session) public sessions;
    mapping(uint256 => mapping(uint256 => AgentScore)) public scores; // sessionId => agentId => score
    mapping(uint256 => uint256[]) public sessionAgents; // sessionId => agentId[]

    event SessionCreated(
        uint256 indexed sessionId,
        string name,
        uint256 startTime,
        uint256 endTime
    );

    event ScoreUpdated(
        uint256 indexed sessionId,
        uint256 indexed agentId,
        int256 totalPnl,
        int256 sharpeRatio,
        uint256 winRate
    );

    constructor() Ownable(msg.sender) {}

    function createSession(
        string calldata name,
        uint256 duration
    ) external onlyOwner returns (uint256 sessionId) {
        sessionId = ++sessionCount;
        uint256 startTime = block.timestamp;
        sessions[sessionId] = Session({
            name: name,
            startTime: startTime,
            endTime: startTime + duration,
            active: true
        });
        emit SessionCreated(sessionId, name, startTime, startTime + duration);
    }

    function submitScore(
        uint256 sessionId,
        uint256 agentId,
        int256 totalPnl,
        int256 sharpeRatio,
        uint256 winRate,
        uint256 tradeCount
    ) external onlyOwner {
        require(sessions[sessionId].active, "Session not active");

        if (scores[sessionId][agentId].updatedAt == 0) {
            sessionAgents[sessionId].push(agentId);
        }

        scores[sessionId][agentId] = AgentScore({
            agentId: agentId,
            totalPnl: totalPnl,
            sharpeRatio: sharpeRatio,
            winRate: winRate,
            tradeCount: tradeCount,
            updatedAt: block.timestamp
        });

        emit ScoreUpdated(sessionId, agentId, totalPnl, sharpeRatio, winRate);
    }

    function endSession(uint256 sessionId) external onlyOwner {
        require(sessions[sessionId].active, "Session already ended");
        sessions[sessionId].active = false;
        sessions[sessionId].endTime = block.timestamp;
    }

    function getLeaderboard(uint256 sessionId)
        external
        view
        returns (AgentScore[] memory)
    {
        uint256[] memory agentIds = sessionAgents[sessionId];
        AgentScore[] memory board = new AgentScore[](agentIds.length);
        for (uint256 i = 0; i < agentIds.length; i++) {
            board[i] = scores[sessionId][agentIds[i]];
        }
        return board;
    }
}
