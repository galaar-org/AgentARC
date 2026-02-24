"""
ERC-4337 (Account Abstraction) wallet adapter.

This adapter implements smart contract wallets using the ERC-4337 standard,
sending transactions as UserOperations through a bundler.

Example:
    >>> wallet = ERC4337Adapter(
    ...     owner_key="0x1234...",
    ...     bundler_url="https://api.pimlico.io/v2/84532/rpc?apikey=...",
    ...     rpc_url="https://sepolia.base.org",
    ... )
    >>> print(wallet.get_address())       # Smart account address
    >>> print(wallet.get_owner_address()) # Owner EOA address
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

from web3 import Web3
from eth_account import Account
from eth_abi import encode

from .smart_wallet_base import SmartWalletAdapter
from ...core.types import TransactionRequest, TransactionResult

# ERC-4337 EntryPoint v0.6
DEFAULT_ENTRY_POINT_V06 = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"

# SimpleAccountFactory v0.6
DEFAULT_ACCOUNT_FACTORY = "0x9406Cc6185a346906296840746125a0E44976454"

# Minimal ABI for SimpleAccount execute function
SIMPLE_ACCOUNT_EXECUTE_ABI = "execute(address,uint256,bytes)"

# Minimal ABI for SimpleAccountFactory
FACTORY_CREATE_ACCOUNT_ABI = [
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "salt", "type": "uint256"},
        ],
        "name": "createAccount",
        "outputs": [{"name": "ret", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "salt", "type": "uint256"},
        ],
        "name": "getAddress",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class ERC4337Adapter(SmartWalletAdapter):
    """
    Wallet implementation using ERC-4337 Account Abstraction.

    Transactions are sent as UserOperations through a bundler service.
    The smart account address is derived counterfactually from the
    owner's EOA address using the SimpleAccountFactory.

    Attributes:
        owner_account: eth_account Account for the owner EOA
        w3: Web3 instance for on-chain reads
        bundler_url: URL of the ERC-4337 bundler RPC
        entry_point: EntryPoint contract address
        account_address: Smart account address

    Example:
        >>> wallet = ERC4337Adapter(
        ...     owner_key="0x1234...",
        ...     bundler_url="https://api.pimlico.io/v2/84532/rpc?apikey=...",
        ...     rpc_url="https://sepolia.base.org",
        ...     chain_id=84532,
        ... )
        >>> result = wallet.send_transaction({
        ...     "to": "0x...",
        ...     "value": 1000000000000000000,
        ... })
    """

    def __init__(
        self,
        owner_key: str,
        bundler_url: str,
        rpc_url: str,
        chain_id: Optional[int] = None,
        entry_point_address: Optional[str] = None,
        account_address: Optional[str] = None,
        account_factory_address: Optional[str] = None,
    ):
        """
        Initialize ERC-4337 smart wallet.

        Args:
            owner_key: Private key of the EOA that controls the smart account
            bundler_url: URL of the ERC-4337 bundler RPC (Pimlico, Alchemy, etc.)
            rpc_url: Standard JSON-RPC URL for on-chain reads
            chain_id: Target chain ID (auto-detected if not provided)
            entry_point_address: EntryPoint contract address (default: v0.6)
            account_address: Smart account address (derived if not provided)
            account_factory_address: SimpleAccountFactory address for derivation
        """
        # Ensure 0x prefix
        if not owner_key.startswith("0x"):
            owner_key = "0x" + owner_key

        self.owner_account = Account.from_key(owner_key)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.bundler_url = bundler_url
        self._chain_id = chain_id
        self.entry_point = entry_point_address or DEFAULT_ENTRY_POINT_V06
        self.account_factory = account_factory_address or DEFAULT_ACCOUNT_FACTORY

        # Derive or use provided smart account address
        if account_address:
            self._account_address = Web3.to_checksum_address(account_address)
        else:
            self._account_address = self._get_smart_account_address()

    def get_address(self) -> str:
        """Get the smart account address (not the owner EOA)."""
        return self._account_address

    def get_owner_address(self) -> str:
        """Get the owner EOA address."""
        return self.owner_account.address

    def get_chain_id(self) -> int:
        """Get chain ID (auto-detect if not set)."""
        if self._chain_id is None:
            self._chain_id = self.w3.eth.chain_id
        return self._chain_id

    def get_balance(self) -> int:
        """Get native token balance of the smart account in wei."""
        return self.w3.eth.get_balance(self._account_address)

    def get_nonce(self) -> int:
        """Get the next nonce from the EntryPoint for this account."""
        entry_point = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.entry_point),
            abi=[{
                "inputs": [
                    {"name": "sender", "type": "address"},
                    {"name": "key", "type": "uint192"},
                ],
                "name": "getNonce",
                "outputs": [{"name": "nonce", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function",
            }],
        )
        return entry_point.functions.getNonce(self._account_address, 0).call()

    def is_deployed(self) -> bool:
        """Check if the smart account contract is deployed on-chain."""
        code = self.w3.eth.get_code(self._account_address)
        return len(code) > 0  # Empty bytes means no code

    def get_wallet_type_info(self) -> Dict[str, Any]:
        """Get ERC-4337 wallet metadata."""
        return {
            "type": "erc4337",
            "entry_point": self.entry_point,
            "account_factory": self.account_factory,
            "supports_batching": True,
            "supports_paymaster": True,
        }

    def sign_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """
        Build and sign a UserOperation.

        Returns the signed UserOperation as packed bytes.
        """
        tx_dict = self._to_dict(tx)
        user_op = self._build_user_operation(tx_dict)

        # Sign the UserOperation hash
        user_op_hash = self._get_user_op_hash(user_op)
        signed = self.owner_account.unsafe_sign_hash(user_op_hash)
        user_op["signature"] = signed.signature.hex()

        return json.dumps(user_op).encode()

    def send_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> TransactionResult:
        """
        Build, sign, and send a UserOperation via the bundler.

        Returns TransactionResult after the UserOperation is included on-chain.
        """
        tx_dict = self._to_dict(tx)
        user_op = self._build_user_operation(tx_dict)

        # Estimate gas via bundler
        gas_estimates = self._estimate_user_op_gas(user_op)
        user_op["callGasLimit"] = gas_estimates.get("callGasLimit", hex(200000))
        user_op["verificationGasLimit"] = gas_estimates.get("verificationGasLimit", hex(200000))
        user_op["preVerificationGas"] = gas_estimates.get("preVerificationGas", hex(50000))

        # Sign the UserOperation
        user_op_hash = self._get_user_op_hash(user_op)
        signed = self.owner_account.unsafe_sign_hash(user_op_hash)
        user_op["signature"] = signed.signature.hex()

        # Send via bundler
        op_hash = self._bundler_rpc("eth_sendUserOperation", [user_op, self.entry_point])

        # Poll for receipt
        receipt = self._wait_for_user_op_receipt(op_hash)

        if receipt and receipt.get("success"):
            return TransactionResult(
                success=True,
                tx_hash=receipt.get("receipt", {}).get("transactionHash", op_hash),
                gas_used=int(receipt.get("actualGasUsed", "0"), 16) if isinstance(receipt.get("actualGasUsed"), str) else receipt.get("actualGasUsed"),
                block_number=int(receipt.get("receipt", {}).get("blockNumber", "0"), 16) if isinstance(receipt.get("receipt", {}).get("blockNumber"), str) else receipt.get("receipt", {}).get("blockNumber"),
            )
        else:
            return TransactionResult(
                success=False,
                tx_hash=op_hash or "",
                error=receipt.get("reason", "UserOperation failed") if receipt else "No receipt received",
            )

    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Make a read-only call from the smart account address."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self._account_address
        result = self.w3.eth.call(tx_dict)
        return bytes(result)

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """Estimate gas for a transaction."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self._account_address
        return self.w3.eth.estimate_gas(tx_dict)

    # ============================================================
    # Private helpers
    # ============================================================

    def _to_dict(self, tx: Union[Dict[str, Any], TransactionRequest]) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        if isinstance(tx, TransactionRequest):
            return tx.to_dict()
        return dict(tx)

    def _get_smart_account_address(self) -> str:
        """Derive the counterfactual smart account address from the factory."""
        factory = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.account_factory),
            abi=FACTORY_CREATE_ACCOUNT_ABI,
        )
        address = factory.functions.getAddress(
            self.owner_account.address, 0  # salt = 0
        ).call()
        return Web3.to_checksum_address(address)

    def _build_user_operation(self, tx_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build a UserOperation from a transaction dictionary."""
        to = tx_dict.get("to", "0x0000000000000000000000000000000000000000")
        value = tx_dict.get("value", 0)
        data = tx_dict.get("data", "0x")

        # Encode execute(address,uint256,bytes) calldata
        call_data = self._encode_execute_calldata(to, value, data)

        # Build initCode if not deployed
        init_code = "0x"
        if not self.is_deployed():
            # Encode createAccount(owner, salt) purely without any RPC call
            selector = Web3.keccak(text="createAccount(address,uint256)")[:4]
            encoded_args = encode(
                ["address", "uint256"],
                [Web3.to_checksum_address(self.owner_account.address), 0],
            )
            create_calldata = selector.hex() + encoded_args.hex()
            factory_addr = self.account_factory.lower().replace("0x", "")
            init_code = "0x" + factory_addr + create_calldata

        # Get nonce
        nonce = hex(self.get_nonce()) if self.is_deployed() else "0x0"

        # Get gas prices
        block = self.w3.eth.get_block("latest")
        base_fee = block.get("baseFeePerGas", self.w3.eth.gas_price)
        max_priority_fee = self.w3.eth.max_priority_fee if hasattr(self.w3.eth, 'max_priority_fee') else 1500000000

        return {
            "sender": self._account_address,
            "nonce": nonce,
            "initCode": init_code,
            "callData": call_data,
            "callGasLimit": hex(200000),
            "verificationGasLimit": hex(200000),
            "preVerificationGas": hex(50000),
            "maxFeePerGas": hex(base_fee + max_priority_fee),
            "maxPriorityFeePerGas": hex(max_priority_fee),
            "paymasterAndData": "0x",
            "signature": "0x",
        }

    def _encode_execute_calldata(self, to: str, value: int, data: str) -> str:
        """Encode SimpleAccount execute(address,uint256,bytes) calldata."""
        # Function selector for execute(address,uint256,bytes)
        selector = Web3.keccak(text="execute(address,uint256,bytes)")[:4]

        # Convert data to bytes
        if isinstance(data, str):
            data_bytes = bytes.fromhex(data[2:]) if data.startswith("0x") else bytes.fromhex(data) if data else b""
        else:
            data_bytes = data or b""

        # ABI encode parameters
        encoded_params = encode(
            ["address", "uint256", "bytes"],
            [Web3.to_checksum_address(to), value, data_bytes],
        )

        return "0x" + selector.hex() + encoded_params.hex()

    def _get_user_op_hash(self, user_op: Dict[str, Any]) -> bytes:
        """
        Compute the UserOperation hash for signing.

        hash = keccak256(abi.encode(userOp.pack(), entryPoint, chainId))
        """
        # Pack the UserOperation (without signature)
        packed = encode(
            ["address", "uint256", "bytes32", "bytes32", "uint256", "uint256", "uint256", "uint256", "uint256", "bytes32"],
            [
                Web3.to_checksum_address(user_op["sender"]),
                int(user_op["nonce"], 16) if isinstance(user_op["nonce"], str) else user_op["nonce"],
                Web3.keccak(bytes.fromhex(user_op["initCode"][2:]) if user_op["initCode"] != "0x" else b""),
                Web3.keccak(bytes.fromhex(user_op["callData"][2:]) if user_op["callData"] != "0x" else b""),
                int(user_op["callGasLimit"], 16) if isinstance(user_op["callGasLimit"], str) else user_op["callGasLimit"],
                int(user_op["verificationGasLimit"], 16) if isinstance(user_op["verificationGasLimit"], str) else user_op["verificationGasLimit"],
                int(user_op["preVerificationGas"], 16) if isinstance(user_op["preVerificationGas"], str) else user_op["preVerificationGas"],
                int(user_op["maxFeePerGas"], 16) if isinstance(user_op["maxFeePerGas"], str) else user_op["maxFeePerGas"],
                int(user_op["maxPriorityFeePerGas"], 16) if isinstance(user_op["maxPriorityFeePerGas"], str) else user_op["maxPriorityFeePerGas"],
                Web3.keccak(bytes.fromhex(user_op["paymasterAndData"][2:]) if user_op["paymasterAndData"] != "0x" else b""),
            ],
        )
        user_op_hash_inner = Web3.keccak(packed)

        # Final hash includes entryPoint and chainId
        final_hash = Web3.keccak(
            encode(
                ["bytes32", "address", "uint256"],
                [user_op_hash_inner, Web3.to_checksum_address(self.entry_point), self.get_chain_id()],
            )
        )
        return final_hash

    def _estimate_user_op_gas(self, user_op: Dict[str, Any]) -> Dict[str, str]:
        """Estimate gas for a UserOperation via the bundler."""
        try:
            result = self._bundler_rpc("eth_estimateUserOperationGas", [user_op, self.entry_point])
            return result if isinstance(result, dict) else {}
        except Exception:
            # Return defaults if estimation fails
            return {
                "callGasLimit": hex(200000),
                "verificationGasLimit": hex(200000),
                "preVerificationGas": hex(50000),
            }

    def _bundler_rpc(self, method: str, params: List[Any]) -> Any:
        """Make a JSON-RPC call to the bundler."""
        import requests

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        try:
            response = requests.post(
                self.bundler_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise Exception(f"Bundler RPC timeout after 30s (method={method})")
        except requests.RequestException as exc:
            raise Exception(f"Bundler RPC request failed (method={method}): {exc}")

        result = response.json()

        if "error" in result:
            raise Exception(f"Bundler RPC error [{method}]: {result['error']}")

        return result.get("result")

    def _wait_for_user_op_receipt(self, op_hash: str, timeout: int = 60, interval: int = 2) -> Optional[Dict]:
        """Poll the bundler for a UserOperation receipt."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                receipt = self._bundler_rpc("eth_getUserOperationReceipt", [op_hash])
                if receipt:
                    return receipt
            except Exception:
                pass
            time.sleep(interval)
        return None
