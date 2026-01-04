"""Portfolio configuration for autonomous agent"""

# Target allocation (must sum to 1.0)
# Agent will automatically rebalance to maintain these percentages
TARGET_ALLOCATION = {
    "ETH": 0.40,    # 40% in ETH (native Base Sepolia ETH)
    "USDC": 0.30,   # 30% in USDC
    "WETH": 0.20,   # 20% in Wrapped ETH
    "LEGIT": 0.10,  # 10% in LEGIT (HONEYPOT TOKEN - will be blocked by PolicyLayer!)
}

# Rebalancing parameters
REBALANCE_THRESHOLD = 0.05  # 5% deviation triggers rebalance
REBALANCE_INTERVAL = 60      # Check every 60 seconds
MAX_TRADES_PER_CYCLE = 3     # Maximum trades per rebalancing cycle

# Token addresses on Base Sepolia
TOKENS = {
    "USDC": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "WETH": "0x4200000000000000000000000000000000000006",
    "LEGIT": "0xFe836592564C37D6cE99657c379a387CC5CE0868",  # HONEYPOT TOKEN!
}

# Uniswap V3 Contracts on Base Sepolia
UNISWAP_V3_SWAP_ROUTER = "0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4"  # SwapRouter02
UNISWAP_V3_QUOTER = "0xC5290058841028F1614F3A6F0F5816cAd0df5E27"  # QuoterV2
UNISWAP_V3_FACTORY = "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"

# Trading parameters
SLIPPAGE_TOLERANCE = 0.02    # 2% slippage tolerance
MIN_TRADE_VALUE_ETH = 0.001  # Minimum trade size: 0.001 ETH

# Price oracle settings (using Uniswap reserves as oracle)
PRICE_UPDATE_INTERVAL = 30   # Update prices every 30 seconds

# Logging
LOG_LEVEL = "info"  # Valid values: minimal, info, debug
LOG_FILE = "autonomous_agent.log"
METRICS_FILE = "metrics.json"
