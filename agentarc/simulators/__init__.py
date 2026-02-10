"""
AgentARC Simulators Module.

This module provides transaction simulators for pre-execution analysis.

Components:
    - TransactionSimulator: Basic eth_call simulation
    - TenderlySimulator: Advanced simulation with Tenderly API

Example:
    >>> from agentarc.simulators import TransactionSimulator
    >>> simulator = TransactionSimulator(web3)
    >>> result = simulator.simulate(tx, from_address)
"""

from .basic import TransactionSimulator, SimulationResult
from .tenderly import TenderlySimulator, TenderlySimulationResult

__all__ = [
    "TransactionSimulator",
    "SimulationResult",
    "TenderlySimulator",
    "TenderlySimulationResult",
]
