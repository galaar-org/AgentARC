"""
Policy validators for transaction enforcement.

This module provides validator classes for enforcing various policy rules
on transactions. Each validator implements the PolicyValidator interface
and checks a specific aspect of the transaction.

Available Validators:
    - AddressDenylistValidator: Block transactions to denied addresses
    - AddressAllowlistValidator: Only allow transactions to approved addresses
    - EthValueLimitValidator: Limit ETH value per transaction
    - TokenAmountLimitValidator: Limit token transfer amounts
    - PerAssetLimitValidator: Per-asset spending limits
    - FunctionAllowlistValidator: Only allow specific function calls
    - GasLimitValidator: Limit gas per transaction

Example:
    >>> from agentarc.rules import EthValueLimitValidator, ValidationResult
    >>>
    >>> config = {"type": "eth_value_limit", "max_value_wei": "1000000000000000000"}
    >>> validator = EthValueLimitValidator(config, logger)
    >>> result = validator.validate(parsed_tx)
    >>> if not result.passed:
    ...     print(f"Blocked: {result.reason}")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from web3 import Web3

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from ..calldata_parser import ParsedTransaction
    from ..core.interfaces import LoggerProtocol


@dataclass
class ValidationResult:
    """
    Result of a policy validation.

    Attributes:
        passed: Whether the transaction passed validation
        reason: Human-readable reason if validation failed
        rule_name: Name of the rule that was checked

    Example:
        >>> result = ValidationResult(passed=False, reason="Value too high", rule_name="eth_value_limit")
        >>> if not result.passed:
        ...     print(f"Blocked by {result.rule_name}: {result.reason}")
    """
    passed: bool
    reason: Optional[str] = None
    rule_name: Optional[str] = None


class PolicyValidator(ABC):
    """
    Abstract base class for policy validators.

    All validators must implement the validate() method which receives
    a ParsedTransaction and returns a ValidationResult.

    Subclasses should:
        1. Call super().__init__(config, logger) in their __init__
        2. Implement the validate() method
        3. Return ValidationResult with appropriate reason if validation fails

    Attributes:
        config: Policy configuration dictionary
        logger: Logger instance for debug output
        enabled: Whether this validator is active
        name: Policy type name for logging/identification

    Example:
        >>> class MyValidator(PolicyValidator):
        ...     def validate(self, parsed_tx):
        ...         if some_condition:
        ...             return ValidationResult(passed=False, reason="Failed", rule_name=self.name)
        ...         return ValidationResult(passed=True)
    """

    def __init__(self, config: Dict[str, Any], logger: "LoggerProtocol"):
        """
        Initialize validator.

        Args:
            config: Policy configuration dictionary containing:
                - type: Policy type name (required)
                - enabled: Whether policy is active (default: True)
                - Additional fields specific to each validator
            logger: Logger instance implementing LoggerProtocol
        """
        self.config = config
        self.logger = logger
        self.enabled: bool = config.get("enabled", True)
        self.name: str = config.get("type", "unknown")

    @abstractmethod
    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """
        Validate transaction against this policy.

        Args:
            parsed_tx: ParsedTransaction with extracted fields including:
                - to: Destination address
                - value: ETH value in wei
                - function_name: Decoded function name (if any)
                - recipient_address: Extracted recipient (for token transfers)
                - token_amount: Token amount (for token transfers)
                - token_address: Token contract address (for token transfers)

        Returns:
            ValidationResult with:
                - passed=True if validation passed
                - passed=False with reason and rule_name if failed
        """
        raise NotImplementedError


class AddressDenylistValidator(PolicyValidator):
    """
    Block transactions to/from denied addresses.

    Configuration:
        type: "address_denylist"
        denied_addresses: List of addresses to block
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "address_denylist",
        ...     "denied_addresses": ["0xbad...", "0xmalicious..."],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if transaction targets a denied address."""
        if not self.enabled:
            return ValidationResult(passed=True)

        denied_addresses = [addr.lower() for addr in self.config.get("denied_addresses", [])]

        if not denied_addresses:
            return ValidationResult(passed=True)

        # Check destination address
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
    """
    Only allow transactions to approved addresses.

    If the allowlist is empty, all addresses are allowed.
    If the allowlist has entries, only those addresses are allowed.

    Configuration:
        type: "address_allowlist"
        allowed_addresses: List of allowed addresses (empty = allow all)
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "address_allowlist",
        ...     "allowed_addresses": ["0xsafe...", "0xapproved..."],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if transaction targets an allowed address."""
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
                rule_name="token_amount_limit"
            )

        return ValidationResult(passed=True)


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
                    # Convert to human-readable for error message
                    amount_readable = parsed_tx.token_amount / (10 ** decimals)
                    limit_readable = max_amount / (10 ** decimals)

                    return ValidationResult(
                        passed=False,
                        reason=f"{token_name} amount {amount_readable} exceeds limit of {limit_readable}",
                        rule_name="per_asset_limit"
                    )

        return ValidationResult(passed=True)


class GasLimitValidator(PolicyValidator):
    """
    Limit gas per transaction.

    Note: This validator always returns passed=True because gas limit
    validation requires the raw transaction dict, not the parsed transaction.
    The actual gas limit check is performed in PolicyEngine.validate_transaction().

    Configuration:
        type: "gas_limit"
        max_gas: Maximum gas limit
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "gas_limit",
        ...     "max_gas": 500000,
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """
        Gas limit validation placeholder.

        Actual validation is done in PolicyEngine with raw transaction.
        """
        # This validator needs the raw transaction dict, not parsed
        # It's handled separately in the policy engine
        return ValidationResult(passed=True)


class FunctionAllowlistValidator(PolicyValidator):
    """
    Only allow specific function calls.

    If the allowlist is empty, all functions are allowed.
    Use "eth_transfer" to allow simple ETH transfers (no calldata).

    Configuration:
        type: "function_allowlist"
        allowed_functions: List of allowed function names
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "function_allowlist",
        ...     "allowed_functions": ["eth_transfer", "transfer", "approve"],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if function is in allowlist."""
        if not self.enabled:
            return ValidationResult(passed=True)

        allowed_functions = self.config.get("allowed_functions", [])

        # If allowlist is empty, allow all
        if not allowed_functions:
            return ValidationResult(passed=True)

        # Handle simple ETH transfers (no function call)
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
