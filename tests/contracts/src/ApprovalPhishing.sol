
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IERC20.sol";

/**
 * @title ApprovalPhishing
 * @dev Contract that tricks users into multiple approvals
 *
 * TEST SCENARIO 2 & 3: Multiple Approvals + Approvals to Unknown
 * - Single transaction requests multiple token approvals
 * - All approvals go to unknown/malicious addresses
 * - SHOULD BE BLOCKED by PolicyLayer
 */
contract ApprovalPhishing {
    address public maliciousContract1;
    address public maliciousContract2;
    address public attacker;

    event MultipleApprovalsRequested(address indexed victim, uint256 count);

    constructor(address _malicious1, address _malicious2) {
        maliciousContract1 = _malicious1;
        maliciousContract2 = _malicious2;
        attacker = msg.sender;
    }

    /**
     * @dev Innocent-looking function that actually requests multiple approvals
     * Simulates a phishing attack where user thinks they're doing one thing
     * but actually approving multiple malicious contracts
     */
    function claimAirdrop(
        address token1,
        address token2,
        address token3
    ) external {
        // Request unlimited approvals for multiple tokens to malicious addresses
        IERC20(token1).approve(maliciousContract1, type(uint256).max);
        IERC20(token2).approve(maliciousContract2, type(uint256).max);
        IERC20(token3).approve(attacker, type(uint256).max);

        emit MultipleApprovalsRequested(msg.sender, 3);
    }

    /**
     * @dev Batch approval function - common pattern but dangerous
     * TEST: Multiple approvals in single transaction
     */
    function batchApprove(
        address[] calldata tokens,
        address[] calldata spenders,
        uint256[] calldata amounts
    ) external {
        require(tokens.length == spenders.length, "Length mismatch");
        require(tokens.length == amounts.length, "Length mismatch");

        for (uint256 i = 0; i < tokens.length; i++) {
            IERC20(tokens[i]).approve(spenders[i], amounts[i]);
        }

        emit MultipleApprovalsRequested(msg.sender, tokens.length);
    }
}