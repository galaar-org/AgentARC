// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/HoneypotToken.sol";

/**
 * @title Deploy Honeypot Test Contracts
 * @notice Deploys honeypot token and blacklist manager for AgentArc testing
 *
 * Usage:
 *   # Local deployment (Anvil)
 *   forge script script/DeployHoneypot.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
 *
 *   # Base Sepolia deployment
 *   forge script script/DeployHoneypot.s.sol --rpc-url $BASE_SEPOLIA_RPC --broadcast --verify
 */
contract DeployHoneypotScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr(
            "PRIVATE_KEY",
            uint256(0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b) // Anvil default key
        );
        address deployer = vm.addr(deployerPrivateKey);

        console.log("\n=== Deploying Honeypot Test Contracts ===");
        console.log("Deployer:", deployer);

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy HoneypotToken
        HoneypotToken honeypot = new HoneypotToken();
        console.log("\n1. HoneypotToken deployed at:", address(honeypot));
        console.log("   Name:", honeypot.name());
        console.log("   Symbol:", honeypot.symbol());
        console.log("   Total Supply:", honeypot.totalSupply());
        console.log("   Owner:", honeypot.owner());

        // 2. Deploy BlacklistManager
        BlacklistManager blacklistMgr = new BlacklistManager(address(honeypot));
        console.log("\n2. BlacklistManager deployed at:", address(blacklistMgr));
        console.log("   Honeypot Token:", blacklistMgr.honeypotToken());

        // 3. Connect blacklist manager to honeypot token
        honeypot.__decimals(address(blacklistMgr));
        console.log("\n3. BlacklistManager connected to HoneypotToken");

        // 4. Display honeypot characteristics
        console.log("\n=== Honeypot Characteristics ===");
        console.log("This token demonstrates the following honeypot techniques:");
        console.log("  [1] Fake balanceOf - shows 100x actual balance");
        console.log("  [2] Hidden blacklist - activates after purchase");
        console.log("  [3] Time-locked transfers - never unlocks (max uint256)");
        console.log("  [4] Owner-only selling - only whitelisted can sell");
        console.log("  [5] Fake Transfer events - emits even on failure");
        console.log("  [6] External blacklist call - hidden attack vector");

        console.log("\n=== Testing Instructions ===");
        console.log("Test with AgentArc to verify detection of:");
        console.log("  - No Transfer events on actual transfer attempt");
        console.log("  - Hidden external calls");
        console.log("  - Balance manipulation");
        console.log("  - Transfer restrictions");

        vm.stopBroadcast();

        // Save deployment info
        string memory deploymentInfo = string(abi.encodePacked(
            "HONEYPOT_TOKEN=", vm.toString(address(honeypot)), "\n",
            "BLACKLIST_MANAGER=", vm.toString(address(blacklistMgr)), "\n"
        ));
        vm.writeFile("honeypot-deployment.txt", deploymentInfo);
        console.log("\nDeployment info saved to: honeypot-deployment.txt");
    }
}