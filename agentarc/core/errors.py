"""
Custom exceptions for AgentARC.

This module provides a hierarchy of exceptions for different error conditions
in the policy enforcement system.

Exception Hierarchy:
    AgentARCError (base)
    ├── PolicyViolationError - Transaction blocked by policy
    ├── ConfigurationError - Invalid configuration
    ├── SimulationError - Transaction simulation failed
    ├── WalletError - Wallet operation failed
    └── ValidationError - General validation error

Example:
    >>> from agentarc.core.errors import PolicyViolationError
    >>>
    >>> try:
    ...     policy_wallet.send_transaction(tx)
    ... except PolicyViolationError as e:
    ...     print(f"Blocked: {e.reason}")
    ...     print(f"Rule: {e.rule_name}")
"""
from typing import Any, Dict, List, Optional


class AgentARCError(Exception):
    """
    Base exception for all AgentARC errors.

    All custom exceptions in AgentARC inherit from this class,
    allowing users to catch all AgentARC errors with a single except block.

    Example:
        >>> try:
        ...     # AgentARC operations
        ... except AgentARCError as e:
        ...     print(f"AgentARC error: {e}")
    """
    pass


class PolicyViolationError(AgentARCError):
    """
    Raised when a transaction violates a policy.

    This exception is raised when the PolicyEngine determines that
    a transaction should be blocked based on configured policies.

    Attributes:
        reason: Human-readable explanation of why the transaction was blocked
        rule_name: Name of the policy rule that was violated (if available)
        details: Additional details about the violation (optional)

    Example:
        >>> raise PolicyViolationError(
        ...     reason="ETH value 2.0 ETH exceeds limit of 1.0 ETH",
        ...     rule_name="eth_value_limit"
        ... )
    """

    def __init__(
        self,
        reason: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize PolicyViolationError.

        Args:
            reason: Human-readable explanation of the violation
            rule_name: Name of the policy rule that was violated
            details: Additional details about the violation
        """
        self.reason = reason
        self.rule_name = rule_name
        self.details = details or {}

        # Construct message
        message = f"Policy violation: {reason}"
        if rule_name:
            message = f"[{rule_name}] {message}"

        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with error details
        """
        return {
            "error": "PolicyViolationError",
            "reason": self.reason,
            "rule_name": self.rule_name,
            "details": self.details,
        }


class ConfigurationError(AgentARCError):
    """
    Raised when policy configuration is invalid.

    This exception is raised during PolicyConfig initialization
    when the configuration file or dictionary is malformed.

    Attributes:
        message: Description of the configuration error
        field: The configuration field that caused the error (if applicable)
        value: The invalid value (if applicable)

    Example:
        >>> raise ConfigurationError(
        ...     message="Invalid policy type",
        ...     field="policies[0].type",
        ...     value="unknown_type"
        ... )
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        """
        Initialize ConfigurationError.

        Args:
            message: Description of the error
            field: Configuration field that caused the error
            value: The invalid value
        """
        self.field = field
        self.value = value

        # Construct full message
        full_message = f"Configuration error: {message}"
        if field:
            full_message += f" (field: {field})"
        if value is not None:
            full_message += f" (value: {value!r})"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "ConfigurationError",
            "message": str(self),
            "field": self.field,
            "value": self.value,
        }


class SimulationError(AgentARCError):
    """
    Raised when transaction simulation fails.

    This exception is raised when the simulator cannot execute
    or when the simulated transaction would revert.

    Attributes:
        message: Description of the simulation failure
        revert_reason: The revert reason from the EVM (if available)
        tx_hash: Transaction hash if partially executed (rare)

    Example:
        >>> raise SimulationError(
        ...     message="Transaction would revert",
        ...     revert_reason="ERC20: transfer amount exceeds balance"
        ... )
    """

    def __init__(
        self,
        message: str,
        revert_reason: Optional[str] = None,
        tx_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize SimulationError.

        Args:
            message: Description of the failure
            revert_reason: EVM revert reason
            tx_data: Transaction data that was simulated
        """
        self.revert_reason = revert_reason
        self.tx_data = tx_data

        # Construct full message
        full_message = f"Simulation error: {message}"
        if revert_reason:
            full_message += f" (revert: {revert_reason})"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "SimulationError",
            "message": str(self),
            "revert_reason": self.revert_reason,
        }


class WalletError(AgentARCError):
    """
    Raised when a wallet operation fails.

    This exception is raised when wallet operations like signing
    or sending transactions fail.

    Attributes:
        message: Description of the wallet error
        operation: The operation that failed (e.g., "sign", "send")
        wallet_address: The wallet address (if available)

    Example:
        >>> raise WalletError(
        ...     message="Insufficient funds for gas",
        ...     operation="send_transaction",
        ...     wallet_address="0x123..."
        ... )
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        wallet_address: Optional[str] = None,
    ):
        """
        Initialize WalletError.

        Args:
            message: Description of the error
            operation: The operation that failed
            wallet_address: The wallet address
        """
        self.operation = operation
        self.wallet_address = wallet_address

        # Construct full message
        full_message = f"Wallet error: {message}"
        if operation:
            full_message = f"Wallet error during {operation}: {message}"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "WalletError",
            "message": str(self),
            "operation": self.operation,
            "wallet_address": self.wallet_address,
        }


class ValidationError(AgentARCError):
    """
    Raised for general validation errors.

    This exception is raised when input validation fails,
    such as invalid addresses or malformed calldata.

    Attributes:
        message: Description of the validation error
        field: The field that failed validation
        constraints: The validation constraints that were violated

    Example:
        >>> raise ValidationError(
        ...     message="Invalid Ethereum address",
        ...     field="to",
        ...     constraints=["must be 42 characters", "must start with 0x"]
        ... )
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        constraints: Optional[List[str]] = None,
    ):
        """
        Initialize ValidationError.

        Args:
            message: Description of the error
            field: The field that failed validation
            constraints: List of constraint descriptions
        """
        self.field = field
        self.constraints = constraints or []

        # Construct full message
        full_message = f"Validation error: {message}"
        if field:
            full_message += f" (field: {field})"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "ValidationError",
            "message": str(self),
            "field": self.field,
            "constraints": self.constraints,
        }


class HoneypotDetectedError(PolicyViolationError):
    """
    Raised when a honeypot token is detected.

    This is a specialized PolicyViolationError for honeypot detection,
    providing additional details about the detected honeypot.

    Attributes:
        token_address: The address of the honeypot token
        detection_method: How the honeypot was detected

    Example:
        >>> raise HoneypotDetectedError(
        ...     token_address="0xscam...",
        ...     detection_method="sell_simulation_failed",
        ...     reason="Token cannot be sold after purchase"
        ... )
    """

    def __init__(
        self,
        token_address: str,
        detection_method: str,
        reason: str,
    ):
        """
        Initialize HoneypotDetectedError.

        Args:
            token_address: Address of the honeypot token
            detection_method: How the honeypot was detected
            reason: Human-readable explanation
        """
        self.token_address = token_address
        self.detection_method = detection_method

        super().__init__(
            reason=reason,
            rule_name="honeypot_detection",
            details={
                "token_address": token_address,
                "detection_method": detection_method,
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["token_address"] = self.token_address
        result["detection_method"] = self.detection_method
        return result


class LLMAnalysisError(PolicyViolationError):
    """
    Raised when LLM analysis detects malicious activity.

    This is a specialized PolicyViolationError for LLM-based detection,
    providing confidence levels and indicators.

    Attributes:
        confidence: Confidence level (0.0 to 1.0)
        risk_level: Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
        indicators: List of detected malicious indicators

    Example:
        >>> raise LLMAnalysisError(
        ...     reason="Multiple unlimited token approvals detected",
        ...     confidence=0.92,
        ...     risk_level="CRITICAL",
        ...     indicators=["unlimited_approval", "unknown_spender"]
        ... )
    """

    def __init__(
        self,
        reason: str,
        confidence: float,
        risk_level: str,
        indicators: List[str],
    ):
        """
        Initialize LLMAnalysisError.

        Args:
            reason: Human-readable explanation
            confidence: Confidence level (0.0 to 1.0)
            risk_level: Risk classification
            indicators: List of detected indicators
        """
        self.confidence = confidence
        self.risk_level = risk_level
        self.indicators = indicators

        super().__init__(
            reason=reason,
            rule_name="llm_analysis",
            details={
                "confidence": confidence,
                "risk_level": risk_level,
                "indicators": indicators,
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["confidence"] = self.confidence
        result["risk_level"] = self.risk_level
        result["indicators"] = self.indicators
        return result
