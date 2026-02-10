"""
Type definitions for AgentARC.

Provides TypedDict definitions for implicit interfaces,
reducing reliance on Dict[str, Any] throughout the codebase.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Use typing_extensions for Python 3.10 compatibility
try:
    from typing import NotRequired, TypedDict
except ImportError:
    from typing_extensions import NotRequired, TypedDict


# ============================================================
# Transaction Types
# ============================================================

class TransactionDict(TypedDict, total=False):
    """
    Standard Ethereum transaction dictionary.

    This TypedDict replaces Dict[str, Any] for transaction parameters,
    providing type safety and IDE autocomplete.

    Attributes:
        to: Destination address (contract or EOA)
        value: ETH value in wei
        data: Transaction calldata (hex string with 0x prefix)
        gas: Gas limit
        gasPrice: Gas price in wei (legacy transactions)
        maxFeePerGas: Max fee per gas (EIP-1559)
        maxPriorityFeePerGas: Max priority fee (EIP-1559)
        nonce: Transaction nonce
        chainId: Chain ID for replay protection

    Example:
        >>> tx: TransactionDict = {
        ...     "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        ...     "value": 1000000000000000000,  # 1 ETH
        ...     "data": "0x",
        ...     "gas": 21000,
        ... }
    """
    to: str
    value: int
    data: str
    gas: NotRequired[int]
    gasPrice: NotRequired[int]
    maxFeePerGas: NotRequired[int]
    maxPriorityFeePerGas: NotRequired[int]
    nonce: NotRequired[int]
    chainId: NotRequired[int]


class TransactionDictWithFrom(TransactionDict):
    """Transaction dictionary that includes the 'from' address."""
    # Note: 'from' is a reserved keyword, so we use this separate type
    # when the sender address is included
    pass


# ============================================================
# Policy Configuration Types
# ============================================================

class PolicyType(str, Enum):
    """Supported policy types."""
    ETH_VALUE_LIMIT = "eth_value_limit"
    ADDRESS_DENYLIST = "address_denylist"
    ADDRESS_ALLOWLIST = "address_allowlist"
    TOKEN_AMOUNT_LIMIT = "token_amount_limit"
    PER_ASSET_LIMIT = "per_asset_limit"
    FUNCTION_ALLOWLIST = "function_allowlist"
    GAS_LIMIT = "gas_limit"


class BasePolicyConfigDict(TypedDict, total=False):
    """Base policy configuration structure."""
    type: str
    enabled: bool
    description: NotRequired[str]


class EthValueLimitPolicyDict(BasePolicyConfigDict):
    """ETH value limit policy configuration."""
    max_value_wei: str


class AddressDenylistPolicyDict(BasePolicyConfigDict):
    """Address denylist policy configuration."""
    denied_addresses: List[str]


class AddressAllowlistPolicyDict(BasePolicyConfigDict):
    """Address allowlist policy configuration."""
    allowed_addresses: List[str]


class TokenAmountLimitPolicyDict(BasePolicyConfigDict):
    """Token amount limit policy configuration."""
    max_amount: str


class AssetLimitDict(TypedDict):
    """Per-asset limit configuration."""
    name: str
    address: str
    max_amount: str
    decimals: int


class PerAssetLimitPolicyDict(BasePolicyConfigDict):
    """Per-asset limit policy configuration."""
    asset_limits: List[AssetLimitDict]


class FunctionAllowlistPolicyDict(BasePolicyConfigDict):
    """Function allowlist policy configuration."""
    allowed_functions: List[str]


class GasLimitPolicyDict(BasePolicyConfigDict):
    """Gas limit policy configuration."""
    max_gas: int


# Union of all policy config types
PolicyConfigDict = Union[
    EthValueLimitPolicyDict,
    AddressDenylistPolicyDict,
    AddressAllowlistPolicyDict,
    TokenAmountLimitPolicyDict,
    PerAssetLimitPolicyDict,
    FunctionAllowlistPolicyDict,
    GasLimitPolicyDict,
    BasePolicyConfigDict,  # Fallback for unknown types
]


class SimulationConfigDict(TypedDict, total=False):
    """Simulation configuration."""
    enabled: bool
    fail_on_revert: bool
    estimate_gas: bool
    print_trace: NotRequired[bool]
    description: NotRequired[str]


class CalldataValidationConfigDict(TypedDict, total=False):
    """Calldata validation configuration."""
    enabled: bool
    strict_mode: bool
    description: NotRequired[str]


class HoneypotDetectionConfigDict(TypedDict, total=False):
    """Honeypot detection configuration."""
    enabled: bool
    description: NotRequired[str]


class LLMValidationConfigDict(TypedDict, total=False):
    """LLM validation configuration."""
    enabled: bool
    provider: NotRequired[str]
    model: NotRequired[str]
    api_key: NotRequired[str]
    description: NotRequired[str]
    warn_threshold: NotRequired[float]
    block_threshold: NotRequired[float]
    patterns: NotRequired[List[str]]
    honeypot_detection: NotRequired[HoneypotDetectionConfigDict]


class LoggingConfigDict(TypedDict, total=False):
    """Logging configuration."""
    level: str


class FullPolicyConfigDict(TypedDict, total=False):
    """
    Complete policy configuration structure.

    This represents the full policy.yaml configuration file.
    """
    version: str
    enabled: bool
    apply_to: NotRequired[List[str]]
    logging: NotRequired[LoggingConfigDict]
    policies: List[PolicyConfigDict]
    simulation: NotRequired[SimulationConfigDict]
    calldata_validation: NotRequired[CalldataValidationConfigDict]
    llm_validation: NotRequired[LLMValidationConfigDict]


# ============================================================
# Simulation Result Types
# ============================================================

@dataclass
class SimulationResultBase:
    """
    Base class for simulation results.

    Both basic and Tenderly simulators return results
    that conform to this structure.
    """
    success: bool
    error: Optional[str] = None
    gas_used: Optional[int] = None


# ============================================================
# Validation Result Types
# ============================================================

class ValidationResultDict(TypedDict):
    """Validation result as dictionary."""
    passed: bool
    reason: Optional[str]
    rule_name: Optional[str]


# ============================================================
# LLM Analysis Types
# ============================================================

class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendedAction(str, Enum):
    """Recommended action from LLM analysis."""
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


class LLMAnalysisDict(TypedDict):
    """LLM analysis result as dictionary."""
    is_malicious: bool
    confidence: float
    risk_level: str
    reason: str
    indicators: List[str]
    recommended_action: str


# ============================================================
# Security Indicator Types
# ============================================================

class SecurityIndicatorsDict(TypedDict, total=False):
    """Security indicators extracted from transaction analysis."""
    # Hidden Approvals
    has_approval: bool
    approval_amount_unlimited: bool
    approval_to_unknown: bool
    multiple_approvals: int

    # Fund Flow
    unique_addresses_interacted: int
    callbacks_to_sender: int
    delegatecalls: int
    unusual_call_pattern: bool

    # Balance Changes
    user_balance_decrease_pct: float
    unexpected_recipients: List[str]
    hidden_fee_detected: bool

    # Token Behavior
    no_transfer_events: bool
    output_token_mismatch: bool
    honeypot_indicators: List[str]

    # Technical
    reentrancy_pattern: bool
    flash_loan_detected: bool


# ============================================================
# Wallet Types
# ============================================================

class WalletType(str, Enum):
    """Supported wallet types."""
    PRIVATE_KEY = "private_key"
    MNEMONIC = "mnemonic"
    HARDWARE = "hardware"
    WALLET_CONNECT = "wallet_connect"
    CDP = "cdp"
    EIP1193 = "eip1193"
    SMART_CONTRACT = "smart_contract"


@dataclass
class WalletInfo:
    """
    Wallet metadata.

    Attributes:
        address: Wallet address
        chain_id: Current chain ID
        wallet_type: Type of wallet
        name: Human-readable wallet name
        is_connected: Whether wallet is connected
    """
    address: str
    chain_id: int
    wallet_type: WalletType
    name: str
    is_connected: bool = True


@dataclass
class TransactionRequest:
    """
    Chain-agnostic transaction request.

    Used internally to represent transactions in a
    wallet-implementation-independent way.
    """
    to: str
    value: int = 0
    data: bytes = b''
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    nonce: Optional[int] = None
    chain_id: Optional[int] = None

    def to_dict(self) -> TransactionDict:
        """Convert to TransactionDict."""
        result: TransactionDict = {
            "to": self.to,
            "value": self.value,
            "data": "0x" + self.data.hex() if self.data else "0x",
        }
        if self.gas is not None:
            result["gas"] = self.gas
        if self.gas_price is not None:
            result["gasPrice"] = self.gas_price
        if self.max_fee_per_gas is not None:
            result["maxFeePerGas"] = self.max_fee_per_gas
        if self.max_priority_fee_per_gas is not None:
            result["maxPriorityFeePerGas"] = self.max_priority_fee_per_gas
        if self.nonce is not None:
            result["nonce"] = self.nonce
        if self.chain_id is not None:
            result["chainId"] = self.chain_id
        return result

    @classmethod
    def from_dict(cls, tx: Dict[str, Any]) -> "TransactionRequest":
        """Create from dictionary."""
        data = tx.get("data", "0x")
        if isinstance(data, str):
            data = bytes.fromhex(data[2:]) if data.startswith("0x") else bytes.fromhex(data)
        elif isinstance(data, bytes):
            pass
        else:
            data = b''

        return cls(
            to=tx.get("to", ""),
            value=int(tx.get("value", 0)),
            data=data,
            gas=tx.get("gas"),
            gas_price=tx.get("gasPrice"),
            max_fee_per_gas=tx.get("maxFeePerGas"),
            max_priority_fee_per_gas=tx.get("maxPriorityFeePerGas"),
            nonce=tx.get("nonce"),
            chain_id=tx.get("chainId"),
        )


@dataclass
class TransactionResult:
    """
    Transaction execution result.

    Returned after sending a transaction through a wallet adapter.
    """
    tx_hash: str
    success: bool
    gas_used: Optional[int] = None
    block_number: Optional[int] = None
    error: Optional[str] = None
