"""
AgentARC - Advanced Policy Enforcement for AI Agents

A comprehensive security and policy enforcement layer for AI agents:
- 3-stage validation pipeline (Intent → Validation → Simulation)
- Multiple policy types (denylists, allowlists, value limits, per-asset limits)
- Transaction simulation before execution
- Calldata parsing and integrity verification
- Configurable logging (minimal, info, debug)

Compatible with Coinbase AgentKit and other blockchain agent frameworks.
"""

from .wallet_wrapper import PolicyWalletProvider, PolicyViolationError
from .policy_engine import PolicyEngine, PolicyConfig
from .logger import PolicyLogger, LogLevel

__version__ = "0.1.0"
__all__ = [
    "PolicyWalletProvider",
    "PolicyViolationError",
    "PolicyEngine",
    "PolicyConfig",
    "PolicyLogger",
    "LogLevel",
]
