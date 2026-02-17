"""
AgentARC - Advanced Policy Enforcement for AI Agents

A comprehensive security and policy enforcement layer for AI agents:
- 4-stage validation pipeline (Intent → Policy → Simulation → LLM Analysis)
- Multiple policy types (denylists, allowlists, value limits, per-asset limits)
- Transaction simulation before execution
- Calldata parsing and integrity verification
- Configurable logging (minimal, info, debug)
- Event streaming for frontend integration
- Dependency injection for testability
- Universal wallet support (private key, mnemonic, CDP, EIP-1193)
- Multi-framework support (LangChain, OpenAI SDK, CrewAI, AutoGen, AgentKit)

Compatible with Coinbase AgentKit and other blockchain agent frameworks.

Example (New API):
    >>> from agentarc import WalletFactory, PolicyWallet
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="https://...")
    >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    >>> result = policy_wallet.send_transaction({"to": "0x...", "value": 1000})

Example (Legacy API):
    >>> from agentarc import PolicyEngine, PolicyConfig
    >>> config = PolicyConfig.load("policy.yaml")
    >>> engine = PolicyEngine(config=config)
    >>> passed, reason = engine.validate_transaction(tx, from_address)
"""

# Core module - configuration, types, interfaces, errors
from .core import (
    # Configuration
    PolicyConfig,
    # Errors
    AgentARCError,
    PolicyViolationError,
    ConfigurationError,
    SimulationError,
    WalletError,
    ValidationError,
    HoneypotDetectedError,
    LLMAnalysisError,
    # Interfaces (Protocols)
    LoggerProtocol,
    SimulatorProtocol,
    TenderlySimulatorProtocol,
    CalldataParserProtocol,
    LLMJudgeProtocol,
    PolicyValidatorProtocol,
    EventEmitterProtocol,
    WalletAdapterProtocol,
    BaseWalletAdapter,
    BasePolicyValidator,
    BaseSimulator,
    # Types
    TransactionDict,
    TransactionRequest,
    TransactionResult,
    PolicyConfigDict,
    FullPolicyConfigDict,
    SimulationConfigDict,
    LLMValidationConfigDict,
    PolicyType,
    RiskLevel,
    RecommendedAction,
    SecurityIndicatorsDict,
    LLMAnalysisDict,
    WalletType,
    WalletInfo,
)

# Policy engine (from engine module)
from .engine import PolicyEngine

# Wallet wrapper (backward compatibility)
from .compat import PolicyWalletProvider

# Logging
from .log import PolicyLogger, LogLevel

# Event streaming
from .events import (
    ValidationEvent,
    ValidationStage,
    EventStatus,
    EventEmitter,
    ValidationEventCollector,
)

# ============================================================================
# NEW MODULAR ARCHITECTURE (v0.2.0+)
# ============================================================================

# Engine module - Modular validation pipeline
from .engine import (
    ValidationContext,
    ValidationPipeline,
    PipelineStage,
    ComponentFactory,
)

# Validators module - Plugin-based validators
from .validators import (
    PolicyValidator,
    ValidationResult,
    ValidatorRegistry,
    # Built-in validators
    AddressDenylistValidator,
    AddressAllowlistValidator,
    EthValueLimitValidator,
    TokenAmountLimitValidator,
    PerAssetLimitValidator,
    GasLimitValidator,
    FunctionAllowlistValidator,
)

# Wallets module - Universal wallet support (phase 2 - optional)
try:
    from .wallets import (
        WalletAdapter,
        WalletFactory,
        PolicyWallet,
        PrivateKeyWallet,
        MnemonicWallet,
        CdpWalletAdapter,
    )
except ImportError:
    WalletAdapter = None  # type: ignore
    WalletFactory = None  # type: ignore
    PolicyWallet = None  # type: ignore
    PrivateKeyWallet = None  # type: ignore
    MnemonicWallet = None  # type: ignore
    CdpWalletAdapter = None  # type: ignore

# Frameworks module - Multi-framework adapters (phase 2 - optional)
try:
    from .frameworks import (
        FrameworkAdapter,
        LangChainAdapter,
        OpenAIAdapter,
        AgentKitAdapter,
    )
except ImportError:
    FrameworkAdapter = None  # type: ignore
    LangChainAdapter = None  # type: ignore
    OpenAIAdapter = None  # type: ignore
    AgentKitAdapter = None  # type: ignore

__version__ = "0.2.0"
__all__ = [
    # ========== LEGACY API (backward compatible) ==========
    # Main components
    "PolicyEngine",
    "PolicyConfig",
    "PolicyWalletProvider",
    "PolicyLogger",
    "LogLevel",
    # Event streaming
    "ValidationEvent",
    "ValidationStage",
    "EventStatus",
    "EventEmitter",
    "ValidationEventCollector",
    # Errors
    "AgentARCError",
    "PolicyViolationError",
    "ConfigurationError",
    "SimulationError",
    "WalletError",
    "ValidationError",
    "HoneypotDetectedError",
    "LLMAnalysisError",
    # Interfaces (Protocols)
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
    # ========== NEW MODULAR API (v0.2.0+) ==========
    # Engine module
    "ValidationContext",
    "ValidationPipeline",
    "PipelineStage",
    "ComponentFactory",
    # Validators module
    "PolicyValidator",
    "ValidationResult",
    "ValidatorRegistry",
    "AddressDenylistValidator",
    "AddressAllowlistValidator",
    "EthValueLimitValidator",
    "TokenAmountLimitValidator",
    "PerAssetLimitValidator",
    "GasLimitValidator",
    "FunctionAllowlistValidator",
    # Wallets module
    "WalletAdapter",
    "WalletFactory",
    "PolicyWallet",
    "PrivateKeyWallet",
    "MnemonicWallet",
    "CdpWalletAdapter",
    # Frameworks module
    "FrameworkAdapter",
    "LangChainAdapter",
    "OpenAIAdapter",
    "AgentKitAdapter",
]
