// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "forge-std/Test.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";

// Minimal mock ERC-8004 registry for testing
contract MockERC8004Registry {
    mapping(uint256 => address) public owners;
    mapping(uint256 => string) public uris;
    uint256 public nextId = 1;

    function registerAgent(address agent, string calldata agentURI) external returns (uint256 agentId) {
        agentId = nextId++;
        owners[agentId] = agent;
        uris[agentId] = agentURI;
    }

    function setAgentURI(uint256 agentId, string calldata newURI) external {
        uris[agentId] = newURI;
    }

    function ownerOf(uint256 agentId) external view returns (address) {
        return owners[agentId];
    }

    function balanceOf(address) external pure returns (uint256) {
        return 1;
    }
}

contract AgentIdentityTest is Test {
    AgentIdentity public identity;
    MockERC8004Registry public mockRegistry;
    address public user = address(0x2);

    function setUp() public {
        mockRegistry = new MockERC8004Registry();
        identity = new AgentIdentity(address(mockRegistry));
    }

    function test_RegisterAgent() public {
        vm.prank(user);
        uint256 agentId = identity.registerAgent("Alpha Hunter", "ipfs://QmTest");

        assertEq(agentId, 1);
        assertEq(mockRegistry.ownerOf(agentId), user);
        assertEq(mockRegistry.uris(agentId), "ipfs://QmTest");
        assertEq(identity.agentName(agentId), "Alpha Hunter");
    }

    function test_UpdateAgentURI() public {
        vm.prank(user);
        uint256 agentId = identity.registerAgent("Alpha Hunter", "ipfs://QmTest");

        vm.prank(user);
        identity.updateAgentURI(agentId, "ipfs://QmUpdated");

        assertEq(mockRegistry.uris(agentId), "ipfs://QmUpdated");
    }

    function test_RevertIfNonOwnerUpdatesURI() public {
        vm.prank(user);
        uint256 agentId = identity.registerAgent("Alpha Hunter", "ipfs://QmTest");

        address other = address(0x3);
        vm.prank(other);
        vm.expectRevert("Not agent owner");
        identity.updateAgentURI(agentId, "ipfs://QmHacker");
    }

    function test_EmitEventOnRegister() public {
        vm.prank(user);
        vm.expectEmit(true, true, false, true);
        emit AgentIdentity.AgentRegistered(1, user, "Alpha Hunter", "ipfs://QmTest");
        identity.registerAgent("Alpha Hunter", "ipfs://QmTest");
    }
}
