"""
Safe (Gnosis Safe) multisig wallet adapter.

This adapter implements Safe multisig wallets, supporting both
single-signer execution and multi-signer proposal flows.

Example:
    >>> wallet = SafeAdapter(
    ...     safe_address="0xYourSafe...",
    ...     signer_key="0x1234...",
    ...     rpc_url="https://sepolia.base.org",
    ... )
    >>> print(wallet.get_address())       # Safe address
    >>> print(wallet.get_owner_address()) # Signer EOA address
    >>> print(wallet.get_threshold())     # Number of required signatures
"""

from typing import Any, Dict, List, Optional, Union

from web3 import Web3
from eth_account import Account

from .smart_wallet_base import SmartWalletAdapter
from ...core.types import TransactionRequest, TransactionResult

# Minimal Safe ABI for the methods we need
SAFE_ABI = [
    {
        "inputs": [],
        "name": "getThreshold",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getOwners",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "nonce",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "operation", "type": "uint8"},
            {"name": "safeTxGas", "type": "uint256"},
            {"name": "baseGas", "type": "uint256"},
            {"name": "gasPrice", "type": "uint256"},
            {"name": "gasToken", "type": "address"},
            {"name": "refundReceiver", "type": "address"},
            {"name": "signatures", "type": "bytes"},
        ],
        "name": "execTransaction",
        "outputs": [{"name": "success", "type": "bool"}],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "operation", "type": "uint8"},
            {"name": "safeTxGas", "type": "uint256"},
            {"name": "baseGas", "type": "uint256"},
            {"name": "gasPrice", "type": "uint256"},
            {"name": "gasToken", "type": "address"},
            {"name": "refundReceiver", "type": "address"},
            {"name": "_nonce", "type": "uint256"},
        ],
        "name": "getTransactionHash",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class SafeAdapter(SmartWalletAdapter):
    """
    Wallet implementation using Safe (Gnosis Safe) multisig.

    Supports both single-signer (threshold=1) auto-execution
    and multi-signer flows where transactions are proposed
    for co-signing.

    Attributes:
        safe_address: Address of the deployed Safe contract
        signer_account: eth_account Account for the signer EOA
        w3: Web3 instance for on-chain reads
        auto_execute: Whether to execute immediately if threshold is met

    Example:
        >>> wallet = SafeAdapter(
        ...     safe_address="0xYourSafe...",
        ...     signer_key="0x1234...",
        ...     rpc_url="https://sepolia.base.org",
        ...     auto_execute=True,
        ... )
        >>> result = wallet.send_transaction({
        ...     "to": "0x...",
        ...     "value": 1000000000000000000,
        ... })
    """

    def __init__(
        self,
        safe_address: str,
        signer_key: str,
        rpc_url: str,
        chain_id: Optional[int] = None,
        auto_execute: bool = True,
    ):
        """
        Initialize Safe multisig wallet.

        Args:
            safe_address: Address of the deployed Safe contract
            signer_key: Private key of a Safe owner/signer
            rpc_url: JSON-RPC URL
            chain_id: Target chain ID (auto-detected if not provided)
            auto_execute: Execute immediately if threshold met (default: True)
        """
        # Ensure 0x prefix
        if not signer_key.startswith("0x"):
            signer_key = "0x" + signer_key

        self.safe_address = Web3.to_checksum_address(safe_address)
        self.signer_account = Account.from_key(signer_key)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self._chain_id = chain_id
        self.auto_execute = auto_execute
        self._safe_contract = None

    def get_address(self) -> str:
        """Get the Safe contract address."""
        return self.safe_address

    def get_owner_address(self) -> str:
        """Get the signer EOA address."""
        return self.signer_account.address

    def get_chain_id(self) -> int:
        """Get chain ID (auto-detect if not set)."""
        if self._chain_id is None:
            self._chain_id = self.w3.eth.chain_id
        return self._chain_id

    def get_balance(self) -> int:
        """Get native token balance of the Safe in wei."""
        return self.w3.eth.get_balance(self.safe_address)

    def get_nonce(self) -> int:
        """Get the Safe contract nonce."""
        contract = self._get_safe_contract()
        return contract.functions.nonce().call()

    def get_threshold(self) -> int:
        """Get the number of required signatures."""
        contract = self._get_safe_contract()
        return contract.functions.getThreshold().call()

    def get_owners(self) -> List[str]:
        """Get the list of Safe owner addresses."""
        contract = self._get_safe_contract()
        return contract.functions.getOwners().call()

    def is_deployed(self) -> bool:
        """Check if the Safe contract is deployed on-chain."""
        code = self.w3.eth.get_code(self.safe_address)
        return len(code) > 0  # Empty bytes means no code

    def get_wallet_type_info(self) -> Dict[str, Any]:
        """Get Safe wallet metadata."""
        return {
            "type": "safe",
            "threshold": self.get_threshold(),
            "owners": self.get_owners(),
            "auto_execute": self.auto_execute,
        }

    def sign_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """
        Build a Safe transaction and sign it with the signer key.

        Returns the signature bytes.
        """
        tx_dict = self._to_dict(tx)
        safe_tx = self._build_safe_tx(tx_dict)

        # Get the Safe transaction hash
        safe_tx_hash = self._compute_safe_tx_hash(safe_tx)

        # Sign with the signer key
        signed = self.signer_account.unsafe_sign_hash(safe_tx_hash)

        return signed.signature

    def send_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> TransactionResult:
        """
        Build, sign, and execute a Safe transaction.

        If threshold == 1 and auto_execute is True, the transaction is
        executed immediately on-chain. Otherwise, the signed transaction
        data is returned as a pending result.
        """
        tx_dict = self._to_dict(tx)
        safe_tx = self._build_safe_tx(tx_dict)

        # Get the Safe transaction hash and sign
        safe_tx_hash = self._compute_safe_tx_hash(safe_tx)
        signed = self.signer_account.unsafe_sign_hash(safe_tx_hash)
        signature = signed.signature

        threshold = self.get_threshold()

        # If threshold is 1 and auto_execute, execute immediately
        if threshold == 1 and self.auto_execute:
            return self._execute_safe_tx(safe_tx, signature)
        else:
            # Return pending result — transaction needs more signatures
            return TransactionResult(
                success=False,
                tx_hash=safe_tx_hash.hex(),
                error=f"Awaiting co-signers: {threshold} signatures required, 1 provided",
            )

    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Make a read-only call from the Safe address."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.safe_address
        result = self.w3.eth.call(tx_dict)
        return bytes(result)

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """Estimate gas for a transaction."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.safe_address
        return self.w3.eth.estimate_gas(tx_dict)

    # ============================================================
    # Private helpers
    # ============================================================

    def _to_dict(self, tx: Union[Dict[str, Any], TransactionRequest]) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        if isinstance(tx, TransactionRequest):
            return tx.to_dict()
        return dict(tx)

    def _get_safe_contract(self):
        """Get or create the Safe web3 contract instance."""
        if self._safe_contract is None:
            self._safe_contract = self.w3.eth.contract(
                address=self.safe_address,
                abi=SAFE_ABI,
            )
        return self._safe_contract

    def _build_safe_tx(self, tx_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Safe transaction from a standard transaction dictionary."""
        to = tx_dict.get("to", ZERO_ADDRESS)
        value = tx_dict.get("value", 0)
        data = tx_dict.get("data", "0x")

        # Convert data to bytes if string
        if isinstance(data, str):
            data_bytes = bytes.fromhex(data[2:]) if data.startswith("0x") else bytes.fromhex(data) if data else b""
        else:
            data_bytes = data or b""

        return {
            "to": Web3.to_checksum_address(to),
            "value": value,
            "data": data_bytes,
            "operation": 0,  # CALL (not DELEGATECALL)
            "safeTxGas": 0,
            "baseGas": 0,
            "gasPrice": 0,
            "gasToken": ZERO_ADDRESS,
            "refundReceiver": ZERO_ADDRESS,
            "nonce": self.get_nonce(),
        }

    def _compute_safe_tx_hash(self, safe_tx: Dict[str, Any]) -> bytes:
        """Compute the Safe transaction hash using the contract's getTransactionHash."""
        contract = self._get_safe_contract()
        tx_hash = contract.functions.getTransactionHash(
            safe_tx["to"],
            safe_tx["value"],
            safe_tx["data"],
            safe_tx["operation"],
            safe_tx["safeTxGas"],
            safe_tx["baseGas"],
            safe_tx["gasPrice"],
            safe_tx["gasToken"],
            safe_tx["refundReceiver"],
            safe_tx["nonce"],
        ).call()
        return tx_hash

    def _execute_safe_tx(self, safe_tx: Dict[str, Any], signature: bytes) -> TransactionResult:
        """Execute a Safe transaction on-chain."""
        contract = self._get_safe_contract()

        # Build the execTransaction call
        tx = contract.functions.execTransaction(
            safe_tx["to"],
            safe_tx["value"],
            safe_tx["data"],
            safe_tx["operation"],
            safe_tx["safeTxGas"],
            safe_tx["baseGas"],
            safe_tx["gasPrice"],
            safe_tx["gasToken"],
            safe_tx["refundReceiver"],
            signature,
        ).build_transaction({
            "from": self.signer_account.address,
            "nonce": self.w3.eth.get_transaction_count(self.signer_account.address),
            "chainId": self.get_chain_id(),
            "gas": 500000,
            "gasPrice": self.w3.eth.gas_price,
        })

        # Sign and send the outer transaction
        signed_tx = self.signer_account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return TransactionResult(
            success=receipt.status == 1,
            tx_hash=tx_hash.hex(),
            gas_used=receipt.gasUsed,
            block_number=receipt.blockNumber,
        )
