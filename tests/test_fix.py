#!/usr/bin/env python3
"""
Test the ETH value limit fix
"""

from decimal import Decimal
from agentguard import PolicyWalletProvider, PolicyEngine, PolicyViolationError


class MockWalletProvider:
    """Mock wallet for testing"""
    def __init__(self):
        self.address = "0x1234567890123456789012345678901234567890"
        self.web3 = None

    def get_address(self) -> str:
        return self.address

    def get_network(self):
        return {"name": "base-sepolia", "chain_id": 84532}

    def get_balance(self) -> Decimal:
        return Decimal("10")

    def send_transaction(self, transaction: dict) -> str:
        return "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def get_name(self) -> str:
        return "MockWallet"


def main():
    print("\n" + "="*70)
    print("Testing ETH Value Limit Fix")
    print("="*70)

    wallet = MockWalletProvider()
    policy_engine = PolicyEngine(config_path="policy_v2.yaml")
    policy_wallet = PolicyWalletProvider(wallet, policy_engine)

    # Test 1: 1.5 ETH transfer (should NOW be blocked!)
    print("\nTest 1: Transfer 1.5 ETH (should be BLOCKED)")
    print("-" * 70)
    try:
        tx = {
            "to": "0x6Cc9397c3B38739daCbfaA68EaD5F5D77Ba5F455",
            "value": 1500000000000000000,  # 1.5 ETH
            "gas": 21000,
            "data": "0x"
        }
        result = policy_wallet.send_transaction(tx)
        print(f"❌ BUG STILL EXISTS: 1.5 ETH transfer was allowed!")
        print(f"   Transaction hash: {result}")
    except PolicyViolationError as e:
        print(f"✅ FIXED: 1.5 ETH transfer was correctly blocked!")
        print(f"   Reason: {e}")

    # Test 2: 0.5 ETH transfer (should be allowed)
    print("\nTest 2: Transfer 0.5 ETH (should be ALLOWED)")
    print("-" * 70)
    try:
        tx = {
            "to": "0x6Cc9397c3B38739daCbfaA68EaD5F5D77Ba5F455",
            "value": 500000000000000000,  # 0.5 ETH
            "gas": 21000,
            "data": "0x"
        }
        result = policy_wallet.send_transaction(tx)
        print(f"✅ CORRECT: 0.5 ETH transfer was allowed")
        print(f"   Transaction hash: {result}")
    except PolicyViolationError as e:
        print(f"❌ ERROR: 0.5 ETH transfer should be allowed!")
        print(f"   Reason: {e}")

    # Test 3: Exactly 1 ETH (should be allowed)
    print("\nTest 3: Transfer 1.0 ETH (should be ALLOWED - at limit)")
    print("-" * 70)
    try:
        tx = {
            "to": "0x6Cc9397c3B38739daCbfaA68EaD5F5D77Ba5F455",
            "value": 1000000000000000000,  # 1.0 ETH (exactly at limit)
            "gas": 21000,
            "data": "0x"
        }
        result = policy_wallet.send_transaction(tx)
        print(f"✅ CORRECT: 1.0 ETH transfer was allowed")
        print(f"   Transaction hash: {result}")
    except PolicyViolationError as e:
        print(f"❌ ERROR: 1.0 ETH transfer should be allowed!")
        print(f"   Reason: {e}")

    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
