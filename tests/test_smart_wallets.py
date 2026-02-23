"""
Tests for smart wallet adapters (SmartWalletAdapter, ERC4337Adapter, SafeAdapter).

Uses unittest.mock to mock web3 and bundler RPC calls.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from agentarc.core.types import TransactionRequest, TransactionResult, WalletType
from agentarc.wallets.adapters.smart_wallet_base import SmartWalletAdapter
from agentarc.wallets.adapters.erc4337 import ERC4337Adapter, DEFAULT_ENTRY_POINT_V06
from agentarc.wallets.adapters.safe_adapter import SafeAdapter


# ============================================================
# Test WalletType enum additions
# ============================================================

class TestWalletTypeEnum:
    def test_erc4337_type_exists(self):
        assert WalletType.ERC4337 == "erc4337"

    def test_safe_type_exists(self):
        assert WalletType.SAFE == "safe"

    def test_smart_contract_still_exists(self):
        assert WalletType.SMART_CONTRACT == "smart_contract"


# ============================================================
# Test SmartWalletAdapter ABC
# ============================================================

class TestSmartWalletAdapterABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            SmartWalletAdapter()

    def test_requires_owner_address(self):
        """SmartWalletAdapter requires get_owner_address to be implemented."""
        class IncompleteWallet(SmartWalletAdapter):
            def get_address(self): return "0x1"
            def get_chain_id(self): return 1
            def get_balance(self): return 0
            def sign_transaction(self, tx): return b""
            def send_transaction(self, tx): return TransactionResult(tx_hash="0x", success=True)
            def call(self, tx): return b""
            # Missing: get_owner_address, is_deployed, get_wallet_type_info

        with pytest.raises(TypeError):
            IncompleteWallet()


# ============================================================
# Test ERC4337Adapter
# ============================================================

# Test private key (DO NOT use in production)
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_OWNER_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"


class TestERC4337Adapter:
    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_constructor_with_account_address(self, MockWeb3):
        """Test construction with a provided account address."""
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount1234567890123456789012345678",
        )

        assert adapter.get_owner_address() == TEST_OWNER_ADDRESS
        assert adapter.get_chain_id() == 84532
        assert adapter.entry_point == DEFAULT_ENTRY_POINT_V06

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_get_address_returns_smart_account(self, MockWeb3):
        """get_address() should return smart account address, not owner."""
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        assert adapter.get_address() == "0xSmartAccount"
        assert adapter.get_address() != adapter.get_owner_address()

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_is_deployed_true(self, MockWeb3):
        """is_deployed() returns True when contract has code."""
        mock_w3 = MagicMock()
        mock_w3.eth.get_code.return_value = b"\x60\x60\x60"  # Some bytecode
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        assert adapter.is_deployed() is True

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_is_deployed_false(self, MockWeb3):
        """is_deployed() returns False when no contract code."""
        mock_w3 = MagicMock()
        mock_w3.eth.get_code.return_value = b""
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        assert adapter.is_deployed() is False

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_get_balance(self, MockWeb3):
        """get_balance() returns balance of the smart account."""
        mock_w3 = MagicMock()
        mock_w3.eth.get_balance.return_value = 5000000000000000000  # 5 ETH
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        assert adapter.get_balance() == 5000000000000000000

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_get_wallet_type_info(self, MockWeb3):
        """get_wallet_type_info() returns ERC-4337 metadata."""
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        info = adapter.get_wallet_type_info()
        assert info["type"] == "erc4337"
        assert info["entry_point"] == DEFAULT_ENTRY_POINT_V06
        assert info["supports_batching"] is True
        assert info["supports_paymaster"] is True

    @patch("agentarc.wallets.adapters.erc4337.Web3")
    def test_to_dict_includes_smart_wallet_fields(self, MockWeb3):
        """to_dict() should include owner, deployed status, and type info."""
        mock_w3 = MagicMock()
        mock_w3.eth.get_code.return_value = b"\x60"
        mock_w3.eth.chain_id = 84532
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = ERC4337Adapter(
            owner_key=TEST_PRIVATE_KEY,
            bundler_url="https://bundler.example.com",
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            account_address="0xSmartAccount",
        )

        d = adapter.to_dict()
        assert "owner_address" in d
        assert "is_deployed" in d
        assert "wallet_type_info" in d
        assert d["owner_address"] == TEST_OWNER_ADDRESS


# ============================================================
# Test SafeAdapter
# ============================================================

class TestSafeAdapter:
    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_constructor(self, MockWeb3):
        """Test basic construction."""
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        assert adapter.get_address() == "0xSafeAddress"
        assert adapter.get_owner_address() == TEST_OWNER_ADDRESS
        assert adapter.get_chain_id() == 84532
        assert adapter.auto_execute is True

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_get_address_returns_safe_address(self, MockWeb3):
        """get_address() should return the Safe contract address."""
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        assert adapter.get_address() == "0xSafeAddress"

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_is_deployed_true(self, MockWeb3):
        """is_deployed() returns True when Safe has code."""
        mock_w3 = MagicMock()
        # get_code returns bytecode regardless of address argument
        mock_w3.eth.get_code = Mock(return_value=b"\x60\x60\x60")
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        result = adapter.is_deployed()
        assert result is True

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_get_balance(self, MockWeb3):
        """get_balance() returns balance of the Safe."""
        mock_w3 = MagicMock()
        mock_w3.eth.get_balance.return_value = 10000000000000000000  # 10 ETH
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        assert adapter.get_balance() == 10000000000000000000

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_get_threshold(self, MockWeb3):
        """get_threshold() reads from the Safe contract."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.getThreshold.return_value.call.return_value = 2
        mock_w3.eth.contract.return_value = mock_contract
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        assert adapter.get_threshold() == 2

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_get_owners(self, MockWeb3):
        """get_owners() reads owner list from the Safe contract."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        owners = [TEST_OWNER_ADDRESS, "0xOwner2"]
        mock_contract.functions.getOwners.return_value.call.return_value = owners
        mock_w3.eth.contract.return_value = mock_contract
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        assert adapter.get_owners() == owners

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_get_wallet_type_info(self, MockWeb3):
        """get_wallet_type_info() returns Safe metadata."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.getThreshold.return_value.call.return_value = 1
        mock_contract.functions.getOwners.return_value.call.return_value = [TEST_OWNER_ADDRESS]
        mock_w3.eth.contract.return_value = mock_contract
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
        )

        info = adapter.get_wallet_type_info()
        assert info["type"] == "safe"
        assert info["threshold"] == 1
        assert info["auto_execute"] is True

    @patch("agentarc.wallets.adapters.safe_adapter.Web3")
    def test_send_transaction_pending_when_threshold_not_met(self, MockWeb3):
        """send_transaction() returns pending result when threshold > 1."""
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_contract.functions.getThreshold.return_value.call.return_value = 2
        mock_contract.functions.nonce.return_value.call.return_value = 0
        mock_contract.functions.getTransactionHash.return_value.call.return_value = b"\x00" * 32
        mock_w3.eth.contract.return_value = mock_contract
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider = Mock()
        MockWeb3.to_checksum_address = lambda x: x

        adapter = SafeAdapter(
            safe_address="0xSafeAddress",
            signer_key=TEST_PRIVATE_KEY,
            rpc_url="https://rpc.example.com",
            chain_id=84532,
            auto_execute=True,
        )

        result = adapter.send_transaction({
            "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
            "value": 1000000000000000000,
            "data": "0x",
        })

        # Should be pending since threshold=2 but only 1 signature
        assert result.success is False
        assert "co-signers" in result.error


# ============================================================
# Test WalletFactory integration
# ============================================================

class TestWalletFactoryIntegration:
    def test_from_erc4337_method_exists(self):
        """WalletFactory should have from_erc4337 method."""
        from agentarc.wallets.factory import WalletFactory
        assert hasattr(WalletFactory, "from_erc4337")

    def test_from_safe_method_exists(self):
        """WalletFactory should have from_safe method."""
        from agentarc.wallets.factory import WalletFactory
        assert hasattr(WalletFactory, "from_safe")


# ============================================================
# Test top-level imports
# ============================================================

class TestTopLevelImports:
    def test_import_smart_wallet_adapter(self):
        from agentarc import SmartWalletAdapter
        assert SmartWalletAdapter is not None

    def test_import_erc4337_adapter(self):
        from agentarc import ERC4337Adapter
        assert ERC4337Adapter is not None

    def test_import_safe_adapter(self):
        from agentarc import SafeAdapter
        assert SafeAdapter is not None

    def test_import_wallet_factory(self):
        from agentarc import WalletFactory
        assert hasattr(WalletFactory, "from_erc4337")
        assert hasattr(WalletFactory, "from_safe")
