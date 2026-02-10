"""
Base classes for policy validators.

This module provides the abstract base class for validators
and the ValidationResult dataclass for validation results.

Example:
    >>> class MyValidator(PolicyValidator):
    ...     def validate(self, parsed_tx):
    ...         if some_condition:
    ...             return ValidationResult(passed=False, reason="Failed")
    ...         return ValidationResult(passed=True)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

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

    def __init__(self, config: Dict[str, Any], logger: Optional["LoggerProtocol"] = None):
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
