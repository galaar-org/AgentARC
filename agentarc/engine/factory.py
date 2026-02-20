"""
Component factory for dependency injection.

This module provides the ComponentFactory class that creates
validators, simulators, and other components from configuration.

Example:
    >>> factory = ComponentFactory(config, logger)
    >>> validators = factory.create_validators()
    >>> simulator = factory.create_simulator(web3_provider)
"""

import os
from typing import Any, Dict, List, Optional

from ..core.config import PolicyConfig
from ..core.interfaces import (
    LoggerProtocol,
    SimulatorProtocol,
    LLMJudgeProtocol,
    CalldataParserProtocol,
)


class ComponentFactory:
    """
    Factory for creating pipeline components from configuration.

    This factory centralizes component creation logic, making it
    easier to test and customize the validation pipeline.

    Attributes:
        config: PolicyConfig instance
        logger: Logger for component creation messages

    Example:
        >>> factory = ComponentFactory(config, logger)
        >>> validators = factory.create_validators()
        >>> simulator = factory.create_simulator(web3_provider)
        >>> llm_judge = factory.create_llm_judge()
    """

    # Map policy types to validator classes
    VALIDATOR_MAP = {
        "address_denylist": "AddressDenylistValidator",
        "address_allowlist": "AddressAllowlistValidator",
        "eth_value_limit": "EthValueLimitValidator",
        "token_amount_limit": "TokenAmountLimitValidator",
        "per_asset_limit": "PerAssetLimitValidator",
        "function_allowlist": "FunctionAllowlistValidator",
    }

    def __init__(
        self,
        config: PolicyConfig,
        logger: Optional[LoggerProtocol] = None,
    ):
        self.config = config
        self.logger = logger

    def create_validators(self) -> List[Any]:
        """
        Create validator instances from configuration.

        Each policy in the config is mapped to its corresponding
        validator class. Unknown policy types are logged and skipped.

        Returns:
            List of PolicyValidator instances
        """
        # Import here to avoid circular imports
        from ..rules import (
            AddressDenylistValidator,
            AddressAllowlistValidator,
            EthValueLimitValidator,
            TokenAmountLimitValidator,
            PerAssetLimitValidator,
            FunctionAllowlistValidator,
        )

        validator_classes = {
            "address_denylist": AddressDenylistValidator,
            "address_allowlist": AddressAllowlistValidator,
            "eth_value_limit": EthValueLimitValidator,
            "token_amount_limit": TokenAmountLimitValidator,
            "per_asset_limit": PerAssetLimitValidator,
            "function_allowlist": FunctionAllowlistValidator,
        }

        validators = []

        for policy_config in self.config.policies:
            policy_type = policy_config.get("type")

            if policy_type in validator_classes:
                validator_class = validator_classes[policy_type]
                validators.append(validator_class(policy_config, self.logger))
            elif policy_type == "gas_limit":
                # Gas limit is handled separately in policy engine
                pass
            else:
                if self.logger:
                    self.logger.warning(f"Unknown policy type: {policy_type}")

        return validators

    def create_calldata_parser(self) -> CalldataParserProtocol:
        """
        Create calldata parser.

        Returns:
            CalldataParser instance
        """
        from ..parsers import CalldataParser

        return CalldataParser()

    def create_simulator(
        self,
        web3_provider: Optional[Any] = None,
    ) -> Optional[SimulatorProtocol]:
        """
        Create basic transaction simulator.

        Args:
            web3_provider: Web3 instance or wallet provider

        Returns:
            TransactionSimulator instance or None
        """
        if not self.config.simulation.get("enabled", False):
            return None

        from ..simulators import TransactionSimulator

        return TransactionSimulator(web3_provider)

    def create_tenderly_simulator(
        self,
        chain_id: Optional[int] = None,
    ) -> Optional[Any]:
        """
        Create Tenderly simulator from environment variables.

        Requires environment variables:
            - TENDERLY_ACCESS_KEY
            - TENDERLY_ACCOUNT_SLUG
            - TENDERLY_PROJECT_SLUG

        Args:
            chain_id: Optional chain ID for simulation

        Returns:
            TenderlySimulator instance or None if not configured
        """
        # Check if Tenderly is available
        try:
            from ..simulators.tenderly import TenderlySimulator
        except ImportError:
            return None

        # Get environment variables
        access_key = os.getenv("TENDERLY_ACCESS_KEY")
        account_slug = os.getenv("TENDERLY_ACCOUNT_SLUG")
        project_slug = os.getenv("TENDERLY_PROJECT_SLUG")

        if not all([access_key, account_slug, project_slug]):
            return None

        return TenderlySimulator(
            access_key=access_key,
            account_slug=account_slug,
            project_slug=project_slug,
            endpoint=os.getenv("TENDERLY_ENDPOINT", "https://api.tenderly.co/api/v1"),
            logger=self.logger,
        )

    def create_llm_judge(self) -> Optional[LLMJudgeProtocol]:
        """
        Create LLM judge from configuration.

        Only creates if llm_validation.enabled is True in config.

        Returns:
            LLMJudge instance or None if not enabled/available
        """
        # Check if LLM validation is enabled
        if not self.config.llm_validation.get("enabled", False):
            return None

        # Check if LLMJudge is available
        try:
            from ..llm_judge import LLMJudge
        except ImportError:
            return None

        return LLMJudge(
            provider=self.config.llm_validation.get("provider", "openai"),
            model=self.config.llm_validation.get("model", "gpt-4o-mini"),
            api_key=self.config.llm_validation.get("api_key"),
            block_threshold=self.config.llm_validation.get("block_threshold", 0.70),
            warn_threshold=self.config.llm_validation.get("warn_threshold", 0.40),
            logger=self.logger,
        )

    def create_logger(self) -> LoggerProtocol:
        """
        Create logger from configuration.

        Returns:
            PolicyLogger instance
        """
        from ..log import PolicyLogger, LogLevel

        log_level_str = self.config.logging.get("level", "info")
        return PolicyLogger(LogLevel(log_level_str))

    def build_policy_context(self) -> Dict[str, Any]:
        """
        Build policy context for LLM analysis.

        Extracts relevant policy information for the LLM
        to understand configured security rules.

        Returns:
            Dictionary with policy context
        """
        context = {}

        for policy in self.config.policies:
            policy_type = policy.get("type")

            if policy_type == "address_allowlist":
                allowed = policy.get("allowed_addresses", [])
                if allowed:
                    context["whitelisted_addresses"] = [
                        addr.lower() for addr in allowed
                    ]

            elif policy_type == "address_denylist":
                denied = policy.get("denied_addresses", [])
                if denied:
                    context["denied_addresses"] = [
                        addr.lower() for addr in denied
                    ]

            elif policy_type == "eth_value_limit" and policy.get("enabled"):
                max_value = policy.get("max_value_wei")
                if max_value:
                    context["max_eth_value"] = max_value

        return context
