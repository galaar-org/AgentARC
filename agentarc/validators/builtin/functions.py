"""
Function allowlist validator.

This validator restricts which contract functions can be called.
"""

from typing import TYPE_CHECKING

from ..base import PolicyValidator, ValidationResult
from ..registry import ValidatorRegistry

if TYPE_CHECKING:
    from ...calldata_parser import ParsedTransaction


@ValidatorRegistry.register("function_allowlist")
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
                    rule_name="function_allowlist",
                )

        # Check if function is allowed
        if parsed_tx.function_name not in allowed_functions:
            return ValidationResult(
                passed=False,
                reason=f"Function '{parsed_tx.function_name}' is not on allowlist",
                rule_name="function_allowlist",
            )

        return ValidationResult(passed=True)
