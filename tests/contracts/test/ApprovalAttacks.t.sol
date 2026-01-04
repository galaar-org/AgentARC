// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/MockERC20.sol";
import "../src/MaliciousSpender.sol";
import "../src/ApprovalPhishing.sol";
import "../src/WhitelistedContract.sol";

/**
 * @title ApprovalAttacksTest
 * @dev Foundry tests for approval attack scenarios
 *
 * Run with: forge test -vvv
 */
contract ApprovalAttacksTest is Test {
    MockERC20 public token;
    MaliciousSpender public maliciousContract;
    ApprovalPhishing public phishingContract;
    WhitelistedContract public whitelistedContract;

    address public user = address(0x1234);
    address public attacker = address(0x6666);
    address public malicious2 = address(0x7777);

    function setUp() public {
        // Deploy contracts
        token = new MockERC20(1000000 ether);

        vm.prank(attacker);
        maliciousContract = new MaliciousSpender();

        vm.prank(attacker);
        phishingContract = new ApprovalPhishing(address(maliciousContract), malicious2);

        whitelistedContract = new WhitelistedContract();

        // Mint tokens to user
        token.mint(user, 10000 ether);

        console.log("Setup complete:");
        console.log("Token:", address(token));
        console.log("Malicious:", address(maliciousContract));
        console.log("Phishing:", address(phishingContract));
        console.log("Whitelisted:", address(whitelistedContract));
        console.log("User balance:", token.balanceOf(user));
    }

    /**
     * TEST 1: Unlimited Approval to Unknown Address
     * CRITICAL - Should be BLOCKED by PolicyLayer
     */
    function test_UnlimitedApprovalToUnknown() public {
        console.log("\n=== TEST 1: Unlimited Approval to Unknown ===");

        vm.startPrank(user);

        // User approves max uint256 to malicious contract
        uint256 maxApproval = type(uint256).max;
        token.approve(address(maliciousContract), maxApproval);

        console.log("Approved amount:", maxApproval);
        console.log("Allowance:", token.allowance(user, address(maliciousContract)));

        // Verify approval was set
        assertEq(
            token.allowance(user, address(maliciousContract)),
            maxApproval,
            "Approval not set correctly"
        );

        vm.stopPrank();

        // Attacker can now drain all tokens!
        vm.prank(attacker);
        maliciousContract.drainTokens(address(token), user);

        // User lost all tokens
        assertEq(token.balanceOf(user), 0, "User should have 0 tokens");
        console.log("User balance after drain:", token.balanceOf(user));
        console.log("Attacker balance:", token.balanceOf(attacker));

        console.log("Result: CRITICAL - Unlimited approval allowed token drain!");
    }

    /**
     * TEST 2: Approval to Whitelisted Contract
     * Should be ALLOWED by PolicyLayer (if whitelisted)
     */
    function test_UnlimitedApprovalToWhitelisted() public {
        console.log("\n=== TEST 2: Unlimited Approval to Whitelisted ===");

        vm.prank(user);
        token.approve(address(whitelistedContract), type(uint256).max);

        console.log("Approved to whitelisted contract:", address(whitelistedContract));
        console.log("Allowance:", token.allowance(user, address(whitelistedContract)));

        console.log("Result: OK - Approval to trusted DEX/protocol");
    }

    /**
     * TEST 3: Multiple Approvals in Single Transaction
     * Should be detected and BLOCKED by PolicyLayer
     */
    function test_MultipleApprovals() public {
        console.log("\n=== TEST 3: Multiple Approvals in Single Transaction ===");

        // Deploy more tokens for testing
        MockERC20 token2 = new MockERC20(1000000 ether);
        MockERC20 token3 = new MockERC20(1000000 ether);

        token2.mint(user, 5000 ether);
        token3.mint(user, 5000 ether);

        vm.startPrank(user);

        // User calls phishing contract thinking it's an airdrop claim
        // But it actually approves multiple tokens to malicious addresses!
        phishingContract.claimAirdrop(
            address(token),
            address(token2),
            address(token3)
        );

        vm.stopPrank();

        // Check that multiple approvals were made
        console.log("Token1 allowance to malicious1:", token.allowance(user, address(maliciousContract)));
        console.log("Token2 allowance to malicious2:", token2.allowance(user, malicious2));
        console.log("Token3 allowance to attacker:", token3.allowance(user, attacker));

        // All should be max uint256
        assertEq(token.allowance(user, address(maliciousContract)), type(uint256).max);
        assertEq(token2.allowance(user, malicious2), type(uint256).max);
        assertEq(token3.allowance(user, attacker), type(uint256).max);

        console.log("Result: CRITICAL - Multiple unlimited approvals in one tx!");
    }

    /**
     * TEST 4: Limited Approval to Unknown Address
     * Should be ALLOWED (limited amount is safer)
     */
    function test_LimitedApprovalToUnknown() public {
        console.log("\n=== TEST 4: Limited Approval to Unknown ===");

        vm.prank(user);
        uint256 limitedAmount = 100 ether;
        token.approve(address(maliciousContract), limitedAmount);

        console.log("Approved limited amount:", limitedAmount);
        console.log("Allowance:", token.allowance(user, address(maliciousContract)));

        // Attacker can only drain limited amount
        vm.prank(attacker);
        vm.expectRevert("Insufficient allowance");
        maliciousContract.drainTokens(address(token), user);

        console.log("Result: OK - Limited approval limits damage");
    }

    /**
     * TEST 5: Batch Approvals
     * Should detect multiple approvals pattern
     */
    function test_BatchApprovals() public {
        console.log("\n=== TEST 5: Batch Approvals ===");

        MockERC20 token2 = new MockERC20(1000000 ether);
        MockERC20 token3 = new MockERC20(1000000 ether);

        address[] memory tokens = new address[](3);
        tokens[0] = address(token);
        tokens[1] = address(token2);
        tokens[2] = address(token3);

        address[] memory spenders = new address[](3);
        spenders[0] = address(maliciousContract);
        spenders[1] = malicious2;
        spenders[2] = attacker;

        uint256[] memory amounts = new uint256[](3);
        amounts[0] = type(uint256).max;
        amounts[1] = type(uint256).max;
        amounts[2] = type(uint256).max;

        vm.prank(user);
        phishingContract.batchApprove(tokens, spenders, amounts);

        console.log("Batch approved 3 tokens");
        console.log("Result: CRITICAL - Batch unlimited approvals!");
    }

    /**
     * Print transaction calldata for PolicyLayer testing
     */
    function test_PrintCalldataForPolicyLayer() public view {
        console.log("\n=== CALLDATA FOR POLICYLAYER TESTING ===");

        // Unlimited approval calldata
        bytes memory calldataUnlimited = abi.encodeWithSignature(
            "approve(address,uint256)",
            address(maliciousContract),
            type(uint256).max
        );

        console.log("\n1. Unlimited Approval Calldata:");
        console.logBytes(calldataUnlimited);

        // Limited approval calldata
        bytes memory calldataLimited = abi.encodeWithSignature(
            "approve(address,uint256)",
            address(maliciousContract),
            100 ether
        );

        console.log("\n2. Limited Approval Calldata:");
        console.logBytes(calldataLimited);

        // Multiple approvals calldata
        bytes memory calldataMultiple = abi.encodeWithSignature(
            "claimAirdrop(address,address,address)",
            address(token),
            address(token),
            address(token)
        );

        console.log("\n3. Multiple Approvals Calldata:");
        console.logBytes(calldataMultiple);
    }
}