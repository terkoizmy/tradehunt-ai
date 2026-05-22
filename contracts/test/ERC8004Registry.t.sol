// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Test} from "forge-std/Test.sol";
import {ERC8004Registry} from "../src/ERC8004Registry.sol";

contract ERC8004RegistryTest is Test {
    ERC8004Registry public registry;
    address public user = address(0x2);

    function setUp() public {
        registry = new ERC8004Registry();
    }

    function test_RegisterAgent() public {
        uint256 agentId = registry.registerAgent(user, "ipfs://QmTest");
        assertEq(agentId, 1);
        assertEq(registry.ownerOf(agentId), user);
        assertEq(registry.agentURI(agentId), "ipfs://QmTest");
        assertEq(registry.balanceOf(user), 1);
    }

    function test_SetAgentURI() public {
        uint256 agentId = registry.registerAgent(user, "ipfs://QmTest");

        vm.prank(user);
        registry.setAgentURI(agentId, "ipfs://QmUpdated");

        assertEq(registry.agentURI(agentId), "ipfs://QmUpdated");
    }

    function test_RevertIfNonOwnerSetsURI() public {
        uint256 agentId = registry.registerAgent(user, "ipfs://QmTest");

        address other = address(0x3);
        vm.prank(other);
        vm.expectRevert("Not owner");
        registry.setAgentURI(agentId, "ipfs://QmHacker");
    }

    function test_MultipleAgentsIncrementIds() public {
        uint256 id1 = registry.registerAgent(user, "uri1");
        uint256 id2 = registry.registerAgent(address(0x3), "uri2");
        assertEq(id1, 1);
        assertEq(id2, 2);
    }
}
