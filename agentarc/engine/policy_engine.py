"""
Policy Engine - Main orchestrator for transaction validation.

This is a slim orchestrator that delegates to the ValidationPipeline.
All heavy lifting is done by pipeline stages and the component factory.

Example:
    >>> from agentarc.engine import PolicyEngine
    >>> engine = PolicyEngine(config_path="policy.yaml")
    >>> passed, reason = engine.validate_transaction(tx, from_address)
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from .context import ValidationContext
from .pipeline import ValidationPipeline, PipelineStage
from .factory import ComponentFactory
from .stages import (
    IntentAnalysisStage,
    PolicyValidationStage,
    SimulationStage,
    HoneypotDetectionStage,
    LLMAnalysisStage,
)

from ..core.config import PolicyConfig
from ..core.events import EventEmitter, ValidationEvent, ValidationStage as VStage, EventStatus
from ..core.interfaces import (
    LoggerProtocol,
    SimulatorProtocol,
    CalldataParserProtocol,
    LLMJudgeProtocol,
)


class PolicyEngine:
    """
    Advanced policy enforcement engine with 4-stage validation.

    This is a slim orchestrator that:
    1. Creates components via ComponentFactory
    2. Builds the validation pipeline
    3. Runs transactions through the pipeline

    Pipeline Stages:
        1. Intent Analysis - Parse and understand transaction intent
        2. Policy Validation - Check against configured policies
        3. Simulation - Test execution (basic or Tenderly)
        4. Honeypot Detection - Detect scam tokens
        5. LLM Analysis - AI-powered malicious activity detection

    Attributes:
        config: PolicyConfig instance with validation rules
        pipeline: ValidationPipeline instance
        event_emitter: Event emitter for progress tracking

    Example:
        >>> # Basic usage
        >>> engine = PolicyEngine(config_path="policy.yaml")
        >>> passed, reason = engine.validate_transaction(tx, from_address)
        >>>
        >>> # With dependency injection for testing
        >>> engine = PolicyEngine(
        ...     config=my_config,
        ...     logger=mock_logger,
        ...     simulator=mock_simulator,
        ... )
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config: Optional[PolicyConfig] = None,
        web3_provider: Optional[Any] = None,
        chain_id: Optional[int] = None,
        event_callback: Optional[Callable[[ValidationEvent], None]] = None,
        # Dependency injection
        logger: Optional[LoggerProtocol] = None,
        calldata_parser: Optional[CalldataParserProtocol] = None,
        simulator: Optional[SimulatorProtocol] = None,
        tenderly_simulator: Optional[SimulatorProtocol] = None,
        llm_judge: Optional[LLMJudgeProtocol] = None,
    ):
        """
        Initialize policy engine with optional dependency injection.

        Args:
            config_path: Path to policy.yaml configuration file
            config: PolicyConfig object (alternative to config_path)
            web3_provider: Web3 instance or wallet provider for simulation
            chain_id: Chain ID for simulation
            event_callback: Callback for validation events
            logger: Custom logger (default: from config)
            calldata_parser: Custom parser (default: CalldataParser)
            simulator: Custom simulator (default: TransactionSimulator)
            tenderly_simulator: Custom Tenderly simulator (default: from env)
            llm_judge: Custom LLM judge (default: from config)

        Raises:
            ValueError: If both config_path and config are provided
        """
        # Validate parameters
        if config_path and config:
            raise ValueError("Cannot specify both config_path and config")

        # Initialize event emitter
        self.event_emitter = EventEmitter()
        if event_callback:
            self.event_emitter.add_callback(event_callback)

        # Load configuration
        self.config = self._load_config(config_path, config)
        self.chain_id = chain_id

        # Create component factory
        self.factory = ComponentFactory(self.config)

        # Initialize components (use injected or create from factory)
        self.logger: LoggerProtocol = logger or self.factory.create_logger()
        self.factory.logger = self.logger  # Update factory logger

        self.parser = calldata_parser or self.factory.create_calldata_parser()
        self.simulator = simulator or self.factory.create_simulator(web3_provider)
        self.tenderly_simulator = (
            tenderly_simulator
            if tenderly_simulator is not None
            else self.factory.create_tenderly_simulator(chain_id)
        )
        self.llm_validator = (
            llm_judge
            if llm_judge is not None
            else self.factory.create_llm_judge()
        )

        # Create validators
        self.validators = self.factory.create_validators()

        # Build validation pipeline
        self.pipeline = self._build_pipeline()

    def _load_config(
        self,
        config_path: Optional[str],
        config: Optional[PolicyConfig],
    ) -> PolicyConfig:
        """Load or create configuration."""
        if config:
            return config
        elif config_path:
            return PolicyConfig.load(config_path)
        else:
            # Default minimal configuration
            return PolicyConfig({
                "version": "2.0",
                "enabled": True,
                "policies": [
                    {"type": "eth_value_limit", "max_value_wei": "1000000000000000000", "enabled": True},
                    {"type": "gas_limit", "max_gas": 500000, "enabled": True},
                ],
                "simulation": {"enabled": True, "fail_on_revert": True},
                "calldata_validation": {"enabled": True},
                "logging": {"level": "info"},
                "llm_validation": {"enabled": False},
            })

    def _build_pipeline(self) -> ValidationPipeline:
        """Build the validation pipeline with configured stages."""
        stages: List[PipelineStage] = []

        # Stage 1: Intent Analysis (always enabled)
        stages.append(IntentAnalysisStage(
            parser=self.parser,
            config=self.config,
        ))

        # Stage 2: Policy Validation (always enabled if policies exist)
        if self.validators or self._has_gas_limit_policy():
            stages.append(PolicyValidationStage(
                validators=self.validators,
                config=self.config,
            ))

        # Stage 3: Simulation (if enabled)
        if self.tenderly_simulator or (self.simulator and self.config.simulation.get("enabled")):
            stages.append(SimulationStage(
                simulator=self.simulator,
                tenderly_simulator=self.tenderly_simulator,
                config=self.config,
                chain_id=self.chain_id,
            ))

        # Stage 3.5: Honeypot Detection (if LLM enabled and Tenderly available)
        if self.config.llm_validation.get("enabled") and self.tenderly_simulator:
            stages.append(HoneypotDetectionStage(
                tenderly_simulator=self.tenderly_simulator,
                chain_id=self.chain_id,
            ))

        # Stage 4: LLM Analysis (if enabled)
        if self.llm_validator:
            policy_context = self.factory.build_policy_context()
            stages.append(LLMAnalysisStage(
                llm_judge=self.llm_validator,
                config=self.config,
                policy_context=policy_context,
            ))

        return ValidationPipeline(
            stages=stages,
            logger=self.logger,
            event_emitter=self.event_emitter,
        )

    def _has_gas_limit_policy(self) -> bool:
        """Check if gas limit policy is configured."""
        return any(
            p.get("type") == "gas_limit" and p.get("enabled", True)
            for p in self.config.policies
        )

    def validate_transaction(
        self,
        transaction: Dict[str, Any],
        from_address: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate a transaction through the pipeline.

        Args:
            transaction: Transaction dictionary
            from_address: Sender's wallet address

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        # Check global master switch
        if not self.config.enabled:
            self.logger.minimal("PolicyLayer DISABLED: All checks bypassed")
            self.event_emitter.emit(
                VStage.COMPLETED.value,
                EventStatus.SKIPPED.value,
                "PolicyLayer disabled via config",
                {"reason": "disabled"},
            )
            return True, "PolicyLayer disabled via config"

        self.logger.section("POLICYLAYER: Validating Transaction")

        # Create validation context
        context = ValidationContext(
            transaction=transaction,
            from_address=from_address,
        )

        # Run pipeline
        return self.pipeline.run(context)

    # Backward compatibility methods

    def add_event_callback(self, callback: Callable[[ValidationEvent], None]) -> None:
        """Add an event callback."""
        self.event_emitter.add_callback(callback)

    def get_validators(self) -> List[Any]:
        """Get list of validators."""
        return self.validators

    def get_config(self) -> PolicyConfig:
        """Get policy configuration."""
        return self.config
