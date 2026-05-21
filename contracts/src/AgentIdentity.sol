// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

interface IERC8004IdentityRegistry {
    function registerAgent(address agent, string calldata agentURI) external returns (uint256 agentId);
    function setAgentURI(uint256 agentId, string calldata newURI) external;
    function ownerOf(uint256 agentId) external view returns (address);
    function balanceOf(address owner) external view returns (uint256);
}

contract AgentIdentity {
    IERC8004IdentityRegistry public immutable registry;

    event AgentRegistered(uint256 indexed agentId, address indexed owner, string agentURI);

    constructor(address _registry) {
        registry = IERC8004IdentityRegistry(_registry);
    }

    function registerAgent(string calldata name, string calldata agentURI)
        external
        returns (uint256 agentId)
    {
        agentId = registry.registerAgent(msg.sender, agentURI);
        emit AgentRegistered(agentId, msg.sender, agentURI);
    }

    function updateAgentURI(uint256 agentId, string calldata newURI) external {
        require(
            registry.ownerOf(agentId) == msg.sender,
            "Not agent owner"
        );
        registry.setAgentURI(agentId, newURI);
    }
}
