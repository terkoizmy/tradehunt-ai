// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Ownable} from "openzeppelin-contracts/access/Ownable.sol";

contract ReputationFeed is Ownable {
    struct Feedback {
        uint256 agentId;
        address client;
        int256 score;       // scaled by 1e4 (e.g. 85000 = 8.5)
        string tag;         // "pnl", "consistency", "sharpe", "winrate"
        uint256 timestamp;
    }

    mapping(uint256 => Feedback[]) public agentFeedback;
    mapping(uint256 => mapping(string => int256)) public aggregateScores; // agentId => tag => avg * 1e4
    mapping(uint256 => mapping(string => uint256)) public feedbackCounts; // agentId => tag => count

    event FeedbackSubmitted(
        uint256 indexed agentId,
        address indexed client,
        int256 score,
        string tag
    );

    constructor() Ownable(msg.sender) {}

    function submitFeedback(uint256 agentId, int256 score, string calldata tag)
        external
        onlyOwner
    {
        agentFeedback[agentId].push(Feedback({
            agentId: agentId,
            client: msg.sender,
            score: score,
            tag: tag,
            timestamp: block.timestamp
        }));

        uint256 count = feedbackCounts[agentId][tag] + 1;
        feedbackCounts[agentId][tag] = count;
        int256 currentAgg = aggregateScores[agentId][tag];
        aggregateScores[agentId][tag] =
            (currentAgg * int256(int(uint256(count - 1))) + score) / int256(int(uint256(count)));

        emit FeedbackSubmitted(agentId, msg.sender, score, tag);
    }

    function getAgentReputation(uint256 agentId, string[] calldata tags)
        external
        view
        returns (int256[] memory scores_, uint256[] memory counts_)
    {
        scores_ = new int256[](tags.length);
        counts_ = new uint256[](tags.length);
        for (uint256 i = 0; i < tags.length; i++) {
            scores_[i] = aggregateScores[agentId][tags[i]];
            counts_[i] = feedbackCounts[agentId][tags[i]];
        }
    }
}
