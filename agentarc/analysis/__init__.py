"""
AgentARC Analysis Module.

This module provides LLM-based and deterministic analysis
for transaction security.

Components:
    - LLMJudge: LLM-powered transaction analysis
    - SecurityIndicators: Deterministic security indicators
    - HoneypotDetector: Honeypot token detection

Example:
    >>> from agentarc.analysis import LLMJudge
    >>> judge = LLMJudge(api_key="...")
    >>> result = judge.analyze(simulation_result)
"""

from .llm_judge import LLMJudge, SecurityIndicators, LLMAnalysis

__all__ = [
    "LLMJudge",
    "SecurityIndicators",
    "LLMAnalysis",
]
