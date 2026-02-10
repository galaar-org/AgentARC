"""
Validation pipeline with pluggable stages.

This module provides the ValidationPipeline class that orchestrates
the 4-stage validation process through pluggable stage handlers.

Pipeline Stages:
    1. Intent Analysis - Parse and understand transaction intent
    2. Policy Validation - Check against configured policies
    3. Simulation - Test execution (basic or Tenderly)
    4. LLM Analysis - AI-powered malicious activity detection

Example:
    >>> pipeline = ValidationPipeline([
    ...     IntentAnalysisStage(parser),
    ...     PolicyValidationStage(validators),
    ...     SimulationStage(simulator),
    ...     LLMAnalysisStage(llm_judge),
    ... ])
    >>> context = ValidationContext(transaction, from_address)
    >>> passed, reason = pipeline.run(context)
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any

from .context import ValidationContext
from ..core.events import EventEmitter, ValidationStage, EventStatus
from ..core.interfaces import LoggerProtocol


class PipelineStage(ABC):
    """
    Abstract base class for validation pipeline stages.

    Each stage implements the execute() method which receives
    the validation context and returns success/failure.

    Attributes:
        name: Human-readable stage name
        stage_type: ValidationStage enum value
        logger: Logger instance for output
        event_emitter: Event emitter for progress tracking

    Example:
        >>> class MyStage(PipelineStage):
        ...     def execute(self, context):
        ...         # Custom validation logic
        ...         if something_wrong:
        ...             return False, "Something failed"
        ...         return True, None
    """

    def __init__(
        self,
        name: str,
        stage_type: ValidationStage,
        logger: Optional[LoggerProtocol] = None,
        event_emitter: Optional[EventEmitter] = None,
    ):
        self.name = name
        self.stage_type = stage_type
        self.logger = logger
        self.event_emitter = event_emitter

    @abstractmethod
    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Execute this pipeline stage.

        Args:
            context: ValidationContext with transaction data and state

        Returns:
            Tuple of (passed: bool, reason: Optional[str])
            - (True, None) if stage passed
            - (False, "reason") if stage failed
        """
        raise NotImplementedError

    def emit_started(self, message: str = None) -> None:
        """Emit stage started event."""
        if self.event_emitter:
            self.event_emitter.emit(
                self.stage_type.value,
                EventStatus.STARTED.value,
                message or f"Starting {self.name}",
            )

    def emit_passed(self, message: str = None, data: dict = None) -> None:
        """Emit stage passed event."""
        if self.event_emitter:
            self.event_emitter.emit(
                self.stage_type.value,
                EventStatus.PASSED.value,
                message or f"{self.name} passed",
                data,
            )

    def emit_failed(self, message: str, data: dict = None) -> None:
        """Emit stage failed event."""
        if self.event_emitter:
            self.event_emitter.emit(
                self.stage_type.value,
                EventStatus.FAILED.value,
                message,
                data,
            )

    def emit_info(self, message: str, data: dict = None) -> None:
        """Emit informational event."""
        if self.event_emitter:
            self.event_emitter.emit(
                self.stage_type.value,
                EventStatus.INFO.value,
                message,
                data,
            )

    def emit_warning(self, message: str, data: dict = None) -> None:
        """Emit warning event."""
        if self.event_emitter:
            self.event_emitter.emit(
                self.stage_type.value,
                EventStatus.WARNING.value,
                message,
                data,
            )


class ValidationPipeline:
    """
    Orchestrates validation through multiple stages.

    The pipeline runs each stage in sequence, stopping at the first
    failure. Each stage receives the shared ValidationContext.

    Attributes:
        stages: List of PipelineStage instances
        logger: Logger instance for output
        event_emitter: Event emitter for progress tracking

    Example:
        >>> pipeline = ValidationPipeline([
        ...     IntentAnalysisStage(parser),
        ...     PolicyValidationStage(validators),
        ...     SimulationStage(simulator),
        ... ])
        >>> context = ValidationContext(transaction, from_address)
        >>> passed, reason = pipeline.run(context)
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        logger: Optional[LoggerProtocol] = None,
        event_emitter: Optional[EventEmitter] = None,
    ):
        self.stages = stages
        self.logger = logger
        self.event_emitter = event_emitter

        # Inject logger and event emitter into stages
        for stage in self.stages:
            if stage.logger is None:
                stage.logger = logger
            if stage.event_emitter is None:
                stage.event_emitter = event_emitter

    def run(self, context: ValidationContext) -> Tuple[bool, str]:
        """
        Run all pipeline stages.

        Executes each stage in sequence. If any stage fails,
        the pipeline stops and returns the failure reason.

        Args:
            context: ValidationContext with transaction data

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        # Emit pipeline started
        if self.event_emitter:
            self.event_emitter.emit(
                ValidationStage.STARTED.value,
                EventStatus.STARTED.value,
                "Starting transaction validation",
                {
                    "to": context.to_address or "",
                    "value": str(context.value),
                },
            )

        # Run each stage
        for stage in self.stages:
            if self.logger:
                self.logger.subsection(f"Stage: {stage.name}")

            passed, reason = stage.execute(context)

            if not passed:
                context.fail(reason)

                # Emit final failure
                if self.event_emitter:
                    self.event_emitter.emit(
                        ValidationStage.COMPLETED.value,
                        EventStatus.FAILED.value,
                        f"BLOCKED: {reason}",
                        {"stage": stage.name, "reason": reason},
                    )

                return False, reason

        # All stages passed
        context.succeed("All policies passed")

        # Emit final success
        if self.event_emitter:
            self.event_emitter.emit(
                ValidationStage.COMPLETED.value,
                EventStatus.PASSED.value,
                "ALLOWED: All security checks passed",
                {"approved": True},
            )

        if self.logger:
            self.logger.success("Transaction approved for execution")

        return True, "All policies passed"

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline."""
        if stage.logger is None:
            stage.logger = self.logger
        if stage.event_emitter is None:
            stage.event_emitter = self.event_emitter
        self.stages.append(stage)

    def remove_stage(self, stage_name: str) -> bool:
        """Remove a stage by name."""
        for i, stage in enumerate(self.stages):
            if stage.name == stage_name:
                self.stages.pop(i)
                return True
        return False
