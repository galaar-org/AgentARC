"""
Custom AgentKit Action Provider for Approval Attack Testing

This action provider allows the agent to interact with deployed test contracts
on Base Sepolia to demonstrate PolicyLayer's protection against approval attacks.

Deployed Contracts (Base Sepolia):
- MockERC20: 0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4
- MaliciousSpender: 0xDc569c33c8C4760E2cB317FBe7B95e4b0318ed6E
- ApprovalPhishing: 0xfb9256a0eA9d0313b3BafAE0c80A19F44046aA1a
- WhitelistedContract: (add your address)
"""

from typing import Any
from pydantic import BaseModel, Field
from coinbase_agentkit import ActionProvider, WalletProvider, create_action
from coinbase_agentkit.network import Network
from web3 import Web3


# ============================================================================
# ACTION SCHEMAS
# ============================================================================

class ApproveTokenSchema(BaseModel):
    """Schema for token approval action"""
    token_address: str = Field(
        description="Address of the ERC20 token contract",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )
    spender_address: str = Field(
        description="Address that will be approved to spend tokens (malicious, whitelisted, or other)"
    )
    amount: str = Field(
        description="Amount to approve in wei (use 'unlimited' for max uint256)",
        default="unlimited"
    )


class ClaimAirdropSchema(BaseModel):
    """Schema for phishing airdrop claim (triggers multiple approvals)"""
    phishing_contract: str = Field(
        description="Address of the phishing contract",
        default="0xfb9256a0eA9d0313b3BafAE0c80A19F44046aA1a"
    )
    token1: str = Field(
        description="First token address",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )
    token2: str = Field(
        description="Second token address",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )
    token3: str = Field(
        description="Third token address",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )


class CheckAllowanceSchema(BaseModel):
    """Schema for checking token allowance"""
    token_address: str = Field(
        description="Address of the ERC20 token contract",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )
    owner_address: str = Field(
        description="Address of the token owner"
    )
    spender_address: str = Field(
        description="Address of the spender to check allowance for"
    )


class MintTestTokensSchema(BaseModel):
    """Schema for minting test tokens"""
    token_address: str = Field(
        description="Address of the MockERC20 token contract",
        default="0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
    )
    recipient: str = Field(
        description="Address to receive the minted tokens"
    )
    amount: str = Field(
        description="Amount to mint in wei (e.g., '1000000000000000000' for 1 token)",
        default="1000000000000000000"
    )


# ============================================================================
# ACTION PROVIDER
# ============================================================================

class ApprovalTestActionProvider(ActionProvider[WalletProvider]):
    """
    Action provider for testing approval attack scenarios with PolicyLayer

    Provides actions to:
    1. Approve tokens (safe and malicious scenarios)
    2. Trigger phishing attacks (multiple approvals)
    3. Check allowances
    4. Mint test tokens

    All actions are protected by PolicyLayer if enabled.
    """

    def __init__(self):
        super().__init__("approval-test-actions", [])

        # Contract addresses on Base Sepolia
        self.MOCK_TOKEN = "0x579342bCd8A72B6f5C5231ed3Ab84f92C9Ce79b4"
        self.MALICIOUS_SPENDER = "0xDc569c33c8C4760E2cB317FBe7B95e4b0318ed6E"
        self.PHISHING_CONTRACT = "0xfb9256a0eA9d0313b3BafAE0c80A19F44046aA1a"
        self.MAX_UINT256 = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        # ERC20 ABI snippets
        self.ERC20_ABI = [
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
                "constant": False,
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "mint",
                "outputs": [],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]

        # Phishing contract ABI
        self.PHISHING_ABI = [
            {
                "constant": False,
                "inputs": [
                    {"name": "token1", "type": "address"},
                    {"name": "token2", "type": "address"},
                    {"name": "token3", "type": "address"}
                ],
                "name": "claimAirdrop",
                "outputs": [],
                "type": "function"
            }
        ]

    @create_action(
        name="test_approve_tokens",
        description=(
            "Test token approval scenarios (safe and malicious). Use this when user asks to approve tokens, "
            "test approvals, or approve unlimited tokens. This demonstrates PolicyLayer protection. "
            "Required: spender_address. Optional: token_address (default: test token), "
            "amount (default: 'unlimited'). PolicyLayer will block malicious unlimited approvals."
        ),
        schema=ApproveTokenSchema
    )
    def approve_tokens(
        self,
        wallet_provider: WalletProvider,
        args: dict[str, Any]
    ) -> str:
        """
        Approve tokens for spending

        This action demonstrates how PolicyLayer protects against:
        - Unlimited approvals to unknown addresses (BLOCKED)
        - Multiple approvals in one transaction (BLOCKED)
        - Approvals to whitelisted addresses (ALLOWED)
        """
        token_address = args.get("token_address", self.MOCK_TOKEN)
        spender_address = args["spender_address"]
        amount = args.get("amount", "unlimited")

        # Convert amount
        if amount == "unlimited":
            amount_wei = self.MAX_UINT256
            amount_display = "UNLIMITED (max uint256)"
        else:
            amount_wei = str(amount)
            amount_display = f"{amount} wei"

        print(f"\n{'='*70}")
        print(f"🔒 APPROVAL TEST ACTION")
        print(f"{'='*70}")
        print(f"Token:   {token_address}")
        print(f"Spender: {spender_address}")
        print(f"Amount:  {amount_display}")
        print(f"\n⚠️  PolicyLayer is analyzing this approval...")
        print(f"{'='*70}\n")

        try:
            # Encode the approve function call using Web3
            web3 = Web3()
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )
            # Use the functions interface to encode the transaction data
            approve_fn = contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                int(amount_wei, 16)
            )
            data = approve_fn._encode_transaction_data()

            # Send the transaction
            tx_hash = wallet_provider.send_transaction({
                "to": Web3.to_checksum_address(token_address),
                "data": data,
                "value": 0
            })

            return (
                f"✅ Approval transaction submitted!\n"
                f"Transaction hash: {tx_hash}\n"
                f"Approved {amount_display} of token {token_address[:10]}... to {spender_address[:10]}...\n"
                f"\n💡 If PolicyLayer blocked this, it detected a malicious pattern!"
            )

        except Exception as e:
            if "PolicyLayer" in str(e) or "blocked" in str(e).lower():
                return (
                    f"🛡️ BLOCKED BY POLICYLAYER!\n\n"
                    f"Reason: {str(e)}\n\n"
                    f"This approval was blocked because it matched a malicious pattern.\n"
                    f"PolicyLayer successfully protected your wallet from a potential attack!"
                )
            else:
                return f"❌ Transaction failed: {str(e)}"

    @create_action(
        name="test_claim_airdrop",
        description=(
            "Test phishing airdrop attack that triggers multiple malicious token approvals. "
            "Use this when user asks to 'claim airdrop', 'test phishing', or 'try fake airdrop'. "
            "PolicyLayer should BLOCK this to demonstrate protection against multi-approval attacks. "
            "Optional: phishing_contract (default: deployed test contract)."
        ),
        schema=ClaimAirdropSchema
    )
    def claim_phishing_airdrop(
        self,
        wallet_provider: WalletProvider,
        args: dict[str, Any]
    ) -> str:
        """
        Trigger a phishing attack that requests multiple approvals

        This demonstrates PolicyLayer blocking multiple approvals in one transaction
        """
        phishing_contract = args.get("phishing_contract", self.PHISHING_CONTRACT)
        token1 = args.get("token1", self.MOCK_TOKEN)
        token2 = args.get("token2", self.MOCK_TOKEN)
        token3 = args.get("token3", self.MOCK_TOKEN)

        print(f"\n{'='*70}")
        print(f"🎣 PHISHING ATTACK TEST")
        print(f"{'='*70}")
        print(f"Calling 'claimAirdrop' on phishing contract...")
        print(f"This will attempt to approve 3 tokens to malicious addresses!")
        print(f"\n⚠️  PolicyLayer should BLOCK this transaction!")
        print(f"{'='*70}\n")

        try:
            # Encode the claimAirdrop function call using Web3
            web3 = Web3()
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(phishing_contract),
                abi=self.PHISHING_ABI
            )
            # Use the functions interface to encode the transaction data
            claim_fn = contract.functions.claimAirdrop(
                Web3.to_checksum_address(token1),
                Web3.to_checksum_address(token2),
                Web3.to_checksum_address(token3)
            )
            data = claim_fn._encode_transaction_data()

            # Send the transaction
            tx_hash = wallet_provider.send_transaction({
                "to": Web3.to_checksum_address(phishing_contract),
                "data": data,
                "value": 0
            })

            return (
                f"⚠️ WARNING: Transaction was NOT blocked!\n"
                f"Transaction hash: {tx_hash}\n"
                f"This phishing attack succeeded. You may need to enable LLM validation in policy.yaml."
            )

        except Exception as e:
            if "PolicyLayer" in str(e) or "blocked" in str(e).lower():
                return (
                    f"🛡️ SUCCESS! BLOCKED BY POLICYLAYER!\n\n"
                    f"Reason: {str(e)}\n\n"
                    f"PolicyLayer detected and blocked the phishing attack!\n"
                    f"This transaction would have approved 3 unlimited token allowances to malicious addresses.\n"
                    f"Your wallet is safe!"
                )
            else:
                return f"❌ Transaction failed: {str(e)}"

    @create_action(
        name="test_check_allowance",
        description=(
            "Check token allowance to verify how much a spender can spend on behalf of an owner. "
            "Use this when user asks to 'check allowance', 'verify approval', or 'check tokens approved'. "
            "Required: owner_address, spender_address. Optional: token_address (default: test token). "
            "This is a read-only operation that's always safe."
        ),
        schema=CheckAllowanceSchema
    )
    def check_allowance(
        self,
        wallet_provider: WalletProvider,
        args: dict[str, Any]
    ) -> str:
        """Check token allowance (read-only operation)"""
        token_address = args.get("token_address", self.MOCK_TOKEN)
        owner_address = args["owner_address"]
        spender_address = args["spender_address"]

        try:
            # Read the allowance using wallet provider's read_contract method
            allowance = wallet_provider.read_contract(
                contract_address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI,
                function_name="allowance",
                args=[
                    Web3.to_checksum_address(owner_address),
                    Web3.to_checksum_address(spender_address)
                ]
            )

            allowance = int(allowance)

            if allowance >= int(self.MAX_UINT256, 16) * 0.9:
                allowance_display = "UNLIMITED (max uint256)"
                warning = "⚠️ WARNING: This is an unlimited approval!"
            else:
                allowance_display = f"{allowance} wei ({allowance / 1e18:.4f} tokens)"
                warning = ""

            return (
                f"Token Allowance Information:\n"
                f"Token:   {token_address[:10]}...\n"
                f"Owner:   {owner_address[:10]}...\n"
                f"Spender: {spender_address[:10]}...\n"
                f"Allowance: {allowance_display}\n"
                f"{warning}"
            )

        except Exception as e:
            return f"❌ Failed to check allowance: {str(e)}"

    @create_action(
        name="test_mint_tokens",
        description=(
            "Mint test tokens to an address for testing. Use this when user asks to 'mint tokens', "
            "'get test tokens', or 'create tokens'. Only works if you're the contract deployer. "
            "Required: recipient. Optional: token_address (default: test token), "
            "amount (default: 1 token = 1000000000000000000 wei)."
        ),
        schema=MintTestTokensSchema
    )
    def mint_test_tokens(
        self,
        wallet_provider: WalletProvider,
        args: dict[str, Any]
    ) -> str:
        """Mint test tokens (if you're the deployer)"""
        token_address = args.get("token_address", self.MOCK_TOKEN)
        recipient = args["recipient"]
        amount = args.get("amount", "1000000000000000000")

        try:
            # Encode the mint function call using Web3
            web3 = Web3()
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )
            # Use the functions interface to encode the transaction data
            mint_fn = contract.functions.mint(
                Web3.to_checksum_address(recipient),
                int(amount)
            )
            data = mint_fn._encode_transaction_data()

            # Send the transaction
            tx_hash = wallet_provider.send_transaction({
                "to": Web3.to_checksum_address(token_address),
                "data": data,
                "value": 0
            })

            amount_tokens = int(amount) / 1e18

            return (
                f"✅ Minted {amount_tokens} test tokens!\n"
                f"Transaction hash: {tx_hash}\n"
                f"Recipient: {recipient}\n"
                f"Amount: {amount} wei ({amount_tokens} tokens)"
            )

        except Exception as e:
            return f"❌ Failed to mint tokens: {str(e)}\nNote: Only the contract deployer can mint tokens."

    def supports_network(self, network: Network) -> bool:
        """This action provider only works on Base Sepolia"""
        return network.network_id == "base-sepolia"


def approval_test_action_provider() -> ApprovalTestActionProvider:
    """Factory function to create the approval test action provider"""
    return ApprovalTestActionProvider()