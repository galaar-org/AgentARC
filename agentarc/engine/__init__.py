"""
AgentARC Engine Module.

This module contains the core validation pipeline and orchestration logic.

Components:
    - PolicyEngine: Main orchestrator (thin, delegates to pipeline)
    - ValidationPipeline: 4-stage validation runner
    - ValidationContext: Context passed through pipeline stages
    - ComponentFactory: Creates validators, simulators from config

Example:
    >>> from agentarc.engine import PolicyEngine
    >>> engine = PolicyEngine(config_path="policy.yaml")
    >>> passed, reason = engine.validate_transaction(tx, from_address)
"""

from .context import ValidationContext
from .pipeline import ValidationPipeline, PipelineStage
from .factory import ComponentFactory
from .policy_engine import PolicyEngine as ModularPolicyEngine
from .legacy import PolicyEngine  # Full-featured legacy engine

__all__ = [
    "PolicyEngine",           # Legacy full-featured engine
    "ModularPolicyEngine",    # New slim modular engine
    "ValidationPipeline",
    "PipelineStage",
    "ValidationContext",
    "ComponentFactory",
]
