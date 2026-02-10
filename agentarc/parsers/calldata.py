"""
Calldata parser for transaction analysis and validation
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from eth_abi import decode
from web3 import Web3


@dataclass
class ParsedTransaction:
    """Parsed transaction with extracted information"""
    to: str
    value: int  # in wei
    function_name: Optional[str]
    function_selector: Optional[str]
    decoded_params: Dict[str, Any]
    raw_calldata: bytes
    recipient_address: Optional[str] = None  # Extracted recipient for transfers
    token_amount: Optional[int] = None  # Extracted amount for token transfers
    token_address: Optional[str] = None  # Token contract address


class CalldataParser:
    """Parse and decode transaction calldata"""

    # Common ERC20 function signatures
    ERC20_ABIS = {
        # transfer(address to, uint256 amount)
        "0xa9059cbb": {
            "name": "transfer",
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        # transferFrom(address from, address to, uint256 amount)
        "0x23b872dd": {
            "name": "transferFrom",
            "inputs": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
        # approve(address spender, uint256 amount)
        "0x095ea7b3": {
            "name": "approve",
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ]
        },
    }

    def __init__(self, custom_abis: Optional[Dict[str, dict]] = None):
        """
        Initialize parser with optional custom ABIs

        Args:
            custom_abis: Additional function signatures to recognize
        """
        self.abi_registry = {**self.ERC20_ABIS}
        if custom_abis:
            self.abi_registry.update(custom_abis)

    def parse(self, tx: Dict[str, Any]) -> ParsedTransaction:
        """
        Parse transaction and extract relevant information

        Args:
            tx: Transaction dict with to, value, data, etc.

        Returns:
            ParsedTransaction with decoded information
        """
        to_address = tx.get("to", "")
        value = int(tx.get("value", 0))
        calldata_hex = tx.get("data", "0x")

        # Convert hex string to bytes
        if isinstance(calldata_hex, str):
            calldata = bytes.fromhex(calldata_hex[2:] if calldata_hex.startswith("0x") else calldata_hex)
        else:
            calldata = calldata_hex

        # Simple ETH transfer (no calldata)
        if len(calldata) == 0 or calldata_hex == "0x":
            return ParsedTransaction(
                to=to_address,
                value=value,
                function_name=None,
                function_selector=None,
                decoded_params={},
                raw_calldata=calldata,
                recipient_address=to_address,  # For ETH transfer, recipient is 'to'
                token_amount=value,  # ETH amount
                token_address=None  # Native ETH
            )

        # Extract function selector (first 4 bytes)
        if len(calldata) < 4:
            return ParsedTransaction(
                to=to_address,
                value=value,
                function_name="unknown",
                function_selector=None,
                decoded_params={},
                raw_calldata=calldata
            )

        selector = "0x" + calldata[:4].hex()

        # Try to decode using known ABIs
        abi_entry = self.abi_registry.get(selector)
        if not abi_entry:
            # Unknown function - can't decode
            return ParsedTransaction(
                to=to_address,
                value=value,
                function_name="unknown",
                function_selector=selector,
                decoded_params={},
                raw_calldata=calldata,
                token_address=to_address  # Assume 'to' is token contract
            )

        # Decode parameters
        try:
            param_data = calldata[4:]
            param_types = [input_param["type"] for input_param in abi_entry["inputs"]]
            decoded_values = decode(param_types, param_data)

            # Create params dict
            params = {}
            for i, input_param in enumerate(abi_entry["inputs"]):
                params[input_param["name"]] = decoded_values[i]

            # Extract recipient and amount for common patterns
            recipient = None
            amount = None

            if abi_entry["name"] == "transfer":
                recipient = params.get("to")
                amount = params.get("amount")
            elif abi_entry["name"] == "transferFrom":
                recipient = params.get("to")
                amount = params.get("amount")
            elif abi_entry["name"] == "approve":
                recipient = params.get("spender")
                amount = params.get("amount")

            return ParsedTransaction(
                to=to_address,
                value=value,
                function_name=abi_entry["name"],
                function_selector=selector,
                decoded_params=params,
                raw_calldata=calldata,
                recipient_address=recipient,
                token_amount=amount,
                token_address=to_address  # 'to' is the token contract
            )

        except Exception as e:
            # Decoding failed
            return ParsedTransaction(
                to=to_address,
                value=value,
                function_name=abi_entry["name"],
                function_selector=selector,
                decoded_params={},
                raw_calldata=calldata,
                token_address=to_address
            )

    def extract_addresses(self, parsed_tx: ParsedTransaction) -> List[str]:
        """Extract all addresses from transaction"""
        addresses = [parsed_tx.to]

        if parsed_tx.recipient_address:
            addresses.append(parsed_tx.recipient_address)

        # Extract addresses from params
        for value in parsed_tx.decoded_params.values():
            if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
                addresses.append(value)

        return list(set(addresses))  # Remove duplicates
