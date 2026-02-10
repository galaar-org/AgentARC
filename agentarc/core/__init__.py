"""
AgentARC Core Module.

This module contains the core policy engine, configuration, types,
interfaces, and error classes.

Components:
    - PolicyConfig: Load and manage policy configuration
    - Types: TypedDict definitions for type safety
    - Interfaces: Protocol definitions for dependency injection
    - Errors: Custom exception classes

Example:
    >>> from agentarc.core import PolicyConfig, PolicyViolationError
    >>>
    >>> config = PolicyConfig.load("policy.yaml")
    >>> print(f"Policies enabled: {config.enabled}")
"""

# Configuration
from .config import PolicyConfig

# Errors
from .errors import (
    AgentARCError,
    ConfigurationError,
    HoneypotDetectedError,
    LLMAnalysisError,
    PolicyViolationError,
    SimulationError,
    ValidationError,
    WalletError,
)

# Interfaces (Protocols)
from .interfaces import (
    BaseSimulator,
    BasePolicyValidator,
    BaseWalletAdapter,
    CalldataParserProtocol,
    EventEmitterProtocol,
    LLMJudgeProtocol,
    LoggerProtocol,
    PolicyValidatorProtocol,
    SimulatorProtocol,
    TenderlySimulatorProtocol,
    WalletAdapterProtocol,
)

# Types
from .types import (
    # Transaction types
    TransactionDict,
    TransactionRequest,
    TransactionResult,
    # Policy config types
    PolicyConfigDict,
    FullPolicyConfigDict,
    SimulationConfigDict,
    LLMValidationConfigDict,
    PolicyType,
    # Analysis types
    RiskLevel,
    RecommendedAction,
    SecurityIndicatorsDict,
    LLMAnalysisDict,
    # Wallet types
    WalletType,
    WalletInfo,
)

# Events
from .events import (
    ValidationStage,
    EventStatus,
    ValidationEvent,
    EventEmitter,
    ValidationEventCollector,
    EventCallback,
)

__all__ = [
    # Configuration
    "PolicyConfig",
    # Errors
    "AgentARCError",
    "PolicyViolationError",
    "ConfigurationError",
    "SimulationError",
    "WalletError",
    "ValidationError",
    "HoneypotDetectedError",
    "LLMAnalysisError",
    # Interfaces
    "LoggerProtocol",
    "SimulatorProtocol",
    "TenderlySimulatorProtocol",
    "CalldataParserProtocol",
    "LLMJudgeProtocol",
    "PolicyValidatorProtocol",
    "EventEmitterProtocol",
    "WalletAdapterProtocol",
    "BaseWalletAdapter",
    "BasePolicyValidator",
    "BaseSimulator",
    # Types
    "TransactionDict",
    "TransactionRequest",
    "TransactionResult",
    "PolicyConfigDict",
    "FullPolicyConfigDict",
    "SimulationConfigDict",
    "LLMValidationConfigDict",
    "PolicyType",
    "RiskLevel",
    "RecommendedAction",
    "SecurityIndicatorsDict",
    "LLMAnalysisDict",
    "WalletType",
    "WalletInfo",
    # Events
    "ValidationStage",
    "EventStatus",
    "ValidationEvent",
    "EventEmitter",
    "ValidationEventCollector",
    "EventCallback",
]
