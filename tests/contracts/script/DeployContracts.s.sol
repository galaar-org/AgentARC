// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/MockERC20.sol";
import "../src/MaliciousSpender.sol";
import "../src/ApprovalPhishing.sol";
import "../src/WhitelistedContract.sol";

/**
 * @title DeployContracts
 * @dev Deploy test contracts for PolicyLayer approval testing
 *
 * Usage:
 *   # Start Anvil (local blockchain)
 *   anvil
 *
 *   # Deploy contracts
 *   forge script script/DeployContracts.s.sol:DeployContracts --rpc-url http://127.0.0.1:8545 --broadcast
 *
 *   # Or deploy with private key
 *   forge script script/DeployContracts.s.sol:DeployContracts --rpc-url http://127.0.0.1:8545 --private-key $PRIVATE_KEY --broadcast
 */
contract DeployContracts is Script {
    function run() public {
        // Get deployer from environment or use default Anvil account
        uint256 deployerPrivateKey = vm.envOr(
            "PRIVATE_KEY",
            uint256(0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b) // Anvil default key
        );

        vm.startBroadcast(deployerPrivateKey);

        console.log("=== Deploying Approval Test Contracts ===");
        console.log("Deployer:", vm.addr(deployerPrivateKey));

        // Deploy MockERC20 token
        MockERC20 token = new MockERC20(1000000 ether);
        console.log("\n1. MockERC20 deployed at:", address(token));
        console.log("   Total supply:", token.totalSupply());

        // Deploy MaliciousSpender
        MaliciousSpender maliciousContract = new MaliciousSpender();
        console.log("\n2. MaliciousSpender deployed at:", address(maliciousContract));
        console.log("   Attacker:", maliciousContract.attacker());

        // Deploy second malicious address for multi-approval tests
        address malicious2 = address(0x7777777777777777777777777777777777777777);

        // Deploy ApprovalPhishing
        ApprovalPhishing phishingContract = new ApprovalPhishing(
            address(maliciousContract),
            malicious2
        );
        console.log("\n3. ApprovalPhishing deployed at:", address(phishingContract));
        console.log("   Malicious target 1:", phishingContract.maliciousContract1());
        console.log("   Malicious target 2:", phishingContract.maliciousContract2());

        // Deploy WhitelistedContract
        WhitelistedContract whitelistedContract = new WhitelistedContract();
        console.log("\n4. WhitelistedContract deployed at:", address(whitelistedContract));
        console.log("   Name:", whitelistedContract.name());

        // Mint tokens to deployer for testing
        address deployer = vm.addr(deployerPrivateKey);
        token.mint(deployer, 10000 ether);
        console.log("\n=== Setup Complete ===");
        console.log("Minted 10000 MOCK tokens to deployer");
        console.log("Deployer balance:", token.balanceOf(deployer) / 1 ether, "MOCK");

        vm.stopBroadcast();

        // Save deployment addresses to file for Python integration
        string memory deploymentInfo = string.concat(
            "{\n",
            '  "token": "', vm.toString(address(token)), '",\n',
            '  "malicious": "', vm.toString(address(maliciousContract)), '",\n',
            '  "phishing": "', vm.toString(address(phishingContract)), '",\n',
            '  "whitelisted": "', vm.toString(address(whitelistedContract)), '",\n',
            '  "deployer": "', vm.toString(deployer), '",\n',
            '  "chainId": ', vm.toString(block.chainid), '\n',
            "}\n"
        );

        vm.writeFile("deployments.json", deploymentInfo);
        console.log("\nDeployment addresses saved to deployments.json");

        // Print instructions for PolicyLayer testing
        console.log("\n=== Next Steps for PolicyLayer Testing ===");
        console.log("\n1. Add whitelisted contract to policy_v2.yaml:");
        console.log("   address_allowlist:");
        console.log("     allowed_addresses:");
        console.log("       -", vm.toString(address(whitelistedContract)));
        console.log("\n2. Run Python integration tests:");
        console.log("   python tests/test_approval_integration.py");
        console.log("\n3. Test scenarios:");
        console.log("   - Unlimited approval to", vm.toString(address(maliciousContract)), "(should BLOCK)");
        console.log("   - Unlimited approval to", vm.toString(address(whitelistedContract)), "(should ALLOW)");
        console.log("   - Limited approval to", vm.toString(address(maliciousContract)), "(should ALLOW)");
    }
}
