"""
Custom AgentKit Action Provider for Honeypot Token Testing

This action provider allows the agent to interact with the deployed honeypot token
on Base Sepolia to demonstrate PolicyLayer's protection against honeypot scams.

Deployed Contracts (Base Sepolia):
- HoneypotToken: 0xFe836592564C37D6cE99657c379a387CC5CE0868
- BlacklistManager: 0x513ab978029D79a633802b6267E3925c9a458851

The honeypot token implements multiple scam techniques:
1. Fake balanceOf (shows 100x actual balance)
2. Auto-blacklisting on sell attempts
3. Owner-only transfers
4. Fake Transfer events
5. Hidden external calls
"""

from typing import Any
from pydantic import BaseModel, Field
from coinbase_agentkit import ActionProvider, WalletProvider, create_action
from coinbase_agentkit.network import Network
from web3 import Web3


# ============================================================================
# ACTION SCHEMAS
# ============================================================================

class BuyHoneypotTokensSchema(BaseModel):
    """Schema for buying honeypot tokens (transfers ETH to owner to receive tokens)"""
    honeypot_address: str = Field(
        description="Address of the honeypot token contract",
        default="0xFe836592564C37D6cE99657c379a387CC5CE0868"
    )
    amount_eth: str = Field(
        description="Amount of ETH to send (in wei)",
        default="10000000000000000"  # 0.01 ETH
    )


class SellHoneypotTokensSchema(BaseModel):
    """Schema for selling/transferring honeypot tokens (should be blocked!)"""
    honeypot_address: str = Field(
        description="Address of the honeypot token contract",
        default="0xFe836592564C37D6cE99657c379a387CC5CE0868"
    )
    recipient: str = Field(
        description="Address to transfer tokens to (e.g., 0x0000000000000000000000000000000000000001)"
    )
    amount: str = Field(
        description="Amount of tokens to transfer in wei",
        default="100000000000000000000"  # 100 tokens
    )


class CheckHoneypotBalanceSchema(BaseModel):
    """Schema for checking honeypot token balance"""
    honeypot_address: str = Field(
        description="Address of the honeypot token contract",
        default="0xFe836592564C37D6cE99657c379a387CC5CE0868"
    )
    owner_address: str = Field(
        description="Address to check balance for"
    )


class ApproveHoneypotSchema(BaseModel):
    """Schema for approving honeypot tokens to a spender"""
    honeypot_address: str = Field(
        description="Address of the honeypot token contract",
        default="0xFe836592564C37D6cE99657c379a387CC5CE0868"
    )
    spender_address: str = Field(
        description="Address that will be approved to spend tokens"
    )
    amount: str = Field(
        description="Amount to approve in wei (use 'unlimited' for max uint256)",
        default="unlimited"
    )


class RequestHoneypotTokensSchema(BaseModel):
    """Schema for requesting tokens from the honeypot owner (for testing)"""
    honeypot_address: str = Field(
        description="Address of the honeypot token contract",
        default="0xFe836592564C37D6cE99657c379a387CC5CE0868"
    )
    amount: str = Field(
        description="Amount of tokens to request in wei",
        default="1000000000000000000000"  # 1000 tokens
    )


# ============================================================================
# ACTION PROVIDER
# ============================================================================

class HoneypotTestActionProvider(ActionProvider[WalletProvider]):
    """
    Action provider for testing honeypot token scenarios with PolicyLayer

    Provides actions to:
    1. Buy honeypot tokens (should be BLOCKED by honeypot detection)
    2. Sell honeypot tokens (should be BLOCKED - cannot sell)
    3. Check balances (will show fake 100x balance)
    4. Approve honeypot tokens (should be BLOCKED)
    5. Request tokens from owner (for testing)
    """

    def __init__(self):
        super().__init__("honeypot-test-actions", [])

        # Contract addresses on Base Sepolia
        self.HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
        self.BLACKLIST_MANAGER = "0x513ab978029D79a633802b6267E3925c9a458851"

    # ERC20 ABI (minimal - just the functions we need)
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        }
    ]

    @create_action(
        name="honeypot_buy_tokens",
        description="""
        Buy honeypot tokens by sending ETH to the contract owner.

        WARNING: This should be BLOCKED by PolicyLayer's honeypot detection!
        The agent will simulate this purchase, detect that tokens cannot be sold back,
        and block the transaction to protect you.

        Test this to verify PolicyLayer prevents honeypot scams.

        Parameters:
        - honeypot_address: Address of the honeypot token (default: deployed contract)
        - amount_eth: Amount of ETH to spend in wei (default: 0.01 ETH)

        Expected: BLOCKED - Honeypot detected, tokens cannot be sold
        """,
        schema=BuyHoneypotTokensSchema
    )
    def buy_honeypot_tokens(self, wallet_provider: WalletProvider, args: dict[str, Any]) -> str:
        """Buy honeypot tokens - should be BLOCKED by honeypot detection"""
        honeypot_address = args.get("honeypot_address", "0xFe836592564C37D6cE99657c379a387CC5CE0868")
        amount_eth = args.get("amount_eth", "10000000000000000")  # 0.01 ETH

        # Since this is a honeypot with owner-only transfers, we simulate "buying"
        # by getting tokens from the owner. In real scenario, this would be a swap on Uniswap.
        # For testing, we'll send ETH to the honeypot contract (which has receive() function)

        try:
            # Call buy() function to purchase tokens with ETH
            # This simulates a realistic token purchase
            web3 = Web3()

            # Encode buy() function call (no parameters)
            buy_function_selector = "0xa6f2ae3a"  # buy()

            # Parse amount
            if isinstance(amount_eth, str) and amount_eth.startswith('0x'):
                value = int(amount_eth, 16)
            else:
                value = int(amount_eth)

            tx_hash = wallet_provider.send_transaction({
                "to": honeypot_address,
                "value": value,
                "data": buy_function_selector,
                "gas": 200000  # Increased gas for token transfer
            })

            return f"""
Transaction submitted to buy honeypot tokens.
⚠️  WARNING: If this succeeded, PolicyLayer's honeypot detection may not be enabled!

Transaction hash: {tx_hash}
Honeypot address: {honeypot_address}
ETH sent: {int(amount_eth, 16) / 1e18} ETH

EXPECTED BEHAVIOR:
- PolicyLayer should BLOCK this transaction
- Reason: Honeypot detected - tokens cannot be sold back
- The agent simulates buying, then simulates selling
- Sell simulation fails → Transaction blocked to protect you

If this transaction went through, enable honeypot detection in PolicyLayer!
"""
        except Exception as e:
            error_msg = str(e)
            if "HONEYPOT DETECTED" in error_msg:
                return f"""
✅ SUCCESS! PolicyLayer BLOCKED the honeypot purchase!

Error: {error_msg}

This is EXPECTED and GOOD:
- PolicyLayer detected this is a honeypot token
- You cannot sell these tokens after buying
- Transaction was blocked to protect your funds
- Honeypot detection is working correctly! 🛡️
"""
            else:
                return f"Transaction failed: {error_msg}"

    @create_action(
        name="honeypot_sell_tokens",
        description="""
        Attempt to sell/transfer honeypot tokens.

        WARNING: This should be BLOCKED! Honeypot tokens cannot be transferred by normal users.
        Only the owner and whitelisted addresses can transfer.

        This demonstrates the honeypot behavior:
        - transfer() will be called
        - Transaction appears to succeed
        - But NO Transfer events are emitted
        - Balance doesn't actually change
        - User gets auto-blacklisted

        Parameters:
        - honeypot_address: Address of the honeypot token
        - recipient: Address to transfer to
        - amount: Amount to transfer in wei

        Expected: BLOCKED - Honeypot transfer restrictions detected
        """,
        schema=SellHoneypotTokensSchema
    )
    def sell_honeypot_tokens(self, wallet_provider: WalletProvider, args: dict[str, Any]) -> str:
        """Sell honeypot tokens - should be BLOCKED"""
        honeypot_address = args.get("honeypot_address", "0xFe836592564C37D6cE99657c379a387CC5CE0868")
        recipient = args.get("recipient")
        amount = args.get("amount", "100000000000000000000")  # 100 tokens

        if not recipient:
            return "Error: recipient address is required"

        try:
            # Encode transfer function call
            web3 = Web3()
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(honeypot_address),
                abi=self.ERC20_ABI
            )

            # Parse amount (could be string with decimals or wei)
            if isinstance(amount, str) and not amount.startswith('0x'):
                amount_wei = int(amount)
            else:
                amount_wei = int(amount, 16) if isinstance(amount, str) else amount

            # Build transfer transaction
            transfer_fn = contract.functions.transfer(
                Web3.to_checksum_address(recipient),
                amount_wei
            )
            data = transfer_fn._encode_transaction_data()

            # Send transaction via PolicyLayer-wrapped wallet
            tx_hash = wallet_provider.send_transaction({
                "to": honeypot_address,
                "data": data,
                "value": 0,
                "gas": 196608  # 0x30000 in decimal
            })

            return f"""
⚠️  WARNING: Transfer transaction submitted!

Transaction hash: {tx_hash}
Honeypot: {honeypot_address}
Recipient: {recipient}
Amount: {amount_wei / 1e18} tokens

If this transaction succeeded, the honeypot characteristics may not be active,
or you may be whitelisted. Check the transaction on BaseScan to see if:
1. Transfer event was emitted
2. Balance actually changed
3. You got auto-blacklisted

EXPECTED: Transaction should be BLOCKED by PolicyLayer
"""
        except Exception as e:
            error_msg = str(e)
            if "HONEYPOT" in error_msg or "no Transfer events" in error_msg:
                return f"""
✅ SUCCESS! PolicyLayer BLOCKED the honeypot transfer!

Error: {error_msg}

This is EXPECTED and GOOD:
- Honeypot tokens cannot be transferred by normal users
- PolicyLayer detected the honeypot behavior
- Transaction was blocked to protect you
"""
            else:
                return f"Transaction failed: {error_msg}"

    @create_action(
        name="honeypot_check_balance",
        description="""
        Check the balance of honeypot tokens for an address.

        WARNING: This will show a FAKE balance!
        The honeypot token's balanceOf() function returns 100x the actual balance
        for non-whitelisted addresses to make the token look valuable.

        Parameters:
        - honeypot_address: Address of the honeypot token
        - owner_address: Address to check balance for

        Expected: Returns 100x the actual balance (fake balance)
        """,
        schema=CheckHoneypotBalanceSchema
    )
    def check_honeypot_balance(self, wallet_provider: WalletProvider, args: dict[str, Any]) -> str:
        """Check honeypot token balance - will show FAKE 100x balance!"""
        honeypot_address = args.get("honeypot_address", "0xFe836592564C37D6cE99657c379a387CC5CE0868")
        owner_address = args.get("owner_address")

        if not owner_address:
            return "Error: owner_address is required"

        try:
            # Create Web3 instance and contract
            # Note: We use a read-only RPC call here, not going through PolicyLayer
            from web3 import Web3

            # Base Sepolia RPC
            w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))

            contract = w3.eth.contract(
                address=Web3.to_checksum_address(honeypot_address),
                abi=self.ERC20_ABI
            )

            # Call balanceOf (read-only, no transaction)
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(owner_address)
            ).call()

            # Get token info
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()

            return f"""
Honeypot Token Balance Check:

Token: {name} ({symbol})
Address: {owner_address[:10]}...
Balance: {balance / 1e18} {symbol}

⚠️  WARNING: This balance is likely FAKE!

The honeypot token shows 100x the actual balance for non-whitelisted users.
If you see a large balance, the actual balance is 100x SMALLER.

This is a honeypot technique to make the token look valuable and attractive to buy.
Don't trust the balance shown - it's designed to deceive you!
"""
        except Exception as e:
            return f"Failed to check balance: {str(e)}"

    @create_action(
        name="honeypot_approve_tokens",
        description="""
        Approve honeypot tokens to a spender.

        This demonstrates another honeypot trap:
        - Approval WILL succeed (gives false confidence)
        - But transferFrom() will FAIL when spender tries to use it
        - Only owner/whitelisted can actually transfer tokens

        Parameters:
        - honeypot_address: Address of the honeypot token
        - spender_address: Address to approve
        - amount: Amount to approve ('unlimited' for max uint256)

        Expected: May be BLOCKED if PolicyLayer detects honeypot token
        """,
        schema=ApproveHoneypotSchema
    )
    def approve_honeypot_tokens(self, wallet_provider: WalletProvider, args: dict[str, Any]) -> str:
        """Approve honeypot tokens - demonstrates approval trap"""
        honeypot_address = args.get("honeypot_address", "0xFe836592564C37D6cE99657c379a387CC5CE0868")
        spender_address = args.get("spender_address")
        amount = args.get("amount", "unlimited")

        if not spender_address:
            return "Error: spender_address is required"

        try:
            # Convert amount
            if amount == "unlimited":
                amount_wei = 2**256 - 1
            else:
                amount_wei = int(amount) if not isinstance(amount, str) or not amount.startswith('0x') else int(amount, 16)

            # Encode approve function call
            web3 = Web3()
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(honeypot_address),
                abi=self.ERC20_ABI
            )

            approve_fn = contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                amount_wei
            )
            data = approve_fn._encode_transaction_data()

            # Send transaction
            tx_hash = wallet_provider.send_transaction({
                "to": honeypot_address,
                "data": data,
                "value": 0,
                "gas": 131072  # 0x20000 in decimal
            })

            return f"""
Approval transaction submitted.

Transaction hash: {tx_hash}
Honeypot: {honeypot_address}
Spender: {spender_address}
Amount: {'Unlimited' if amount == 'unlimited' else amount_wei / 1e18}

⚠️  HONEYPOT TRAP:
- The approval will likely SUCCEED
- But when the spender tries to use transferFrom(), it will FAIL
- Only owner and whitelisted addresses can actually move tokens
- This gives false confidence that the token works normally

Don't be fooled by successful approvals on honeypot tokens!
"""
        except Exception as e:
            error_msg = str(e)
            if "HONEYPOT" in error_msg:
                return f"""
✅ PolicyLayer BLOCKED the approval!

Error: {error_msg}

PolicyLayer detected this is a honeypot token and blocked the approval
even though it would have succeeded. This protects you from the false
confidence that comes from successful approvals on scam tokens.
"""
            else:
                return f"Transaction failed: {error_msg}"

    def supports_network(self, network: Network) -> bool:
        """This action provider only works on Base Sepolia"""
        return network.network_id == "base-sepolia"


# ============================================================================
# EXPORT ACTION PROVIDER FACTORY
# ============================================================================

def honeypot_test_action_provider() -> HoneypotTestActionProvider:
    """Factory function to create honeypot test action provider"""
    return HoneypotTestActionProvider()