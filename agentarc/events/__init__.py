"""
AgentARC Events Module.

This module provides event streaming for the validation pipeline.

Components:
    - ValidationEvent: Structured event data
    - ValidationStage: Pipeline stage enum
    - EventStatus: Event status enum
    - EventEmitter: Manages callbacks and emission
    - ValidationEventCollector: Collects events for batch processing

Example:
    >>> from agentarc.events import EventEmitter, ValidationEvent
    >>> emitter = EventEmitter()
    >>> emitter.add_callback(lambda e: print(e.message))
"""

from .events import (
    ValidationEvent,
    ValidationStage,
    EventStatus,
    EventEmitter,
    EventCallback,
    ValidationEventCollector,
)

__all__ = [
    "ValidationEvent",
    "ValidationStage",
    "EventStatus",
    "EventEmitter",
    "EventCallback",
    "ValidationEventCollector",
]
