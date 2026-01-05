"""Portfolio Management Action Provider for AgentKit

This module provides portfolio analysis and management actions for the autonomous agent.
"""

from typing import Dict
from web3 import Web3
from coinbase_agentkit import ActionProvider, WalletProvider, create_action
from pydantic import BaseModel
import json

# ERC20 ABI for balance queries
ERC20_ABI = [
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
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class AnalyzePortfolioInput(BaseModel):
    """Input schema for analyze_portfolio action (no params needed)"""
    pass


class PortfolioActionProvider(ActionProvider[WalletProvider]):
    """Portfolio analysis and management actions

    Provides:
    - analyze_portfolio: Check current allocation vs target
    - get_portfolio_balance: Get detailed balance breakdown
    """

    def __init__(self, target_allocation: Dict[str, float], token_addresses: Dict[str, str]):
        """Initialize portfolio action provider

        Args:
            target_allocation: Dict of {token: percentage} e.g., {"ETH": 0.5, "USDC": 0.3, "WETH": 0.2}
            token_addresses: Dict of {token_symbol: address} e.g., {"USDC": "0x036...", "WETH": "0x420..."}
        """
        super().__init__("portfolio", [])
        self.target_allocation = target_allocation
        self.token_addresses = token_addresses

    def supports_network(self, network_id: str) -> bool:
        """Supports all networks"""
        return True

    @create_action(
        name="analyze_portfolio",
        description=(
            "Analyze current portfolio allocation and compare with target allocation. "
            "Returns which tokens need to be bought or sold to rebalance the portfolio. "
            "Use this action before making any trades to determine if rebalancing is needed."
        ),
        schema=AnalyzePortfolioInput,
    )
    def analyze_portfolio(
        self,
        wallet_provider: WalletProvider,
        params: AnalyzePortfolioInput
    ) -> str:
        """Analyze portfolio allocation and suggest rebalancing trades"""
        try:
            print("   📊 Analyzing portfolio...")

            # Get RPC URL from network - Use Alchemy for better reliability
            network = wallet_provider.get_network()
            if network.network_id == "base-sepolia":
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"
            elif network.network_id == "base-mainnet":
                rpc_url = "https://mainnet.base.org"
            else:
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

            web3 = Web3(Web3.HTTPProvider(rpc_url))
            address = wallet_provider.get_address()
            print(f"   💼 Wallet: {address}")
            print(f"   🌐 Network: {network.network_id}")

            # Get current balances
            balances = self._get_balances(web3, address)

            # Calculate total value in ETH
            total_value_eth = sum(balances.values())

            if total_value_eth == 0:
                return "⚠️ Portfolio is empty. Please fund the wallet first."

            # Calculate current allocation percentages
            current_allocation = {
                token: (value / total_value_eth) if total_value_eth > 0 else 0
                for token, value in balances.items()
            }

            # Find rebalancing needs
            rebalancing_needed = {}
            for token, target_pct in self.target_allocation.items():
                current_pct = current_allocation.get(token, 0)
                diff_pct = target_pct - current_pct
                diff_value_eth = diff_pct * total_value_eth

                # Only suggest rebalancing if difference > 5% (threshold)
                if abs(diff_pct) > 0.05:
                    rebalancing_needed[token] = {
                        'current_pct': f"{current_pct*100:.1f}%",
                        'target_pct': f"{target_pct*100:.1f}%",
                        'diff_pct': f"{diff_pct*100:+.1f}%",
                        'diff_value_eth': f"{diff_value_eth:+.6f}",
                        'action': 'BUY' if diff_pct > 0 else 'SELL',
                        'trade_amount_eth': f"{abs(diff_value_eth):.6f}"
                    }

            # Build response
            result = {
                'total_value_eth': f"{total_value_eth:.6f}",
                'balances': {
                    token: f"{value:.6f} ETH" for token, value in balances.items()
                },
                'current_allocation': {
                    token: f"{pct*100:.1f}%" for token, pct in current_allocation.items()
                },
                'target_allocation': {
                    token: f"{pct*100:.1f}%" for token, pct in self.target_allocation.items()
                },
                'rebalancing_needed': rebalancing_needed
            }

            # Format human-readable output
            output = f"""
📊 Portfolio Analysis
{'='*50}

Total Value: {total_value_eth:.6f} ETH

Current Balances:
"""
            for token, value in balances.items():
                pct = current_allocation.get(token, 0) * 100
                output += f"  {token}: {value:.6f} ETH ({pct:.1f}%)\n"

            output += f"\nTarget Allocation:\n"
            for token, pct in self.target_allocation.items():
                output += f"  {token}: {pct*100:.1f}%\n"

            if rebalancing_needed:
                output += f"\n⚠️  Rebalancing Needed:\n"
                for token, info in rebalancing_needed.items():
                    output += f"\n  {token}:"
                    output += f"\n    Current: {info['current_pct']} → Target: {info['target_pct']}"
                    output += f"\n    Action: {info['action']} {info['trade_amount_eth']} ETH worth"
            else:
                output += f"\n✅ Portfolio is balanced! No rebalancing needed."

            return output

        except Exception as e:
            return f"❌ Portfolio analysis failed: {str(e)}"

    def _get_balances(self, web3: Web3, address: str) -> Dict[str, float]:
        """Get balances for all tokens in the portfolio

        Returns:
            Dict of {token_symbol: value_in_eth}
        """
        balances = {}

        # Get ETH balance
        eth_balance_wei = web3.eth.get_balance(address)
        balances['ETH'] = float(web3.from_wei(eth_balance_wei, 'ether'))

        # Get ERC20 token balances
        for token_symbol, token_address in self.token_addresses.items():
            try:
                token_contract = web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=ERC20_ABI
                )

                # Get balance
                balance_wei = token_contract.functions.balanceOf(
                    Web3.to_checksum_address(address)
                ).call()

                # Get decimals
                decimals = token_contract.functions.decimals().call()

                # Convert to ETH-like units (assuming 1:1 price for simplicity)
                # In production, you'd use an oracle or Uniswap prices
                balance_eth = balance_wei / (10 ** decimals)

                # For WETH, it's 1:1 with ETH
                # For USDC and other stablecoins, you'd need price conversion
                # For now, treat all tokens as 1:1 for simplicity
                balances[token_symbol] = balance_eth

            except Exception as e:
                print(f"Warning: Could not get balance for {token_symbol}: {e}")
                balances[token_symbol] = 0.0

        return balances

    @create_action(
        name="get_portfolio_balance",
        description="Get detailed breakdown of all token balances in the portfolio",
        schema=AnalyzePortfolioInput,
    )
    def get_portfolio_balance(
        self,
        wallet_provider: WalletProvider,
        params: AnalyzePortfolioInput
    ) -> str:
        """Get detailed balance information"""
        try:
            # Get RPC URL from network - Use Alchemy for better reliability
            network = wallet_provider.get_network()
            if network.network_id == "base-sepolia":
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"
            elif network.network_id == "base-mainnet":
                rpc_url = "https://mainnet.base.org"
            else:
                rpc_url = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

            web3 = Web3(Web3.HTTPProvider(rpc_url))
            address = wallet_provider.get_address()

            balances = self._get_balances(web3, address)

            output = f"""
💰 Portfolio Balances
{'='*50}
Wallet: {address}

"""
            for token, balance in balances.items():
                output += f"{token}: {balance:.6f}\n"

            total = sum(balances.values())
            output += f"\nTotal Value: {total:.6f} ETH (approximate)\n"

            return output

        except Exception as e:
            return f"❌ Failed to get balances: {str(e)}"