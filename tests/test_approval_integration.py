#!/usr/bin/env python3
"""
Real Integration Test for Hidden Token Approvals

This test uses REAL deployed contracts on a local blockchain (Anvil)
and validates that PolicyLayer correctly blocks malicious approvals.

Prerequisites:
    1. Install Foundry: https://book.getfoundry.sh/getting-started/installation
    2. pip install web3

Setup & Run:
    # Terminal 1: Start Anvil
    anvil

    # Terminal 2: Deploy contracts
    cd tests/contracts
    forge script script/DeployContracts.s.sol:DeployContracts --rpc-url http://127.0.0.1:8545 --broadcast

    # Terminal 3: Run integration test
    python tests/test_approval_integration.py
"""

import os
import sys
import json
from pathlib import Path
from web3 import Web3
from eth_account import Account

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentguard.policy_engine import PolicyEngine


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_test_header(test_num, name):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}TEST {test_num}: {name}{Colors.END}")
    print("="*80)


def print_result(passed, expected_block):
    """Print test result"""
    if (passed and not expected_block) or (not passed and expected_block):
        print(f"\n{Colors.GREEN}✅ TEST PASSED{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}❌ TEST FAILED{Colors.END}")
        return False


def main():
    print(f"\n{Colors.BOLD}{'='*80}")
    print("REAL APPROVAL ATTACK INTEGRATION TEST")
    print(f"{'='*80}{Colors.END}\n")

    # ============================================================
    # STEP 1: Load Deployment Info
    # ============================================================
    deployments_path = Path(__file__).parent / "contracts" / "deployments.json"

    if not deployments_path.exists():
        print(f"{Colors.RED}❌ deployments.json not found!{Colors.END}")
        print("\nPlease deploy contracts first:")
        print("  cd tests/contracts")
        print("  forge script script/DeployContracts.s.sol:DeployContracts --rpc-url http://127.0.0.1:8545 --broadcast")
        return

    with open(deployments_path) as f:
        deployments = json.load(f)

    print(f"{Colors.BLUE}📋 Loaded deployment info:{Colors.END}")
    print(f"  Token:       {deployments['token']}")
    print(f"  Malicious:   {deployments['malicious']}")
    print(f"  Phishing:    {deployments['phishing']}")
    print(f"  Whitelisted: {deployments['whitelisted']}")
    print(f"  Deployer:    {deployments['deployer']}")

    # ============================================================
    # STEP 2: Connect to Local Blockchain
    # ============================================================
    rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print(f"\n{Colors.RED}❌ Failed to connect to {rpc_url}{Colors.END}")
        print("\nPlease start Anvil:")
        print("  anvil")
        return

    print(f"\n{Colors.GREEN}✅ Connected to blockchain{Colors.END}")
    print(f"  Chain ID: {w3.eth.chain_id}")
    print(f"  Block: {w3.eth.block_number}")

    # ============================================================
    # STEP 3: Setup Test Account (Use Anvil default account)
    # ============================================================
    # Anvil default private key
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    user_account = Account.from_key(private_key)
    user_address = user_account.address

    print(f"\n{Colors.BLUE}👤 Test account:{Colors.END}")
    print(f"  Address: {user_address}")
    print(f"  Balance: {w3.from_wei(w3.eth.get_balance(user_address), 'ether')} ETH")

    # ============================================================
    # STEP 4: Load Token ABI
    # ============================================================
    # Minimal ERC20 ABI
    erc20_abi = [
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]

    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(deployments['token']),
        abi=erc20_abi
    )

    user_balance = token_contract.functions.balanceOf(user_address).call()
    print(f"  Token Balance: {w3.from_wei(user_balance, 'ether')} MOCK")

    # ============================================================
    # STEP 5: Initialize PolicyLayer
    # ============================================================
    print(f"\n{Colors.BLUE}🛡️  Initializing PolicyLayer...{Colors.END}")

    config_path = Path(__file__).parent.parent / "policy_v2.yaml"
    policy_engine = PolicyEngine(
        config_path=str(config_path),
        web3_provider=w3,
        chain_id=w3.eth.chain_id
    )

    print(f"{Colors.GREEN}✅ PolicyLayer initialized{Colors.END}")

    # ============================================================
    # TEST SUITE
    # ============================================================
    results = []
    max_uint256 = 2**256 - 1

    # TEST 1: Unlimited Approval to Unknown Malicious Contract
    print_test_header(1, "Unlimited Approval to Unknown Malicious Contract")
    print(f"Description: User approves max uint256 to {deployments['malicious']}")
    print(f"Expected: {Colors.RED}❌ BLOCK{Colors.END}")

    tx1 = {
        'from': user_address,
        'to': Web3.to_checksum_address(deployments['token']),
        'value': 0,
        'gas': 100000,
        'data': token_contract.encodeABI(
            fn_name='approve',
            args=[Web3.to_checksum_address(deployments['malicious']), max_uint256]
        )
    }

    passed1, reason1 = policy_engine.validate_transaction(tx1, user_address)
    print(f"\nPolicyLayer result: {'ALLOWED' if passed1 else 'BLOCKED'}")
    print(f"Reason: {reason1}")

    result1 = print_result(passed1, expected_block=True)
    results.append(("Test 1: Unlimited to Malicious", result1))

    # TEST 2: Unlimited Approval to Whitelisted Contract
    print_test_header(2, "Unlimited Approval to Whitelisted Contract")
    print(f"Description: User approves max uint256 to {deployments['whitelisted']}")
    print(f"Expected: {Colors.GREEN}✅ ALLOW{Colors.END} (if whitelisted in policy)")

    tx2 = {
        'from': user_address,
        'to': Web3.to_checksum_address(deployments['token']),
        'value': 0,
        'gas': 100000,
        'data': token_contract.encodeABI(
            fn_name='approve',
            args=[Web3.to_checksum_address(deployments['whitelisted']), max_uint256]
        )
    }

    passed2, reason2 = policy_engine.validate_transaction(tx2, user_address)
    print(f"\nPolicyLayer result: {'ALLOWED' if passed2 else 'BLOCKED'}")
    print(f"Reason: {reason2}")

    result2 = print_result(passed2, expected_block=False)
    results.append(("Test 2: Unlimited to Whitelisted", result2))

    # TEST 3: Limited Approval to Unknown Contract
    print_test_header(3, "Limited Approval to Unknown Contract")
    limited_amount = w3.to_wei(100, 'ether')
    print(f"Description: User approves only 100 tokens to {deployments['malicious']}")
    print(f"Expected: {Colors.GREEN}✅ ALLOW{Colors.END} (limited amount)")

    tx3 = {
        'from': user_address,
        'to': Web3.to_checksum_address(deployments['token']),
        'value': 0,
        'gas': 100000,
        'data': token_contract.encodeABI(
            fn_name='approve',
            args=[Web3.to_checksum_address(deployments['malicious']), limited_amount]
        )
    }

    passed3, reason3 = policy_engine.validate_transaction(tx3, user_address)
    print(f"\nPolicyLayer result: {'ALLOWED' if passed3 else 'BLOCKED'}")
    print(f"Reason: {reason3}")

    result3 = print_result(passed3, expected_block=False)
    results.append(("Test 3: Limited to Malicious", result3))

    # TEST 4: Zero Approval (Revoke)
    print_test_header(4, "Zero Approval (Revoke Approval)")
    print(f"Description: User revokes approval by setting to 0")
    print(f"Expected: {Colors.GREEN}✅ ALLOW{Colors.END} (safe operation)")

    tx4 = {
        'from': user_address,
        'to': Web3.to_checksum_address(deployments['token']),
        'value': 0,
        'gas': 100000,
        'data': token_contract.encodeABI(
            fn_name='approve',
            args=[Web3.to_checksum_address(deployments['malicious']), 0]
        )
    }

    passed4, reason4 = policy_engine.validate_transaction(tx4, user_address)
    print(f"\nPolicyLayer result: {'ALLOWED' if passed4 else 'BLOCKED'}")
    print(f"Reason: {reason4}")

    result4 = print_result(passed4, expected_block=False)
    results.append(("Test 4: Zero Approval (Revoke)", result4))

    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{Colors.BOLD}{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}{Colors.END}\n")

    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)

    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} - {test_name}")

    print(f"\n{Colors.BOLD}Total: {total_passed}/{total_tests} tests passed{Colors.END}")

    if total_passed == total_tests:
        print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}⚠️  {total_tests - total_passed} test(s) failed{Colors.END}\n")

    # ============================================================
    # ADDITIONAL INFO
    # ============================================================
    print(f"{Colors.BLUE}💡 Additional Testing Notes:{Colors.END}")
    print("\n1. To test with LLM validation, enable in policy_v2.yaml:")
    print("   llm_validation:")
    print("     enabled: true")
    print("     provider: openai")
    print("     model: gpt-4o-mini")
    print("\n2. To test with Tenderly simulation, add to .env:")
    print("   TENDERLY_ACCESS_KEY=your_key")
    print("   TENDERLY_ACCOUNT_SLUG=your_account")
    print("   TENDERLY_PROJECT_SLUG=your_project")
    print("\n3. To whitelist the legitimate contract, update policy_v2.yaml:")
    print(f"   allowed_addresses:")
    print(f"     - {deployments['whitelisted']}")
    print()


if __name__ == "__main__":
    main()
