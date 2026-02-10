"""
AgentARC Validators Module.

This module provides policy validators with a plugin architecture.
Validators can be registered and discovered dynamically.

Components:
    - ValidatorRegistry: Register and discover validators
    - PolicyValidator: Base class for validators
    - ValidationResult: Result of validation
    - Built-in validators: Address, limits, gas, functions

Example:
    >>> from agentarc.validators import ValidatorRegistry, PolicyValidator
    >>>
    >>> @ValidatorRegistry.register("my_rule")
    ... class MyValidator(PolicyValidator):
    ...     def validate(self, parsed_tx):
    ...         return ValidationResult(passed=True)
"""

from .base import PolicyValidator, ValidationResult
from .registry import ValidatorRegistry

# Import builtin validators to register them
from .builtin import (
    AddressDenylistValidator,
    AddressAllowlistValidator,
    EthValueLimitValidator,
    TokenAmountLimitValidator,
    PerAssetLimitValidator,
    GasLimitValidator,
    FunctionAllowlistValidator,
)

__all__ = [
    # Base classes
    "PolicyValidator",
    "ValidationResult",
    # Registry
    "ValidatorRegistry",
    # Built-in validators
    "AddressDenylistValidator",
    "AddressAllowlistValidator",
    "EthValueLimitValidator",
    "TokenAmountLimitValidator",
    "PerAssetLimitValidator",
    "GasLimitValidator",
    "FunctionAllowlistValidator",
]
