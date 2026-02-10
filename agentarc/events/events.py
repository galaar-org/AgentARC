"""
Event system for AgentARC validation pipeline

This module provides a structured event system for streaming validation
progress to frontends, logs, or other consumers.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import time


class ValidationStage(Enum):
    """Validation pipeline stages"""
    STARTED = "started"
    INTENT_ANALYSIS = "intent_analysis"
    POLICY_VALIDATION = "policy_validation"
    SIMULATION = "simulation"
    HONEYPOT_DETECTION = "honeypot_detection"
    LLM_VALIDATION = "llm_validation"
    COMPLETED = "completed"


class EventStatus(Enum):
    """Status of a validation event"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    INFO = "info"


@dataclass
class ValidationEvent:
    """
    A structured event from the validation pipeline.

    This can be serialized to JSON and streamed to frontends.
    """
    stage: str
    status: str
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "stage": self.stage,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details
        }


# Type alias for event callbacks
EventCallback = Callable[[ValidationEvent], None]


class EventEmitter:
    """
    Manages event callbacks and emission.

    Can be attached to PolicyEngine to stream validation events.
    """

    def __init__(self):
        self._callbacks: List[EventCallback] = []
        self._events: List[ValidationEvent] = []
        self._store_events: bool = True

    def add_callback(self, callback: EventCallback) -> None:
        """Register an event callback"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: EventCallback) -> None:
        """Remove an event callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit(
        self,
        stage: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ValidationEvent:
        """
        Emit a validation event to all registered callbacks.

        Args:
            stage: The validation stage (from ValidationStage enum or string)
            status: Event status (from EventStatus enum or string)
            message: Human-readable message
            details: Additional structured data

        Returns:
            The emitted ValidationEvent
        """
        event = ValidationEvent(
            stage=stage if isinstance(stage, str) else stage.value,
            status=status if isinstance(status, str) else status.value,
            message=message,
            details=details or {}
        )

        # Store event for later retrieval
        if self._store_events:
            self._events.append(event)

        # Notify all callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break validation
                print(f"Warning: Event callback error: {e}")

        return event

    def get_events(self) -> List[ValidationEvent]:
        """Get all stored events"""
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear stored events"""
        self._events.clear()

    def set_store_events(self, store: bool) -> None:
        """Enable or disable event storage"""
        self._store_events = store


# Global event collector for capturing events during validation
class ValidationEventCollector:
    """
    A context manager for collecting validation events.

    Usage:
        collector = ValidationEventCollector()
        policy_engine.event_emitter.add_callback(collector.collect)

        # Run validation
        passed, reason = policy_engine.validate_transaction(tx, from_addr)

        # Get collected events
        events = collector.events
    """

    def __init__(self):
        self.events: List[ValidationEvent] = []

    def collect(self, event: ValidationEvent) -> None:
        """Callback to collect events"""
        self.events.append(event)

    def clear(self) -> None:
        """Clear collected events"""
        self.events.clear()

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all events to list of dicts for JSON serialization"""
        return [event.to_dict() for event in self.events]
