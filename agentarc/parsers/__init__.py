"""
AgentARC Parsers Module.

This module provides calldata parsing for transaction analysis.

Components:
    - CalldataParser: Parse and decode transaction calldata
    - ParsedTransaction: Parsed transaction with extracted info

Example:
    >>> from agentarc.parsers import CalldataParser
    >>> parser = CalldataParser()
    >>> parsed = parser.parse(tx)
"""

from .calldata import CalldataParser, ParsedTransaction

__all__ = [
    "CalldataParser",
    "ParsedTransaction",
]
