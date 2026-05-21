// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Script} from "forge-std/Script.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";
import {TradeRegistry} from "../src/TradeRegistry.sol";
import {ArenaLeaderboard} from "../src/ArenaLeaderboard.sol";
import {ReputationFeed} from "../src/ReputationFeed.sol";

contract Deploy is Script {
    // ERC-8004 Identity Registry on Mantle Sepolia
    // Address to be confirmed from Mantle docs — update before deploying
    address constant ERC8004_IDENTITY_REGISTRY = address(0); // TODO: update

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        AgentIdentity agentIdentity = new AgentIdentity(ERC8004_IDENTITY_REGISTRY);
        console.log("AgentIdentity deployed at:", address(agentIdentity));

        TradeRegistry tradeRegistry = new TradeRegistry();
        console.log("TradeRegistry deployed at:", address(tradeRegistry));

        ArenaLeaderboard arenaLeaderboard = new ArenaLeaderboard();
        console.log("ArenaLeaderboard deployed at:", address(arenaLeaderboard));

        ReputationFeed reputationFeed = new ReputationFeed();
        console.log("ReputationFeed deployed at:", address(reputationFeed));

        vm.stopBroadcast();
    }
}
