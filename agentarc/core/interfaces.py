"""
Abstract interfaces for AgentARC components.

This module defines Protocol classes (structural subtyping) for all injectable
components, enabling dependency injection and mock injection for testing.

Using Protocol instead of ABC allows any class that implements the required
methods to be used, without explicit inheritance (duck typing with type safety).

Example:
    >>> class MockSimulator:
    ...     def simulate(self, tx, from_addr):
    ...         return SimulationResult(success=True)
    ...     def estimate_gas(self, tx, from_addr):
    ...         return 21000
    >>>
    >>> # MockSimulator is compatible with SimulatorProtocol
    >>> # even without inheriting from it
    >>> engine = PolicyEngine(simulator=MockSimulator())
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..calldata_parser import ParsedTransaction
    from ..events import ValidationEvent
    from ..llm_judge import LLMAnalysis
    from ..simulator import SimulationResult
    from ..simulators.tenderly import TenderlySimulationResult
    from .types import TransactionDict, TransactionRequest, TransactionResult


# ============================================================
# Logger Protocol
# ============================================================

@runtime_checkable
class LoggerProtocol(Protocol):
    """
    Protocol for logging.

    Any object with these methods can be used as a logger,
    including PolicyLogger, Python's logging.Logger, or loguru.

    Example:
        >>> class SimpleLogger:
        ...     def debug(self, msg, prefix=""): print(f"DEBUG: {msg}")
        ...     def info(self, msg, prefix=""): print(f"INFO: {msg}")
        ...     def warning(self, msg, prefix=""): print(f"WARN: {msg}")
        ...     def error(self, msg, prefix=""): print(f"ERROR: {msg}")
        ...     def success(self, msg, prefix=""): print(f"SUCCESS: {msg}")
        ...     def minimal(self, msg): print(msg)
        ...     def section(self, title): print(f"=== {title} ===")
        ...     def subsection(self, title): print(f"--- {title} ---")
    """

    def debug(self, msg: str, prefix: str = "") -> None:
        """Log debug message."""
        ...

    def info(self, msg: str, prefix: str = "") -> None:
        """Log info message."""
        ...

    def warning(self, msg: str, prefix: str = "") -> None:
        """Log warning message."""
        ...

    def error(self, msg: str, prefix: str = "") -> None:
        """Log error message."""
        ...

    def success(self, msg: str, prefix: str = "") -> None:
        """Log success message."""
        ...

    def minimal(self, msg: str) -> None:
        """Log minimal/critical message (always shown)."""
        ...

    def section(self, title: str) -> None:
        """Log section header."""
        ...

    def subsection(self, title: str) -> None:
        """Log subsection header."""
        ...


# ============================================================
# Simulator Protocols
# ============================================================

@runtime_checkable
class SimulatorProtocol(Protocol):
    """
    Protocol for transaction simulators.

    Both basic (eth_call) and advanced (Tenderly) simulators
    implement this interface.

    Example:
        >>> class TestSimulator:
        ...     def simulate(self, tx, from_addr):
        ...         return SimulationResult(success=True, gas_used=21000)
        ...     def estimate_gas(self, tx, from_addr):
        ...         return 21000
    """

    def simulate(
        self,
        tx: Dict[str, Any],
        from_address: str,
    ) -> Any:  # Returns SimulationResult or TenderlySimulationResult
        """
        Simulate transaction execution.

        Args:
            tx: Transaction dictionary
            from_address: Sender address

        Returns:
            Simulation result with success status and details
        """
        ...

    def estimate_gas(
        self,
        tx: Dict[str, Any],
        from_address: str,
    ) -> Optional[int]:
        """
        Estimate gas for transaction.

        Args:
            tx: Transaction dictionary
            from_address: Sender address

        Returns:
            Estimated gas or None if estimation fails
        """
        ...


@runtime_checkable
class TenderlySimulatorProtocol(SimulatorProtocol, Protocol):
    """
    Extended protocol for Tenderly simulator.

    Includes additional methods specific to Tenderly's capabilities.
    """

    def simulate(
        self,
        tx: Dict[str, Any],
        from_address: str,
        network_id: str = "1",
        block_number: str = "latest",
        simulation_type: str = "full",
    ) -> Any:  # Returns TenderlySimulationResult
        """
        Simulate transaction via Tenderly API.

        Args:
            tx: Transaction dictionary
            from_address: Sender address
            network_id: Chain ID as string
            block_number: Block number or "latest"
            simulation_type: "full" or "quick"

        Returns:
            TenderlySimulationResult with call traces, asset changes, logs
        """
        ...

    def is_available(self) -> bool:
        """Check if Tenderly credentials are configured."""
        ...


# ============================================================
# Calldata Parser Protocol
# ============================================================

@runtime_checkable
class CalldataParserProtocol(Protocol):
    """
    Protocol for calldata parsing.

    Parses transaction calldata to extract function calls,
    parameters, and recipient information.
    """

    def parse(self, tx: Dict[str, Any]) -> Any:  # Returns ParsedTransaction
        """
        Parse transaction calldata.

        Args:
            tx: Transaction dictionary with 'to', 'value', 'data' fields

        Returns:
            ParsedTransaction with extracted function details
        """
        ...


# ============================================================
# LLM Judge Protocol
# ============================================================

@runtime_checkable
class LLMJudgeProtocol(Protocol):
    """
    Protocol for LLM-based security analysis.

    Analyzes transactions for malicious patterns using
    an LLM (OpenAI, Anthropic, or local model).
    """

    def analyze(
        self,
        transaction: Dict[str, Any],
        parsed_tx: Any,  # ParsedTransaction
        simulation_result: Optional[Any] = None,  # SimulationResult or TenderlySimulationResult
        policy_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:  # Returns Optional[LLMAnalysis]
        """
        Analyze transaction for malicious patterns.

        Args:
            transaction: Raw transaction dictionary
            parsed_tx: Parsed transaction with function details
            simulation_result: Simulation result (optional)
            policy_context: Policy context for LLM (whitelists, etc.)

        Returns:
            LLMAnalysis if analysis performed, None if skipped
        """
        ...


# ============================================================
# Policy Validator Protocol
# ============================================================

@runtime_checkable
class PolicyValidatorProtocol(Protocol):
    """
    Protocol for policy validators.

    Each validator checks a specific policy rule
    (e.g., value limits, address lists, function restrictions).
    """

    name: str
    enabled: bool

    def validate(self, parsed_tx: Any) -> Any:  # Returns ValidationResult
        """
        Validate transaction against this policy.

        Args:
            parsed_tx: ParsedTransaction with extracted fields

        Returns:
            ValidationResult with passed status and reason if failed
        """
        ...


# ============================================================
# Event Emitter Protocol
# ============================================================

@runtime_checkable
class EventEmitterProtocol(Protocol):
    """
    Protocol for event emission.

    Emits validation events for progress tracking
    and frontend integration.
    """

    def add_callback(self, callback: Callable[[Any], None]) -> None:
        """Add a callback to receive events."""
        ...

    def emit(
        self,
        stage: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a validation event."""
        ...

    def get_events(self) -> List[Any]:
        """Get all stored events."""
        ...

    def clear(self) -> None:
        """Clear stored events."""
        ...


# ============================================================
# Wallet Adapter Protocol
# ============================================================

@runtime_checkable
class WalletAdapterProtocol(Protocol):
    """
    Protocol for wallet adapters.

    All wallet implementations (private key, mnemonic, CDP, etc.)
    must implement this interface.

    Example:
        >>> class MyWallet:
        ...     def get_address(self) -> str:
        ...         return "0x..."
        ...     def get_chain_id(self) -> int:
        ...         return 1
        ...     # ... other methods
    """

    def get_address(self) -> str:
        """Get the wallet's address."""
        ...

    def get_chain_id(self) -> int:
        """Get the current chain ID."""
        ...

    def get_balance(self) -> int:
        """Get native token balance in wei."""
        ...

    def sign_message(self, message: bytes) -> bytes:
        """Sign a message."""
        ...

    def sign_transaction(self, tx: "TransactionRequest") -> bytes:
        """Sign a transaction without sending."""
        ...

    def send_transaction(self, tx: "TransactionRequest") -> "TransactionResult":
        """Sign and send a transaction."""
        ...

    def call(self, tx: "TransactionRequest") -> bytes:
        """Execute a read-only call (eth_call)."""
        ...

    def estimate_gas(self, tx: "TransactionRequest") -> int:
        """Estimate gas for a transaction."""
        ...


# ============================================================
# Abstract Base Classes (for inheritance-based typing)
# ============================================================

class BaseWalletAdapter(ABC):
    """
    Abstract base class for wallet adapters.

    Use this for inheritance-based implementations where
    you want to ensure all methods are implemented.

    Example:
        >>> class MyWallet(BaseWalletAdapter):
        ...     def get_address(self) -> str:
        ...         return "0x..."
        ...     # ... must implement all abstract methods
    """

    @abstractmethod
    def get_address(self) -> str:
        """Get the wallet's address."""
        raise NotImplementedError

    @abstractmethod
    def get_chain_id(self) -> int:
        """Get the current chain ID."""
        raise NotImplementedError

    @abstractmethod
    def get_balance(self) -> int:
        """Get native token balance in wei."""
        raise NotImplementedError

    @abstractmethod
    def sign_message(self, message: bytes) -> bytes:
        """Sign a message."""
        raise NotImplementedError

    @abstractmethod
    def sign_transaction(self, tx: "TransactionRequest") -> bytes:
        """Sign a transaction without sending."""
        raise NotImplementedError

    @abstractmethod
    def send_transaction(self, tx: "TransactionRequest") -> "TransactionResult":
        """Sign and send a transaction."""
        raise NotImplementedError

    @abstractmethod
    def call(self, tx: "TransactionRequest") -> bytes:
        """Execute a read-only call (eth_call)."""
        raise NotImplementedError

    @abstractmethod
    def estimate_gas(self, tx: "TransactionRequest") -> int:
        """Estimate gas for a transaction."""
        raise NotImplementedError

    def sign_typed_data(self, typed_data: Dict[str, Any]) -> bytes:
        """
        Sign EIP-712 typed data.

        Optional method - default implementation raises NotImplementedError.
        """
        raise NotImplementedError("Typed data signing not supported by this wallet")

    def is_connected(self) -> bool:
        """
        Check if wallet is connected.

        Optional method - default returns True.
        """
        return True


class BasePolicyValidator(ABC):
    """
    Abstract base class for policy validators.

    All validators must implement the validate() method.
    """

    def __init__(self, config: Dict[str, Any], logger: LoggerProtocol):
        """
        Initialize validator.

        Args:
            config: Policy configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.enabled: bool = config.get("enabled", True)
        self.name: str = config.get("type", "unknown")

    @abstractmethod
    def validate(self, parsed_tx: Any) -> Any:  # Returns ValidationResult
        """
        Validate transaction against this policy.

        Args:
            parsed_tx: ParsedTransaction with extracted fields

        Returns:
            ValidationResult with passed status and reason if failed
        """
        raise NotImplementedError


class BaseSimulator(ABC):
    """
    Abstract base class for transaction simulators.

    Provides a template for implementing custom simulators.
    """

    @abstractmethod
    def simulate(
        self,
        tx: Dict[str, Any],
        from_address: str,
    ) -> Any:
        """
        Simulate transaction execution.

        Args:
            tx: Transaction dictionary
            from_address: Sender address

        Returns:
            Simulation result
        """
        raise NotImplementedError

    def estimate_gas(
        self,
        tx: Dict[str, Any],
        from_address: str,
    ) -> Optional[int]:
        """
        Estimate gas for transaction.

        Default implementation returns None (not supported).
        Override in subclasses that support gas estimation.
        """
        return None
