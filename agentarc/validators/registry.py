"""
Validator registry for plugin architecture.

This module provides a registry for discovering and creating
validators dynamically based on policy type.

Example:
    >>> @ValidatorRegistry.register("my_custom_rule")
    ... class MyValidator(PolicyValidator):
    ...     def validate(self, parsed_tx):
    ...         return ValidationResult(passed=True)
    >>>
    >>> # Later, create validator from config
    >>> validator = ValidatorRegistry.create(config, logger)
"""

from typing import Any, Dict, List, Optional, Type

from .base import PolicyValidator, ValidationResult


class ValidatorRegistry:
    """
    Registry for policy validators.

    Validators can register themselves with a policy type name,
    and then be created from configuration dictionaries.

    Example:
        >>> @ValidatorRegistry.register("my_rule")
        ... class MyValidator(PolicyValidator):
        ...     pass
        >>>
        >>> config = {"type": "my_rule", "enabled": True}
        >>> validator = ValidatorRegistry.create(config, logger)
    """

    _validators: Dict[str, Type[PolicyValidator]] = {}

    @classmethod
    def register(cls, policy_type: str):
        """
        Decorator to register a validator class.

        Args:
            policy_type: The policy type name this validator handles

        Returns:
            Decorator function

        Example:
            >>> @ValidatorRegistry.register("address_denylist")
            ... class AddressDenylistValidator(PolicyValidator):
            ...     pass
        """

        def decorator(validator_cls: Type[PolicyValidator]) -> Type[PolicyValidator]:
            cls._validators[policy_type] = validator_cls
            return validator_cls

        return decorator

    @classmethod
    def get(cls, policy_type: str) -> Optional[Type[PolicyValidator]]:
        """
        Get validator class by policy type.

        Args:
            policy_type: The policy type name

        Returns:
            Validator class or None if not found
        """
        return cls._validators.get(policy_type)

    @classmethod
    def create(cls, config: Dict[str, Any], logger: Optional[Any] = None) -> Optional[PolicyValidator]:
        """
        Create validator instance from configuration.

        Args:
            config: Policy configuration dictionary with 'type' key
            logger: Logger instance

        Returns:
            Validator instance or None if type not found
        """
        policy_type = config.get("type")
        if not policy_type:
            return None

        validator_cls = cls.get(policy_type)
        if not validator_cls:
            return None

        return validator_cls(config, logger)

    @classmethod
    def create_all(
        cls,
        configs: List[Dict[str, Any]],
        logger: Optional[Any] = None,
    ) -> List[PolicyValidator]:
        """
        Create validators for all configurations.

        Args:
            configs: List of policy configuration dictionaries
            logger: Logger instance

        Returns:
            List of validator instances (skips unknown types)
        """
        validators = []
        for config in configs:
            validator = cls.create(config, logger)
            if validator:
                validators.append(validator)
        return validators

    @classmethod
    def list_types(cls) -> List[str]:
        """
        List all registered policy types.

        Returns:
            List of registered policy type names
        """
        return list(cls._validators.keys())

    @classmethod
    def is_registered(cls, policy_type: str) -> bool:
        """
        Check if a policy type is registered.

        Args:
            policy_type: The policy type name

        Returns:
            True if registered, False otherwise
        """
        return policy_type in cls._validators

    @classmethod
    def unregister(cls, policy_type: str) -> bool:
        """
        Unregister a validator (mainly for testing).

        Args:
            policy_type: The policy type name

        Returns:
            True if removed, False if not found
        """
        if policy_type in cls._validators:
            del cls._validators[policy_type]
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        """Clear all registered validators (mainly for testing)."""
        cls._validators.clear()
