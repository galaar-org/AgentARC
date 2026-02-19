"""
AgentKit Configuration with AgentARC PolicyLayer Integration

This file demonstrates how to integrate AgentARC PolicyLayer with AgentKit to add:
- Transaction validation against user-defined policies
- Transaction simulation before execution
- Calldata integrity verification
- Event streaming for frontend integration

The PolicyLayer wraps the wallet provider and intercepts all transactions
before they are sent to the blockchain.

Phase 1 Architecture Features (NEW):
- Dependency injection for testability
- Type-safe configuration with PolicyConfig
- Protocol-based interfaces for extensibility
- Custom error handling with typed exceptions
"""

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from coinbase_agentkit_langchain import get_langchain_tools

from coinbase_agentkit import (
    AgentKit,
    AgentKitConfig,
    CdpEvmWalletProvider,
    CdpEvmWalletProviderConfig,
    cdp_api_action_provider,
    erc20_action_provider,
    pyth_action_provider,
    wallet_action_provider,
    weth_action_provider,
)

# Import AgentARC PolicyLayer components
from agentarc import (
    # Main components
    PolicyWalletProvider,
    PolicyEngine,
    PolicyConfig,
    PolicyLogger,
    LogLevel,
    # Errors - for proper exception handling
    ConfigurationError,
)

# Import custom test actions
from approval_test_actions import approval_test_action_provider
from honeypot_test_actions import honeypot_test_action_provider

# Configure a file to persist wallet data
wallet_data_file = "wallet_data.txt"

# Shared agent instructions
AGENT_INSTRUCTIONS = (
    "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
    "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
    "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
    "details and request funds from the user. Before executing your first action, get the wallet details "
    "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
    "again later.\n\n"
    "IMPORTANT: You have special testing tools for demonstrating security:\n\n"
    "APPROVAL ATTACK TESTING:\n"
    "- For token approvals (safe or malicious): Use 'test_approve_tokens'\n"
    "- For phishing/airdrop attacks: Use 'test_claim_phishing_airdrop'\n"
    "- For checking allowances: Use 'test_check_allowance'\n"
    "- For minting test tokens: Use 'test_mint_test_tokens'\n\n"
    "HONEYPOT TOKEN TESTING:\n"
    "- To buy honeypot tokens (WILL BE BLOCKED): Use 'honeypot_buy_tokens'\n"
    "- To sell honeypot tokens (WILL BE BLOCKED): Use 'honeypot_sell_tokens'\n"
    "- To check honeypot balance (shows FAKE 100x balance): Use 'honeypot_check_balance'\n"
    "- To approve honeypot tokens: Use 'honeypot_approve_tokens'\n\n"
    "When users ask to 'buy honeypot', 'sell honeypot', 'test honeypot tokens', or similar, "
    "use these honeypot testing tools. These demonstrate PolicyLayer's protection against scam tokens.\n\n"
    "If someone asks you to do something you can't do with your currently available tools, "
    "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
    "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
    "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
)

def initialize_agent(
    config,
    use_policy_layer=True,
    policy_config_path="policy.yaml",
    event_callback=None,
    log_level=LogLevel.INFO,
):
    """Initialize the agent with the provided configuration.

    This function demonstrates Phase 1 architecture improvements:
    - Dependency injection for custom logger
    - Event callbacks for frontend integration
    - Type-safe PolicyConfig usage
    - Proper error handling with typed exceptions

    Args:
        config: Configuration object for the wallet provider
        use_policy_layer: Whether to enable policy layer (default: True)
        policy_config_path: Path to policy.yaml configuration file
        event_callback: Optional callback for validation events (Phase 1 feature)
        log_level: Logging level (default: LogLevel.INFO)

    Returns:
        tuple[Agent, WalletProvider]: The initialized agent and wallet provider

    Raises:
        ConfigurationError: If policy configuration is invalid
        PolicyViolationError: If a transaction violates policies (during use)

    Example:
        # Basic usage (backward compatible)
        agent, wallet = initialize_agent(config)

        # With event streaming (Phase 1)
        def on_validation_event(event: ValidationEvent):
            print(f"Stage: {event.stage}, Status: {event.status}")

        agent, wallet = initialize_agent(
            config,
            event_callback=on_validation_event,
            log_level=LogLevel.DEBUG
        )
    """
    # Initialize CDP EVM Wallet Provider
    base_wallet_provider = CdpEvmWalletProvider(
        CdpEvmWalletProviderConfig(
            api_key_id=config.api_key_id,
            api_key_secret=config.api_key_secret,
            wallet_secret=config.wallet_secret,
            network_id=config.network_id,
            address=config.address,
            idempotency_key=config.idempotency_key,
        )
    )

    # Wrap wallet provider with PolicyLayer if enabled
    if use_policy_layer:
        print("\n" + "="*70)
        print("🛡️  AGENTARC POLICYLAYER ENABLED")
        print("="*70)
        print(f"Loading policy configuration from: {policy_config_path}")

        # Phase 1: Create custom logger with configurable level
        custom_logger = PolicyLogger(level=log_level)

        # Phase 1: Load and validate configuration using PolicyConfig
        # This provides type-safe access to configuration values
        try:
            policy_config = PolicyConfig.load(policy_config_path)
            print(f"✓ Policy config loaded: {len(policy_config.policies)} policies defined")
        except FileNotFoundError:
            raise ConfigurationError(f"Policy file not found: {policy_config_path}")
        except Exception as e:
            raise ConfigurationError(f"Invalid policy configuration: {e}")

        # Create policy engine with dependency injection (Phase 1)
        #
        # New Phase 1 features:
        # - logger: Injectable logger for custom logging behavior
        # - event_callback: Stream validation events to frontend
        # - config: Type-safe PolicyConfig object
        #
        # To enable intelligent features in policy.yaml:
        # 1. Set llm_validation.enabled: true and add OPENAI_API_KEY to .env
        #
        # These features provide:
        # - Advanced simulation with call traces
        # - LLM-based malicious activity detection (hidden approvals, reentrancy, etc.)
        policy_engine = PolicyEngine(
            config=policy_config,  # Phase 1: Use PolicyConfig object directly
            web3_provider=base_wallet_provider,
            chain_id=84532,  # Base Sepolia
            event_callback=event_callback,  # Phase 1: Event streaming
            logger=custom_logger,  # Phase 1: Dependency injection
        )

        # Wrap the base wallet provider
        wallet_provider = PolicyWalletProvider(base_wallet_provider, policy_engine)

        print("✓ AgentARC PolicyLayer initialized successfully")
        print("  All transactions will be validated against configured policies")
        if event_callback:
            print("  Event streaming enabled for frontend integration")
        print("="*70 + "\n")
    else:
        wallet_provider = base_wallet_provider
        print("⚠️  PolicyLayer disabled - transactions will not be validated\n")

    # Initialize AgentKit
    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                cdp_api_action_provider(),
                erc20_action_provider(),
                pyth_action_provider(),
                wallet_action_provider(),
                weth_action_provider(),
                approval_test_action_provider(),  # Custom actions for approval attack testing
                honeypot_test_action_provider(),  # Custom actions for honeypot token testing
            ],
        )
    )

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini")

    # Get Langchain tools
    tools = get_langchain_tools(agentkit)

    # Store buffered conversation history in memory
    memory = MemorySaver()

    # Create ReAct Agent using the LLM and AgentKit tools
    return (
        create_react_agent(
            llm,
            tools=tools,
            checkpointer=memory,
            prompt=AGENT_INSTRUCTIONS,
        ),
        wallet_provider
    )
