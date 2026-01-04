// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title WhitelistedContract
 * @dev Legitimate contract that should be whitelisted
 *
 * TEST SCENARIO: Unlimited Approval to WHITELISTED Address
 * - User approves max uint256 to this whitelisted contract
 * - This is a known DEX/protocol that user trusts
 * - SHOULD BE ALLOWED by PolicyLayer (if whitelisted in policy.yaml)
 */
contract WhitelistedContract {
    string public name = "Legitimate DEX";

    event ApprovalReceived(address indexed token, address indexed user, uint256 amount);

    /**
     * @dev Legitimate swap function that needs approval
     */
    function swap(address tokenIn, address tokenOut, uint256 amountIn) external pure returns (bool) {
        // Legitimate swap logic would go here
        // For testing, we just validate the call
        require(tokenIn != address(0), "Invalid token");
        require(tokenOut != address(0), "Invalid token");
        require(amountIn > 0, "Invalid amount");
        return true;
    }
}