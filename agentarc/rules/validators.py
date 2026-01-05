"""
Policy validators for transaction enforcement
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from web3 import Web3


@dataclass
class ValidationResult:
    """Result of a policy validation"""
    passed: bool
    reason: Optional[str] = None
    rule_name: Optional[str] = None


class PolicyValidator:
    """Base class for policy validators"""

    def __init__(self, config: Dict[str, Any], logger: Any):
        self.config = config
        self.logger = logger
        self.enabled = config.get("enabled", True)
        self.name = config.get("type", "unknown")

    def validate(self, parsed_tx: Any) -> ValidationResult:
        """Validate transaction - to be implemented by subclasses"""
        raise NotImplementedError


class AddressDenylistValidator(PolicyValidator):
    """Block transactions to/from denied addresses"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        denied_addresses = [addr.lower() for addr in self.config.get("denied_addresses", [])]

        # Check recipient
        if parsed_tx.to and parsed_tx.to.lower() in denied_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Destination address {parsed_tx.to} is on denylist",
                rule_name="address_denylist"
            )

        # Check extracted recipient (for token transfers)
        if parsed_tx.recipient_address and parsed_tx.recipient_address.lower() in denied_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Recipient address {parsed_tx.recipient_address} is on denylist",
                rule_name="address_denylist"
            )

        return ValidationResult(passed=True)


class AddressAllowlistValidator(PolicyValidator):
    """Only allow transactions to approved addresses"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        allowed_addresses = [addr.lower() for addr in self.config.get("allowed_addresses", [])]

        # If allowlist is empty, allow all
        if not allowed_addresses:
            return ValidationResult(passed=True)

        # Check recipient - use extracted recipient if available, otherwise use 'to'
        recipient = parsed_tx.recipient_address or parsed_tx.to

        if recipient and recipient.lower() not in allowed_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Address {recipient} is not on allowlist",
                rule_name="address_allowlist"
            )

        return ValidationResult(passed=True)


class EthValueLimitValidator(PolicyValidator):
    """Limit ETH value per transaction"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        max_value_wei = int(self.config.get("max_value_wei", 0))

        # Check ETH value for ALL transactions (including contract calls with value)
        if parsed_tx.value > max_value_wei:
            value_eth = Web3.from_wei(parsed_tx.value, 'ether')
            limit_eth = Web3.from_wei(max_value_wei, 'ether')
            return ValidationResult(
                passed=False,
                reason=f"ETH value {value_eth} ETH exceeds limit of {limit_eth} ETH",
                rule_name="eth_value_limit"
            )

        return ValidationResult(passed=True)


class TokenAmountLimitValidator(PolicyValidator):
    """Limit token transfer amounts per transaction"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        # Only applies to token transfers
        if not parsed_tx.token_amount:
            return ValidationResult(passed=True)

        max_amount = int(self.config.get("max_amount", 0))

        if max_amount > 0 and parsed_tx.token_amount > max_amount:
            return ValidationResult(
                passed=False,
                reason=f"Token amount {parsed_tx.token_amount} exceeds limit of {max_amount}",
                rule_name="token_amount_limit"
            )

        return ValidationResult(passed=True)


class PerAssetLimitValidator(PolicyValidator):
    """Limit spending per specific token/asset"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        # Get asset limits from config
        asset_limits = self.config.get("asset_limits", {})

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

                # Convert to human-readable
                amount_readable = parsed_tx.token_amount / (10 ** decimals)
                limit_readable = max_amount / (10 ** decimals)

                if parsed_tx.token_amount > max_amount:
                    return ValidationResult(
                        passed=False,
                        reason=f"{token_name} amount {amount_readable} exceeds limit of {limit_readable}",
                        rule_name="per_asset_limit"
                    )

        return ValidationResult(passed=True)


class GasLimitValidator(PolicyValidator):
    """Limit gas per transaction"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        # This validator needs the raw transaction dict, not parsed
        # It's handled separately in the policy engine
        return ValidationResult(passed=True)


class FunctionAllowlistValidator(PolicyValidator):
    """Only allow specific function calls"""

    def validate(self, parsed_tx: Any) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(passed=True)

        allowed_functions = self.config.get("allowed_functions", [])

        # If allowlist is empty, allow all
        if not allowed_functions:
            return ValidationResult(passed=True)

        # Allow simple ETH transfers
        if parsed_tx.function_name is None:
            if "eth_transfer" in allowed_functions:
                return ValidationResult(passed=True)
            else:
                return ValidationResult(
                    passed=False,
                    reason="Simple ETH transfers not allowed by function allowlist",
                    rule_name="function_allowlist"
                )

        # Check if function is allowed
        if parsed_tx.function_name not in allowed_functions:
            return ValidationResult(
                passed=False,
                reason=f"Function '{parsed_tx.function_name}' is not on allowlist",
                rule_name="function_allowlist"
            )

        return ValidationResult(passed=True)
