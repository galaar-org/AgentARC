// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/HoneypotToken.sol";

/**
 * @title Honeypot Token Tests
 * @notice Tests to verify honeypot behaviors work correctly
 */
contract HoneypotTokenTest is Test {
    HoneypotToken public honeypot;
    BlacklistManager public blacklistMgr;

    address public owner;
    address public alice;
    address public bob;

    function setUp() public {
        owner = address(this);
        alice = address(0x1);
        bob = address(0x2);

        // Deploy contracts
        honeypot = new HoneypotToken();
        blacklistMgr = new BlacklistManager(address(honeypot));

        // Connect blacklist manager
        honeypot.__decimals(address(blacklistMgr));

        // Give Alice some tokens (simulate liquidity pool)
        vm.prank(owner);
        honeypot.transfer(alice, 1000 * 10**18);
    }

    /// ============ HONEYPOT BEHAVIOR TESTS ============

    /**
     * @dev TEST 1: Fake balanceOf shows inflated balance
     * Expected: Shows 100x actual balance for non-whitelisted accounts
     */
    function test_FakeBalanceOf() public {
        uint256 actualBalance = 1000 * 10**18;

        // Alice's actual balance
        vm.prank(owner);
        honeypot.setWhitelist(alice, true);
        uint256 whitelistedBalance = honeypot.balanceOf(alice);
        assertEq(whitelistedBalance, actualBalance);

        // Bob's fake balance (100x)
        vm.prank(owner);
        honeypot.setWhitelist(alice, false);
        uint256 fakeBalance = honeypot.balanceOf(alice);
        assertEq(fakeBalance, actualBalance * 100, "Should show 100x fake balance");

        console.log("TEST 1: Fake balanceOf");
        console.log("  Actual balance:", actualBalance);
        console.log("  Fake balance shown:", fakeBalance);
        console.log("  Result: HONEYPOT - Shows 100x inflated balance!");
    }

    /**
     * @dev TEST 2: Owner can transfer, non-whitelisted cannot
     * Expected: Owner succeeds, Alice fails silently
     */
    function test_OnlyOwnerCanSell() public {
        // Owner can transfer
        vm.prank(owner);
        bool ownerSuccess = honeypot.transfer(bob, 100 * 10**18);
        assertTrue(ownerSuccess, "Owner should be able to transfer");

        // Alice cannot transfer (not whitelisted)
        vm.prank(alice);
        bool aliceSuccess = honeypot.transfer(bob, 100 * 10**18);
        // Returns false but emits Transfer event (deceptive!)
        assertFalse(aliceSuccess, "Alice should fail to transfer");

        console.log("\nTEST 2: Owner-only selling");
        console.log("  Owner transfer: SUCCESS");
        console.log("  Alice transfer: FAIL (emits fake Transfer event)");
        console.log("  Result: HONEYPOT - Only owner can sell!");
    }

    /**
     * @dev TEST 3: No Transfer events emitted on failed transfer
     * Expected: Event emitted but no actual token movement
     */
    function test_NoTransferEventsOnFail() public {
        uint256 bobBalanceBefore = honeypot.balanceOf(bob);
        uint256 aliceBalanceBefore = honeypot.balanceOf(alice);

        // Alice tries to transfer
        vm.prank(alice);
        honeypot.transfer(bob, 100 * 10**18);

        // Balances should NOT change
        uint256 bobBalanceAfter = honeypot.balanceOf(bob);
        uint256 aliceBalanceAfter = honeypot.balanceOf(alice);

        // Note: fake balances stay same because actual balances didn't change
        console.log("\nTEST 3: Fake Transfer events");
        console.log("  Bob balance before:", bobBalanceBefore);
        console.log("  Bob balance after:", bobBalanceAfter);
        console.log("  Change:", bobBalanceAfter - bobBalanceBefore);
        console.log("  Result: HONEYPOT - No actual token movement!");
    }

    /**
     * @dev TEST 4: Non-whitelisted users can't transfer (blacklist + time lock)
     * Expected: Non-whitelisted users blocked immediately
     * Note: Time lock check is unreachable because blacklist check comes first
     */
    function test_NonWhitelistedCantTransfer() public {
        // Give Bob some tokens (owner can transfer)
        vm.prank(owner);
        honeypot.transfer(bob, 100 * 10**18);

        // Bob tries to transfer immediately - will be auto-blacklisted
        vm.prank(bob);
        bool success = honeypot.transfer(alice, 50 * 10**18);
        assertFalse(success, "Non-whitelisted transfer should fail");

        // Bob is now blacklisted
        assertTrue(honeypot.isBlacklisted(bob), "Bob should be blacklisted");

        // Even after 1 year, still can't transfer (blacklisted)
        vm.warp(block.timestamp + 365 days);
        vm.prank(bob);
        bool success2 = honeypot.transfer(alice, 50 * 10**18);
        assertFalse(success2, "Transfer should still fail after time");

        console.log("\nTEST 4: Non-whitelisted restrictions");
        console.log("  Initial transfer: FAIL (auto-blacklisted)");
        console.log("  Transfer after 1 year: STILL FAIL");
        console.log("  Result: HONEYPOT - Permanent restrictions!");
    }

    /**
     * @dev TEST 5: Auto-blacklisting on transfer attempt
     * Expected: Alice gets blacklisted when trying to sell
     */
    function test_AutoBlacklistOnSell() public {
        // Alice is not blacklisted initially
        assertFalse(honeypot.isBlacklisted(alice));

        // Alice tries to transfer (this will auto-blacklist her)
        vm.prank(alice);
        honeypot.transfer(bob, 100 * 10**18);

        // Alice is now blacklisted
        assertTrue(honeypot.isBlacklisted(alice), "Alice should be blacklisted");

        console.log("\nTEST 5: Auto-blacklist");
        console.log("  Alice blacklisted before transfer: false");
        console.log("  Alice blacklisted after transfer: true");
        console.log("  Result: HONEYPOT - Auto-blacklists sellers!");
    }

    /**
     * @dev TEST 6: Whitelisted addresses can transfer normally
     * Expected: Whitelisted users bypass all restrictions
     */
    function test_WhitelistedCanTransfer() public {
        // Whitelist Alice
        vm.prank(owner);
        honeypot.setWhitelist(alice, true);

        // Alice can now transfer
        vm.prank(alice);
        bool success = honeypot.transfer(bob, 100 * 10**18);
        assertTrue(success, "Whitelisted should be able to transfer");

        console.log("\nTEST 6: Whitelist bypass");
        console.log("  Whitelisted can transfer: YES");
        console.log("  Result: Only insiders can sell!");
    }

    /**
     * @dev TEST 7: Approve works normally (gives false confidence)
     * Expected: Approval succeeds but transferFrom will fail
     */
    function test_ApproveWorksButTransferFromFails() public {
        // Alice approves Bob
        vm.prank(alice);
        bool approveSuccess = honeypot.approve(bob, 500 * 10**18);
        assertTrue(approveSuccess, "Approve should succeed");

        // Bob tries to transferFrom
        vm.prank(bob);
        bool transferSuccess = honeypot.transferFrom(alice, bob, 100 * 10**18);
        assertFalse(transferSuccess, "TransferFrom should fail for non-whitelisted");

        console.log("\nTEST 7: Approve trap");
        console.log("  Approve succeeds: YES");
        console.log("  TransferFrom succeeds: NO");
        console.log("  Result: HONEYPOT - Approval works but transfer doesn't!");
    }

    /// ============ SUMMARY TEST ============

    function test_HoneypotSummary() public {
        console.log("\n========================================");
        console.log("HONEYPOT TOKEN BEHAVIOR SUMMARY");
        console.log("========================================");
        console.log("\nHoneypot Techniques Implemented:");
        console.log("  [1] Fake balanceOf (100x inflation)");
        console.log("  [2] Owner-only selling");
        console.log("  [3] Fake Transfer events");
        console.log("  [4] Permanent time lock (max uint256)");
        console.log("  [5] Auto-blacklisting");
        console.log("  [6] External blacklist manager");
        console.log("  [7] Whitelist bypass for insiders");
        console.log("\nAgentArc Should Detect:");
        console.log("  - No Transfer events on actual transfer");
        console.log("  - External calls to unknown contract");
        console.log("  - Transfer restrictions");
        console.log("  - Balance inconsistencies");
        console.log("========================================\n");
    }
}