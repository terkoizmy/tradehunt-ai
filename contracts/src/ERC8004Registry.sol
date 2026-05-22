// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

// Minimal ERC-8004 Identity Registry for Mantle Sepolia hackathon deployment
contract ERC8004Registry {
    uint256 public nextAgentId = 1;

    mapping(uint256 => address) public ownerOf;
    mapping(uint256 => string) public agentURI;
    mapping(address => uint256) public balanceOf;

    event AgentRegistered(uint256 indexed agentId, address indexed owner, string uri);
    event AgentURIUpdated(uint256 indexed agentId, string newURI);

    function registerAgent(address agent, string calldata uri) external returns (uint256 agentId) {
        agentId = nextAgentId++;
        ownerOf[agentId] = agent;
        agentURI[agentId] = uri;
        balanceOf[agent]++;
        emit AgentRegistered(agentId, agent, uri);
    }

    function setAgentURI(uint256 agentId, string calldata newURI) external {
        require(msg.sender == ownerOf[agentId], "Not owner");
        agentURI[agentId] = newURI;
        emit AgentURIUpdated(agentId, newURI);
    }
}
