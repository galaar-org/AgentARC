"""
Gas limit validator.

Note: Gas limit validation is typically handled separately in the
PolicyEngine since it needs the raw transaction dict, not parsed.
This validator is registered but returns True by default.
"""

from typing import TYPE_CHECKING

from ..base import PolicyValidator, ValidationResult
from ..registry import ValidatorRegistry

if TYPE_CHECKING:
    from ...calldata_parser import ParsedTransaction


@ValidatorRegistry.register("gas_limit")
class GasLimitValidator(PolicyValidator):
    """
    Limit gas per transaction.

    Note: This validator always returns passed=True because gas limit
    validation requires the raw transaction dict, not the parsed transaction.
    The actual gas limit check is performed in PolicyValidationStage.

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

        Actual validation is done in PolicyValidationStage with raw transaction.
        """
        # This validator needs the raw transaction dict, not parsed
        # It's handled separately in the policy engine/stage
        return ValidationResult(passed=True)
