"""Uniswap V3 Action Provider for AgentKit

This module provides Uniswap V3 integration for token swaps on Base Sepolia.
All transactions are protected by PolicyLayer before execution.
"""

from typing import Optional
from web3 import Web3
from coinbase_agentkit import ActionProvider, WalletProvider, create_action
from pydantic import BaseModel, Field
import json

# Uniswap V3 contracts on Base Sepolia
SWAP_ROUTER_02 = "0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4"
QUOTER_V2 = "0xC5290058841028F1614F3A6F0F5816cAd0df5E27"

# WETH address on Base Sepolia (used for ETH wrapping)
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"

# Uniswap V3 SwapRouter02 ABI (only functions we need)
SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Uniswap V3 QuoterV2 ABI
QUOTER_V2_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# ERC20 ABI for approve, allowance, and balanceOf
ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class SwapTokensInput(BaseModel):
    """Input schema for swap_tokens_uniswap action"""
    from_token: str = Field(
        description="Token address to swap FROM (use 'ETH' for native ETH, or token address like '0x036CbD...')"
    )
    to_token: str = Field(
        description="Token address to swap TO (use 'ETH' for native ETH, or token address)"
    )
    amount_eth: str = Field(
        description="Amount to swap in ETH units (e.g., '0.01' for 0.01 ETH or 0.01 tokens)"
    )
    slippage: Optional[float] = Field(
        default=2.0,
        description="Slippage tolerance percentage (default: 2.0 = 2%)"
    )


class GetSwapQuoteInput(BaseModel):
    """Input schema for get_swap_quote action"""
    from_token: str = Field(description="Token address to swap FROM (or 'ETH')")
    to_token: str = Field(description="Token address to swap TO (or 'ETH')")
    amount_eth: str = Field(description="Amount in ETH units")


class UniswapActionProvider(ActionProvider[WalletProvider]):
    """Uniswap V3 integration for AgentKit

    Provides actions for:
    - Token swaps (ETH↔Token, Token↔Token)
    - Price quotes

    All transactions are validated by PolicyLayer before execution.
    """

    def __init__(self):
        super().__init__("uniswap", [])

    def supports_network(self, network_id: str) -> bool:
        """Check if this action provider supports the network"""
        return network_id in ["base-sepolia", "base-mainnet"]

    @create_action(
        name="swap_tokens_uniswap",
        description=(
            "Swap tokens using Uniswap V3 on Base Sepolia. "
            "Use 'ETH' for native ETH or provide token address. "
            "Example: swap 0.01 ETH to USDC, or 10 USDC to WETH. "
            "IMPORTANT: This action is protected by PolicyLayer which will automatically "
            "detect honeypot tokens and block malicious swaps!"
        ),
        schema=SwapTokensInput,
    )
    def swap_tokens(
        self,
        wallet_provider: WalletProvider,
        params: SwapTokensInput
    ) -> str:
        """Execute token swap on Uniswap V3

        This action builds the swap transaction and sends it through wallet_provider.
        PolicyLayer will validate it before execution.
        """
        try:
            print(f"\n╭{'─' * 118}╮")
            print(f"│ {'💱 SWAP ATTEMPT':^118} │")
            print(f"├{'─' * 118}┤")
            print(f"│ From: {params.from_token[:42]:<84} │")
            print(f"│ To:   {params.to_token[:42]:<84} │")
            print(f"│ Amount: {params.amount_eth:<80} │")
            print(f"│ Slippage: {params.slippage}%{' ' * 83} │")
            print(f"╰{'─' * 118}╯")

            # Get RPC URL from network - Base Sepolia public RPC
            network = wallet_provider.get_network()
            if network.network_id == "base-sepolia":
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"
            elif network.network_id == "base-mainnet":
                rpc_url = "https://mainnet.base.org"
            else:
                rpc_url = f"https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

            # Get Web3 instance
            web3 = Web3(Web3.HTTPProvider(rpc_url))

            # Get wallet address
            address = wallet_provider.get_address()

            # Normalize token addresses - V3 requires WETH instead of ETH
            from_token = Web3.to_checksum_address(WETH_ADDRESS) if params.from_token.upper() == "ETH" else Web3.to_checksum_address(params.from_token)
            to_token = Web3.to_checksum_address(WETH_ADDRESS) if params.to_token.upper() == "ETH" else Web3.to_checksum_address(params.to_token)

            # Get token decimals and convert amount appropriately
            if params.from_token.upper() == "ETH":
                # ETH uses 18 decimals
                amount_wei = web3.to_wei(float(params.amount_eth), 'ether')
            else:
                # Get decimals from the token contract
                token_contract = web3.eth.contract(
                    address=from_token,
                    abi=ERC20_ABI
                )
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(float(params.amount_eth) * (10 ** decimals))

            # Get quote first to calculate minimum output with slippage
            quoter_contract = web3.eth.contract(
                address=Web3.to_checksum_address(QUOTER_V2),
                abi=QUOTER_V2_ABI
            )

            # V3 fee tier (0.3% is most common)
            fee = 3000

            # Get quote
            quote_params = {
                'tokenIn': from_token,
                'tokenOut': to_token,
                'amountIn': amount_wei,
                'fee': fee,
                'sqrtPriceLimitX96': 0
            }

            result = quoter_contract.functions.quoteExactInputSingle(quote_params).call()
            expected_output = result[0]

            # Calculate minimum output with slippage
            min_output = int(expected_output * (1 - params.slippage / 100))

            # Approve tokens if not ETH
            if params.from_token.upper() != "ETH":
                self._approve_token(
                    web3,
                    from_token,
                    SWAP_ROUTER_02,
                    amount_wei,
                    wallet_provider,
                    address
                )

            # Get SwapRouter contract
            router_contract = web3.eth.contract(
                address=Web3.to_checksum_address(SWAP_ROUTER_02),
                abi=SWAP_ROUTER_ABI
            )

            # Build swap params for V3
            swap_params = {
                'tokenIn': from_token,
                'tokenOut': to_token,
                'fee': fee,
                'recipient': Web3.to_checksum_address(address),
                'amountIn': amount_wei,
                'amountOutMinimum': min_output,
                'sqrtPriceLimitX96': 0  # No price limit
            }

            # Build transaction
            tx_dict = {
                'from': address,
                'gas': 300000,
                'nonce': web3.eth.get_transaction_count(address),
            }

            # If swapping from ETH, send ETH value with transaction
            if params.from_token.upper() == "ETH":
                tx_dict['value'] = amount_wei

            tx = router_contract.functions.exactInputSingle(swap_params).build_transaction(tx_dict)

            # Send transaction via wallet provider
            # PolicyLayer will validate this transaction before execution!
            print(f"\n   📤 Sending transaction to PolicyLayer for validation...")
            tx_hash = wallet_provider.send_transaction(tx)

            # Print transaction hash immediately
            print(f"\n   ✅ Transaction approved and sent!")
            print(f"   🔗 Hash: {tx_hash}")
            print(f"   🌐 View: https://sepolia.basescan.org/tx/{tx_hash}")

            # Wait for transaction to be mined
            print(f"\n   ⏳ Waiting for confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                print(f"   ✅ Confirmed in block {receipt['blockNumber']}")
            else:
                raise Exception("Swap transaction failed")

            # Convert output amount using correct decimals for output token
            if params.to_token.upper() == "ETH":
                output_formatted = web3.from_wei(expected_output, 'ether')
            else:
                # Get decimals from the output token contract
                output_token_contract = web3.eth.contract(
                    address=to_token,
                    abi=ERC20_ABI
                )
                output_decimals = output_token_contract.functions.decimals().call()
                output_formatted = expected_output / (10 ** output_decimals)

            return f"✅ Swap successful!\nTransaction: {tx_hash}\nSwapped {params.amount_eth} {params.from_token} → {output_formatted:.6f} {params.to_token}"

        except Exception as e:
            return f"❌ Swap failed: {str(e)}"

    def _approve_token(
        self,
        web3: Web3,
        token_address: str,
        spender: str,
        amount: int,
        wallet_provider: WalletProvider,
        owner_address: str
    ):
        """Approve token spending (helper method)"""
        token_contract = web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )

        # Check current allowance
        current_allowance = token_contract.functions.allowance(
            Web3.to_checksum_address(owner_address),
            Web3.to_checksum_address(spender)
        ).call()

        if current_allowance < amount:
            print(f"\n   📝 Approving tokens for swap...")

            # Build approve transaction
            approve_tx = token_contract.functions.approve(
                Web3.to_checksum_address(spender),
                amount
            ).build_transaction({
                'from': owner_address,
                'gas': 100000,
                'nonce': web3.eth.get_transaction_count(owner_address),
            })

            # Send approve transaction (also validated by PolicyLayer)
            print(f"   📤 Sending approval to PolicyLayer...")
            tx_hash = wallet_provider.send_transaction(approve_tx)

            # Wait for approval to be mined (crucial for swap to work)
            print(f"   ⏳ Waiting for approval confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                print(f"   ✅ Approval confirmed\n")
            else:
                raise Exception("Approval transaction failed")
        else:
            print(f"   ✅ Token already approved\n")

    @create_action(
        name="get_swap_quote_uniswap",
        description="Get a price quote for swapping tokens on Uniswap V3 (no transaction executed)",
        schema=GetSwapQuoteInput,
    )
    def get_quote(
        self,
        wallet_provider: WalletProvider,
        params: GetSwapQuoteInput
    ) -> str:
        """Get swap quote without executing transaction"""
        try:
            # Get RPC URL from network - Base Sepolia public RPC
            network = wallet_provider.get_network()
            if network.network_id == "base-sepolia":
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"
            elif network.network_id == "base-mainnet":
                rpc_url = "https://mainnet.base.org"
            else:
                rpc_url = f"https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

            web3 = Web3(Web3.HTTPProvider(rpc_url))

            # Normalize addresses - V3 doesn't support native ETH directly, must use WETH
            from_token = Web3.to_checksum_address(WETH_ADDRESS) if params.from_token.upper() == "ETH" else Web3.to_checksum_address(params.from_token)
            to_token = Web3.to_checksum_address(WETH_ADDRESS) if params.to_token.upper() == "ETH" else Web3.to_checksum_address(params.to_token)

            # Get token decimals and convert amount appropriately
            if params.from_token.upper() == "ETH":
                # ETH uses 18 decimals
                amount_wei = web3.to_wei(float(params.amount_eth), 'ether')
            else:
                # Get decimals from the token contract
                token_contract = web3.eth.contract(
                    address=from_token,
                    abi=ERC20_ABI
                )
                decimals = token_contract.functions.decimals().call()
                amount_wei = int(float(params.amount_eth) * (10 ** decimals))

            # Get QuoterV2 contract
            quoter_contract = web3.eth.contract(
                address=Web3.to_checksum_address(QUOTER_V2),
                abi=QUOTER_V2_ABI
            )

            # V3 uses fee tiers. Try common fee tiers: 500 (0.05%), 3000 (0.3%), 10000 (1%)
            # Most pools use 3000 (0.3%)
            fee = 3000

            # Build quote params
            quote_params = {
                'tokenIn': from_token,
                'tokenOut': to_token,
                'amountIn': amount_wei,
                'fee': fee,
                'sqrtPriceLimitX96': 0  # No price limit
            }

            # Get quote from QuoterV2
            result = quoter_contract.functions.quoteExactInputSingle(quote_params).call()
            output_amount = result[0]  # First return value is amountOut

            # Convert output amount using correct decimals for output token
            if params.to_token.upper() == "ETH":
                # ETH uses 18 decimals
                output_formatted = web3.from_wei(output_amount, 'ether')
            else:
                # Get decimals from the output token contract
                output_token_contract = web3.eth.contract(
                    address=to_token,
                    abi=ERC20_ABI
                )
                output_decimals = output_token_contract.functions.decimals().call()
                output_formatted = output_amount / (10 ** output_decimals)

            return f"💱 Quote: {params.amount_eth} {params.from_token} → {output_formatted:.6f} {params.to_token} (fee tier: 0.3%)"

        except Exception as e:
            return f"❌ Quote failed: {str(e)}"