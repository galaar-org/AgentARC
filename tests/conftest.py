"""
Shared test fixtures for AgentARC.

Provides mock objects and factory functions to reduce test boilerplate.
All fixtures are designed to work with dependency injection patterns.

Usage:
    pytest tests/ -v

Example:
    def test_policy_engine(policy_engine_factory, sample_eth_transfer):
        engine = policy_engine_factory()
        passed, reason = engine.validate_transaction(sample_eth_transfer, "0xfrom")
        assert passed
"""
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass


# ============================================================
# Mock Factories
# ============================================================

@pytest.fixture
def mock_logger():
    """
    Create a mock logger that implements LoggerProtocol.
    
    Returns:
        Mock object with all logger methods
    """
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.success = Mock()
    logger.minimal = Mock()
    logger.section = Mock()
    logger.subsection = Mock()
    return logger


@pytest.fixture
def mock_simulator():
    """
    Create a mock basic simulator with configurable responses.
    
    Returns:
        Mock simulator that returns success by default
    """
    from agentarc.simulator import SimulationResult
    
    simulator = Mock()
    simulator.simulate = Mock(return_value=SimulationResult(
        success=True,
        error=None,
        gas_used=21000
    ))
    simulator.estimate_gas = Mock(return_value=21000)
    return simulator


@pytest.fixture
def mock_tenderly_simulator():
    """
    Create a mock Tenderly simulator.
    
    Returns:
        Mock Tenderly simulator with empty but valid results
    """
    # Create mock result class
    @dataclass
    class MockTenderlyResult:
        success: bool = True
        error: Optional[str] = None
        gas_used: int = 50000
        call_trace: List = None
        asset_changes: List = None
        logs: List = None
        
        def __post_init__(self):
            self.call_trace = self.call_trace or []
            self.asset_changes = self.asset_changes or []
            self.logs = self.logs or []
        
        def has_data(self):
            return bool(self.call_trace or self.asset_changes or self.logs)
    
    simulator = Mock()
    simulator.simulate = Mock(return_value=MockTenderlyResult())
    simulator.estimate_gas = Mock(return_value=50000)
    simulator.is_available = Mock(return_value=True)
    return simulator


@pytest.fixture
def mock_llm_judge():
    """
    Create a mock LLM judge that always passes (returns None).
    
    Returns:
        Mock LLM judge that indicates no malicious activity
    """
    judge = Mock()
    judge.analyze = Mock(return_value=None)  # None = no malicious activity
    return judge


@pytest.fixture
def mock_llm_judge_blocking():
    """
    Create a mock LLM judge that always blocks.
    
    Returns:
        Mock LLM judge that indicates malicious activity
    """
    @dataclass
    class MockLLMAnalysis:
        is_malicious: bool = True
        confidence: float = 0.95
        risk_level: str = "CRITICAL"
        reason: str = "Test: Malicious pattern detected"
        indicators: List[str] = None
        recommended_action: str = "BLOCK"
        
        def __post_init__(self):
            self.indicators = self.indicators or ["test_indicator"]
        
        def should_block(self, threshold: float = 0.7) -> bool:
            return self.confidence >= threshold
        
        def should_warn(self, threshold: float = 0.4) -> bool:
            return self.confidence >= threshold
    
    judge = Mock()
    judge.analyze = Mock(return_value=MockLLMAnalysis())
    return judge


@pytest.fixture
def mock_calldata_parser():
    """
    Create a mock calldata parser.
    
    Returns:
        Mock parser that returns a basic ParsedTransaction
    """
    from agentarc.calldata_parser import ParsedTransaction
    
    parser = Mock()
    parser.parse = Mock(return_value=ParsedTransaction(
        to="0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        value=0,
        function_name=None,
        function_selector=None,
        decoded_params={},
        raw_calldata=b"",
        recipient_address=None,
        token_amount=None,
        token_address=None,
    ))
    return parser


# ============================================================
# Transaction Fixtures
# ============================================================

@pytest.fixture
def sample_eth_transfer() -> Dict[str, Any]:
    """
    Simple ETH transfer transaction.
    
    Returns:
        Transaction dict for 1 ETH transfer
    """
    return {
        "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        "value": 1000000000000000000,  # 1 ETH
        "data": "0x",
        "gas": 21000,
    }


@pytest.fixture
def sample_eth_transfer_small() -> Dict[str, Any]:
    """
    Small ETH transfer (0.1 ETH).
    
    Returns:
        Transaction dict for 0.1 ETH transfer
    """
    return {
        "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        "value": 100000000000000000,  # 0.1 ETH
        "data": "0x",
        "gas": 21000,
    }


@pytest.fixture
def sample_erc20_transfer() -> Dict[str, Any]:
    """
    ERC20 token transfer transaction.
    
    Returns:
        Transaction dict for USDC transfer (10 USDC)
    """
    # transfer(address to, uint256 amount)
    # Selector: 0xa9059cbb
    # to: 0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0
    # amount: 10000000 (10 USDC with 6 decimals)
    return {
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC mainnet
        "value": 0,
        "data": "0xa9059cbb000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f5a5b00000000000000000000000000000000000000000000000000000000000989680",
        "gas": 100000,
    }


@pytest.fixture
def sample_erc20_approve_unlimited() -> Dict[str, Any]:
    """
    ERC20 unlimited approval transaction.
    
    Returns:
        Transaction dict for unlimited USDC approval
    """
    # approve(address spender, uint256 amount)
    # Selector: 0x095ea7b3
    # spender: 0x1234567890123456789012345678901234567890
    # amount: max uint256
    return {
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "value": 0,
        "data": "0x095ea7b3000000000000000000000000123456789012345678901234567890123456789ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "gas": 50000,
    }


@pytest.fixture
def sample_contract_call() -> Dict[str, Any]:
    """
    Generic contract call with value.
    
    Returns:
        Transaction dict for contract call with 0.5 ETH
    """
    return {
        "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap Router
        "value": 500000000000000000,  # 0.5 ETH
        "data": "0x7ff36ab5000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000800000000000000000000000001234567890123456789012345678901234567890000000000000000000000000000000000000000000000000000000006789abcd",
        "gas": 250000,
    }


# ============================================================
# Parsed Transaction Fixtures
# ============================================================

@pytest.fixture
def parsed_eth_transfer():
    """
    Parsed ETH transfer transaction.
    
    Returns:
        ParsedTransaction for simple ETH transfer
    """
    from agentarc.calldata_parser import ParsedTransaction
    
    return ParsedTransaction(
        to="0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        value=1000000000000000000,
        function_name=None,
        function_selector=None,
        decoded_params={},
        raw_calldata=b"",
        recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        token_amount=None,
        token_address=None,
    )


@pytest.fixture
def parsed_erc20_transfer():
    """
    Parsed ERC20 transfer transaction.
    
    Returns:
        ParsedTransaction for token transfer
    """
    from agentarc.calldata_parser import ParsedTransaction
    
    return ParsedTransaction(
        to="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        value=0,
        function_name="transfer",
        function_selector="0xa9059cbb",
        decoded_params={
            "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
            "amount": 10000000,
        },
        raw_calldata=bytes.fromhex("a9059cbb000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f5a5b00000000000000000000000000000000000000000000000000000000000989680"),
        recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0",
        token_amount=10000000,
        token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    )


# ============================================================
# Configuration Fixtures
# ============================================================

@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """
    Sample policy configuration dictionary.
    
    Returns:
        Complete configuration dict with common policies
    """
    return {
        "version": "2.0",
        "enabled": True,
        "logging": {"level": "debug"},
        "policies": [
            {
                "type": "eth_value_limit",
                "max_value_wei": "1000000000000000000",  # 1 ETH
                "enabled": True,
            },
            {
                "type": "address_denylist",
                "denied_addresses": ["0xbad0000000000000000000000000000000000bad"],
                "enabled": True,
            },
            {
                "type": "gas_limit",
                "max_gas": 500000,
                "enabled": True,
            },
        ],
        "simulation": {"enabled": True, "fail_on_revert": True},
        "calldata_validation": {"enabled": True},
        "llm_validation": {"enabled": False},
    }


@pytest.fixture
def sample_config_dict_strict() -> Dict[str, Any]:
    """
    Strict policy configuration with low limits.
    
    Returns:
        Configuration dict with restrictive policies
    """
    return {
        "version": "2.0",
        "enabled": True,
        "logging": {"level": "debug"},
        "policies": [
            {
                "type": "eth_value_limit",
                "max_value_wei": "100000000000000000",  # 0.1 ETH
                "enabled": True,
            },
            {
                "type": "gas_limit",
                "max_gas": 100000,
                "enabled": True,
            },
        ],
        "simulation": {"enabled": False},
        "llm_validation": {"enabled": False},
    }


@pytest.fixture
def sample_config_disabled() -> Dict[str, Any]:
    """
    Configuration with PolicyLayer disabled.
    
    Returns:
        Configuration dict with enabled=False
    """
    return {
        "version": "2.0",
        "enabled": False,
        "policies": [],
    }


# ============================================================
# Policy Engine Factory
# ============================================================

@pytest.fixture
def policy_engine_factory(
    mock_logger,
    mock_simulator,
    mock_tenderly_simulator,
    mock_llm_judge,
):
    """
    Factory for creating PolicyEngine with injectable mocks.
    
    Usage:
        engine = policy_engine_factory()  # Default config
        engine = policy_engine_factory(config_dict={...})  # Custom config
        engine = policy_engine_factory(use_tenderly=True)  # With Tenderly mock
    
    Returns:
        Factory function that creates configured PolicyEngine instances
    """
    from agentarc.policy_engine import PolicyEngine
    from agentarc.core.config import PolicyConfig
    
    def create_engine(
        config_dict: Optional[Dict[str, Any]] = None,
        use_tenderly: bool = False,
        use_llm: bool = False,
        use_real_parser: bool = True,
    ) -> PolicyEngine:
        """
        Create a PolicyEngine with mocked dependencies.
        
        Args:
            config_dict: Custom config (default: minimal config)
            use_tenderly: Whether to inject mock Tenderly simulator
            use_llm: Whether to inject mock LLM judge
            use_real_parser: Whether to use real CalldataParser (default: True)
        
        Returns:
            Configured PolicyEngine ready for testing
        """
        if config_dict is None:
            config_dict = {
                "version": "2.0",
                "enabled": True,
                "policies": [
                    {"type": "eth_value_limit", "max_value_wei": "1000000000000000000", "enabled": True},
                    {"type": "gas_limit", "max_gas": 500000, "enabled": True},
                ],
                "simulation": {"enabled": True},
                "llm_validation": {"enabled": use_llm},
            }
        
        config = PolicyConfig(config_dict)
        
        # Use real parser by default for accurate testing
        calldata_parser = None if use_real_parser else mock_calldata_parser
        
        return PolicyEngine(
            config=config,
            logger=mock_logger,
            simulator=mock_simulator,
            tenderly_simulator=mock_tenderly_simulator if use_tenderly else None,
            llm_judge=mock_llm_judge if use_llm else None,
            calldata_parser=calldata_parser,
        )
    
    return create_engine


# ============================================================
# Utility Fixtures
# ============================================================

@pytest.fixture
def sample_from_address() -> str:
    """
    Sample wallet address for testing.
    
    Returns:
        Valid Ethereum address
    """
    return "0x1234567890123456789012345678901234567890"


@pytest.fixture
def denied_address() -> str:
    """
    Sample denied address for denylist testing.
    
    Returns:
        Address that should be on denylist
    """
    return "0xbad0000000000000000000000000000000000bad"
