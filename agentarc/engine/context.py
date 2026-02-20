"""
Validation context for pipeline stages.

This module provides the ValidationContext dataclass that holds all state
passed through the validation pipeline stages.

Example:
    >>> context = ValidationContext(
    ...     transaction={"to": "0x...", "value": 100},
    ...     from_address="0x123..."
    ... )
    >>> # Pipeline stages modify context
    >>> context.parsed_tx = parser.parse(context.transaction)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.events import ValidationEvent


@dataclass
class ValidationContext:
    """
    Context passed through validation pipeline stages.

    Each stage can read from and write to this context, allowing
    data to flow between stages without tight coupling.

    Attributes:
        transaction: Original transaction dictionary
        from_address: Sender's wallet address
        parsed_tx: ParsedTransaction after intent analysis
        simulation_result: Result from basic simulation
        tenderly_result: Result from Tenderly simulation
        llm_analysis: Result from LLM security analysis
        events: List of validation events emitted
        metadata: Additional metadata for extensibility

    Example:
        >>> context = ValidationContext(
        ...     transaction={"to": "0x...", "value": 100},
        ...     from_address="0x123...",
        ... )
        >>> # Stage 1: Intent Analysis
        >>> context.parsed_tx = parser.parse(context.transaction)
        >>> # Stage 2: Simulation
        >>> context.simulation_result = simulator.simulate(...)
    """

    # Required inputs
    transaction: Dict[str, Any]
    from_address: Optional[str] = None

    # Stage outputs (populated by pipeline stages)
    parsed_tx: Optional[Any] = None
    simulation_result: Optional[Any] = None
    tenderly_result: Optional[Any] = None
    llm_analysis: Optional[Any] = None

    # Event tracking
    events: List[ValidationEvent] = field(default_factory=list)

    # Extensibility
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Final result
    passed: bool = True
    reason: str = "Validation not completed"

    def add_event(self, event: ValidationEvent) -> None:
        """Add a validation event to the context."""
        self.events.append(event)

    def fail(self, reason: str) -> None:
        """Mark validation as failed with reason."""
        self.passed = False
        self.reason = reason

    def succeed(self, reason: str = "All policies passed") -> None:
        """Mark validation as successful."""
        self.passed = True
        self.reason = reason

    @property
    def to_address(self) -> Optional[str]:
        """Get destination address from transaction."""
        return self.transaction.get("to")

    @property
    def value(self) -> int:
        """Get ETH value from transaction."""
        return int(self.transaction.get("value", 0))

    @property
    def gas(self) -> int:
        """Get gas limit from transaction."""
        return int(self.transaction.get("gas", 0))

    @property
    def data(self) -> str:
        """Get calldata from transaction."""
        return self.transaction.get("data", "0x")

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "transaction": self.transaction,
            "from_address": self.from_address,
            "parsed_tx": str(self.parsed_tx) if self.parsed_tx else None,
            "passed": self.passed,
            "reason": self.reason,
            "events_count": len(self.events),
            "metadata": self.metadata,
        }
