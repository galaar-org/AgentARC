"""
Value and amount limit validators.

These validators enforce spending limits on ETH and token transfers.
"""

from typing import Any, Dict, List, TYPE_CHECKING

from web3 import Web3

from ..base import PolicyValidator, ValidationResult
from ..registry import ValidatorRegistry

if TYPE_CHECKING:
    from ...calldata_parser import ParsedTransaction


@ValidatorRegistry.register("eth_value_limit")
class EthValueLimitValidator(PolicyValidator):
    """
    Limit ETH value per transaction.

    Applies to ALL transactions, including contract calls that send ETH.

    Configuration:
        type: "eth_value_limit"
        max_value_wei: Maximum ETH value in wei (as string for large numbers)
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "eth_value_limit",
        ...     "max_value_wei": "1000000000000000000",  # 1 ETH
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if ETH value exceeds limit."""
        if not self.enabled:
            return ValidationResult(passed=True)

        max_value_wei = int(self.config.get("max_value_wei", 0))

        if max_value_wei == 0:
            return ValidationResult(passed=True)

        # Check ETH value for ALL transactions
        if parsed_tx.value > max_value_wei:
            value_eth = Web3.from_wei(parsed_tx.value, "ether")
            limit_eth = Web3.from_wei(max_value_wei, "ether")
            return ValidationResult(
                passed=False,
                reason=f"ETH value {value_eth} ETH exceeds limit of {limit_eth} ETH",
                rule_name="eth_value_limit",
            )

        return ValidationResult(passed=True)


@ValidatorRegistry.register("token_amount_limit")
class TokenAmountLimitValidator(PolicyValidator):
    """
    Limit token transfer amounts per transaction.

    Only applies to transactions that transfer tokens (transfer, transferFrom).
    Non-token transactions always pass.

    Configuration:
        type: "token_amount_limit"
        max_amount: Maximum token amount in smallest unit (as string)
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "token_amount_limit",
        ...     "max_amount": "1000000000000000000000",  # 1000 tokens (18 decimals)
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if token amount exceeds limit."""
        if not self.enabled:
            return ValidationResult(passed=True)

        # Only applies to token transfers
        if not parsed_tx.token_amount:
            return ValidationResult(passed=True)

        max_amount = int(self.config.get("max_amount", 0))

        if max_amount == 0:
            return ValidationResult(passed=True)

        if parsed_tx.token_amount > max_amount:
            return ValidationResult(
                passed=False,
                reason=f"Token amount {parsed_tx.token_amount} exceeds limit of {max_amount}",
                rule_name="token_amount_limit",
            )

        return ValidationResult(passed=True)


@ValidatorRegistry.register("per_asset_limit")
class PerAssetLimitValidator(PolicyValidator):
    """
    Limit spending per specific token/asset.

    Allows setting different limits for different tokens.
    Tokens not in the list have no limit.

    Configuration:
        type: "per_asset_limit"
        asset_limits: List of asset configurations, each containing:
            - name: Human-readable token name
            - address: Token contract address
            - max_amount: Maximum amount in smallest unit
            - decimals: Token decimals for display
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "per_asset_limit",
        ...     "asset_limits": [
        ...         {"name": "USDC", "address": "0xa0b8...", "max_amount": "10000000", "decimals": 6},
        ...         {"name": "DAI", "address": "0x6b17...", "max_amount": "100000000000000000000", "decimals": 18}
        ...     ],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if token amount exceeds per-asset limit."""
        if not self.enabled:
            return ValidationResult(passed=True)

        # Get asset limits from config
        asset_limits: List[Dict[str, Any]] = self.config.get("asset_limits", [])

        if not asset_limits:
            return ValidationResult(passed=True)

        # Only applies to token transfers
        if not parsed_tx.token_address or not parsed_tx.token_amount:
            return ValidationResult(passed=True)

        token_address = parsed_tx.token_address.lower()

        # Check if this token has a limit
        for asset_config in asset_limits:
            config_address = asset_config.get("address", "").lower()

            if config_address == token_address:
                max_amount = int(asset_config.get("max_amount", 0))
                token_name = asset_config.get("name", token_address[:10])
                decimals = int(asset_config.get("decimals", 18))

                if max_amount == 0:
                    continue

                if parsed_tx.token_amount > max_amount:
                    # Convert to human-readable
                    amount_readable = parsed_tx.token_amount / (10**decimals)
                    limit_readable = max_amount / (10**decimals)

                    return ValidationResult(
                        passed=False,
                        reason=f"{token_name} amount {amount_readable} exceeds limit of {limit_readable}",
                        rule_name="per_asset_limit",
                    )

        return ValidationResult(passed=True)
