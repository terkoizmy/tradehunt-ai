// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {ERC8004Registry} from "../src/ERC8004Registry.sol";
import {AgentIdentity} from "../src/AgentIdentity.sol";
import {TradeRegistry} from "../src/TradeRegistry.sol";
import {ArenaLeaderboard} from "../src/ArenaLeaderboard.sol";
import {ReputationFeed} from "../src/ReputationFeed.sol";

contract Deploy is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        ERC8004Registry registry = new ERC8004Registry();
        console.log("ERC8004Registry deployed at:", address(registry));

        AgentIdentity agentIdentity = new AgentIdentity(address(registry));
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
