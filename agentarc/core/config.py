"""
Policy configuration loading and management.

This module provides the PolicyConfig class for loading, validating,
and managing policy configuration from YAML files or dictionaries.

Example:
    >>> from agentarc.core.config import PolicyConfig
    >>>
    >>> # Load from file
    >>> config = PolicyConfig.load("policy.yaml")
    >>>
    >>> # Check if policies are enabled
    >>> if config.enabled:
    ...     for policy in config.policies:
    ...         print(f"{policy['type']}: {policy.get('enabled', True)}")
    >>>
    >>> # Create from dictionary
    >>> config = PolicyConfig({
    ...     "version": "2.0",
    ...     "enabled": True,
    ...     "policies": [
    ...         {"type": "eth_value_limit", "max_value_wei": "1000000000000000000"}
    ...     ]
    ... })
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .errors import ConfigurationError
from .types import (
    FullPolicyConfigDict,
    LLMValidationConfigDict,
    LoggingConfigDict,
    PolicyConfigDict,
    SimulationConfigDict,
    CalldataValidationConfigDict,
)


class PolicyConfig:
    """
    Configuration for policy enforcement.

    Loads and manages policy configuration from YAML files or dictionaries.
    Provides validation and default value handling.

    Attributes:
        version: Config schema version (default: "1.0")
        enabled: Master switch for all checks (default: True)
        policies: List of policy configurations
        simulation: Simulation settings
        calldata_validation: Calldata validation settings
        logging: Logging configuration
        llm_validation: LLM validation settings

    Example:
        >>> config = PolicyConfig.load("policy.yaml")
        >>> print(f"Policies enabled: {config.enabled}")
        >>> print(f"Number of policies: {len(config.policies)}")
        >>>
        >>> # Access simulation settings
        >>> if config.simulation.get("enabled", False):
        ...     print("Simulation is enabled")
    """

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize from configuration dictionary.

        Args:
            config_dict: Raw configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._validate_config(config_dict)

        self.config = config_dict
        self.version: str = config_dict.get("version", "1.0")
        self.enabled: bool = config_dict.get("enabled", True)
        self.policies: List[PolicyConfigDict] = config_dict.get("policies", [])
        self.simulation: SimulationConfigDict = config_dict.get("simulation", {})
        self.calldata_validation: CalldataValidationConfigDict = config_dict.get(
            "calldata_validation", {}
        )
        self.logging: LoggingConfigDict = config_dict.get("logging", {})
        self.llm_validation: LLMValidationConfigDict = config_dict.get(
            "llm_validation", {}
        )

    def _validate_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Validate configuration structure.

        Args:
            config_dict: Configuration dictionary to validate

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(config_dict, dict):
            raise ConfigurationError(
                message="Config must be a dictionary",
                value=type(config_dict).__name__,
            )

        # Validate policies structure
        policies = config_dict.get("policies", [])
        if not isinstance(policies, list):
            raise ConfigurationError(
                message="'policies' must be a list",
                field="policies",
                value=type(policies).__name__,
            )

        # Validate each policy
        valid_policy_types = {
            "eth_value_limit",
            "address_denylist",
            "address_allowlist",
            "token_amount_limit",
            "per_asset_limit",
            "function_allowlist",
            "gas_limit",
        }

        for i, policy in enumerate(policies):
            if not isinstance(policy, dict):
                raise ConfigurationError(
                    message=f"Policy {i} must be a dictionary",
                    field=f"policies[{i}]",
                    value=type(policy).__name__,
                )

            if "type" not in policy:
                raise ConfigurationError(
                    message=f"Policy {i} missing 'type' field",
                    field=f"policies[{i}].type",
                )

            policy_type = policy.get("type")
            if policy_type not in valid_policy_types:
                # Warning, not error - allow custom policy types
                pass

        # Validate simulation config
        simulation = config_dict.get("simulation", {})
        if simulation and not isinstance(simulation, dict):
            raise ConfigurationError(
                message="'simulation' must be a dictionary",
                field="simulation",
                value=type(simulation).__name__,
            )

        # Validate llm_validation config
        llm_config = config_dict.get("llm_validation", {})
        if llm_config and not isinstance(llm_config, dict):
            raise ConfigurationError(
                message="'llm_validation' must be a dictionary",
                field="llm_validation",
                value=type(llm_config).__name__,
            )

        # Validate thresholds if present
        if llm_config:
            block_threshold = llm_config.get("block_threshold")
            if block_threshold is not None:
                if not isinstance(block_threshold, (int, float)):
                    raise ConfigurationError(
                        message="block_threshold must be a number",
                        field="llm_validation.block_threshold",
                        value=block_threshold,
                    )
                if not 0 <= block_threshold <= 1:
                    raise ConfigurationError(
                        message="block_threshold must be between 0 and 1",
                        field="llm_validation.block_threshold",
                        value=block_threshold,
                    )

            warn_threshold = llm_config.get("warn_threshold")
            if warn_threshold is not None:
                if not isinstance(warn_threshold, (int, float)):
                    raise ConfigurationError(
                        message="warn_threshold must be a number",
                        field="llm_validation.warn_threshold",
                        value=warn_threshold,
                    )
                if not 0 <= warn_threshold <= 1:
                    raise ConfigurationError(
                        message="warn_threshold must be between 0 and 1",
                        field="llm_validation.warn_threshold",
                        value=warn_threshold,
                    )

    @classmethod
    def load(cls, path: Union[str, Path]) -> "PolicyConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to policy.yaml file

        Returns:
            PolicyConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ConfigurationError: If config is invalid
            yaml.YAMLError: If YAML parsing fails

        Example:
            >>> config = PolicyConfig.load("policy.yaml")
            >>> config = PolicyConfig.load(Path("./config/policy.yaml"))
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigurationError(
                    message=f"Failed to parse YAML: {e}",
                    field="file",
                    value=str(path),
                )

        if data is None:
            raise ConfigurationError(
                message="Config file is empty",
                field="file",
                value=str(path),
            )

        return cls(data)

    @classmethod
    def create_default(cls, output_path: Union[str, Path]) -> None:
        """
        Create a comprehensive default policy configuration file.

        Creates a well-documented policy.yaml file with sensible defaults
        and examples for all policy types.

        Args:
            output_path: Where to write the config file

        Example:
            >>> PolicyConfig.create_default("policy.yaml")
            >>> config = PolicyConfig.load("policy.yaml")
        """
        default_config: FullPolicyConfigDict = {
            "version": "2.0",
            # GLOBAL MASTER SWITCH: Set to false to disable ALL AgentArc checks
            "enabled": True,
            "apply_to": ["all"],
            # Logging configuration
            "logging": {"level": "info"},  # minimal, info, debug
            # Policies
            "policies": [
                {
                    "type": "eth_value_limit",
                    "max_value_wei": "1000000000000000000",  # 1 ETH
                    "enabled": True,
                    "description": "Limit ETH transfers to 1 ETH per transaction",
                },
                {
                    "type": "address_denylist",
                    "denied_addresses": [
                        # Add sanctioned/malicious addresses here
                        # "0x...",
                    ],
                    "enabled": True,
                    "description": "Block transactions to denied addresses",
                },
                {
                    "type": "address_allowlist",
                    "allowed_addresses": [
                        # Add approved addresses here (empty = allow all)
                        # "0x...",
                    ],
                    "enabled": False,  # Disabled by default
                    "description": "Only allow transactions to approved addresses",
                },
                {
                    "type": "token_amount_limit",
                    "max_amount": "1000000000000000000000",  # 1000 tokens (18 decimals)
                    "enabled": False,
                    "description": "Limit token transfers per transaction",
                },
                {
                    "type": "per_asset_limit",
                    "asset_limits": [
                        {
                            "name": "USDC",
                            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                            "max_amount": "10000000",  # 10 USDC (6 decimals)
                            "decimals": 6,
                        },
                        {
                            "name": "DAI",
                            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                            "max_amount": "100000000000000000000",  # 100 DAI
                            "decimals": 18,
                        },
                    ],
                    "enabled": True,
                    "description": "Per-asset spending limits",
                },
                {
                    "type": "function_allowlist",
                    "allowed_functions": [
                        "eth_transfer",
                        "transfer",
                        "approve",
                        # Add more allowed functions as needed
                    ],
                    "enabled": False,
                    "description": "Only allow specific function calls",
                },
                {
                    "type": "gas_limit",
                    "max_gas": 500000,
                    "enabled": True,
                    "description": "Limit gas to 500k per transaction",
                },
            ],
            # Simulation settings
            "simulation": {
                "enabled": True,
                "fail_on_revert": True,
                "estimate_gas": True,
                "description": "Simulate transactions before execution",
            },
            # Calldata validation
            "calldata_validation": {
                "enabled": True,
                "strict_mode": False,
                "description": "Validate and parse transaction calldata",
            },
            # LLM-based Security Analysis
            "llm_validation": {
                "enabled": False,  # Disabled by default (requires API key)
                "provider": "openai",
                "model": "gpt-4o-mini",
                "description": "AI-powered pattern detection for advanced threats",
                "warn_threshold": 0.40,
                "block_threshold": 0.70,
                "patterns": [
                    "unlimited_approvals",
                    "unusual_fund_flows",
                    "hidden_fees",
                    "honeypot_indicators",
                    "fake_token_balances",
                    "transfer_restrictions",
                    "reentrancy",
                    "delegatecall_risks",
                    "time_lock_manipulation",
                ],
                "honeypot_detection": {
                    "enabled": True,
                    "description": "Automatically detect honeypot tokens via simulation",
                },
            },
        }

        with open(output_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    def get_policy(self, policy_type: str) -> Optional[PolicyConfigDict]:
        """
        Get a specific policy configuration by type.

        Args:
            policy_type: The policy type to find

        Returns:
            Policy configuration dict or None if not found

        Example:
            >>> eth_limit = config.get_policy("eth_value_limit")
            >>> if eth_limit and eth_limit.get("enabled", True):
            ...     max_value = eth_limit.get("max_value_wei", "0")
        """
        for policy in self.policies:
            if policy.get("type") == policy_type:
                return policy
        return None

    def get_enabled_policies(self) -> List[PolicyConfigDict]:
        """
        Get all enabled policies.

        Returns:
            List of enabled policy configurations

        Example:
            >>> for policy in config.get_enabled_policies():
            ...     print(f"Active policy: {policy['type']}")
        """
        return [p for p in self.policies if p.get("enabled", True)]

    def is_simulation_enabled(self) -> bool:
        """Check if simulation is enabled."""
        return self.simulation.get("enabled", False)

    def is_llm_enabled(self) -> bool:
        """Check if LLM validation is enabled."""
        return self.llm_validation.get("enabled", False)

    def get_log_level(self) -> str:
        """Get the configured log level."""
        return self.logging.get("level", "info")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Complete configuration as dictionary
        """
        return self.config.copy()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"PolicyConfig(version={self.version!r}, "
            f"enabled={self.enabled}, "
            f"policies={len(self.policies)})"
        )
