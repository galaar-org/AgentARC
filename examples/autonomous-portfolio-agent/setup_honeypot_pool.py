#!/usr/bin/env python3
"""
Create Uniswap V3 pool for honeypot token (LEGIT)

This script:
1. Creates a WETH/LEGIT pool on Uniswap V3
2. Initializes the pool price
3. Adds initial liquidity
4. Makes the honeypot token tradeable on Uniswap

Deployed Contracts (Base Sepolia):
- HoneypotToken (LEGIT): 0xFe836592564C37D6cE99657c379a387CC5CE0868
- WETH: 0x4200000000000000000000000000000000000006
- Uniswap V3 Factory: 0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24
- Uniswap V3 NonfungiblePositionManager: 0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2
"""

import os
import math
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Contract addresses on Base Sepolia
HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"
UNISWAP_V3_FACTORY = "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"
UNISWAP_V3_POSITION_MANAGER = "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2"

# RPC URL
RPC_URL = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

# ABIs
ERC20_ABI = [
    {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
]

FACTORY_ABI = [
    {"inputs": [{"internalType": "address", "name": "", "type": "address"}, {"internalType": "address", "name": "", "type": "address"}, {"internalType": "uint24", "name": "", "type": "uint24"}], "name": "getPool", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "createPool", "outputs": [{"internalType": "address", "name": "pool", "type": "address"}], "stateMutability": "nonpayable", "type": "function"}
]

POOL_ABI = [
    {"inputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}], "name": "initialize", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

POSITION_MANAGER_ABI = [
    {"inputs": [{"components": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "internalType": "struct INonfungiblePositionManager.MintParams", "name": "params", "type": "tuple"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"}
]


def main():
    print("\n" + "="*70)
    print("🏗️  CREATING UNISWAP V3 POOL FOR HONEYPOT TOKEN")
    print("="*70)

    # Setup Web3
    private_key = "0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b"

    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = web3.eth.account.from_key(private_key)
    wallet_address = account.address

    print(f"\n👛 Wallet: {wallet_address}")
    print(f"💰 Balance: {web3.from_wei(web3.eth.get_balance(wallet_address), 'ether')} ETH\n")

    # Get contracts
    factory = web3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V3_FACTORY), abi=FACTORY_ABI)
    honeypot = web3.eth.contract(address=Web3.to_checksum_address(HONEYPOT_TOKEN), abi=ERC20_ABI)

    # Check token balance
    token_balance = honeypot.functions.balanceOf(wallet_address).call()
    print(f"🪙 LEGIT balance: {web3.from_wei(token_balance, 'ether')} tokens\n")

    # STEP 1: Check if pool exists
    print("🔍 STEP 1: Checking if pool exists...")
    fee_tier = 3000  # 0.3%
    pool_address = factory.functions.getPool(
        Web3.to_checksum_address(WETH_ADDRESS),
        Web3.to_checksum_address(HONEYPOT_TOKEN),
        fee_tier
    ).call()

    pool_exists = pool_address != "0x0000000000000000000000000000000000000000"

    if pool_exists:
        print(f"✅ Pool already exists: {pool_address}")
        print(f"🔗 https://sepolia.basescan.org/address/{pool_address}\n")
    else:
        # STEP 2: Create pool
        print("\n📝 STEP 2: Creating new pool...")
        tx = factory.functions.createPool(
            Web3.to_checksum_address(WETH_ADDRESS),
            Web3.to_checksum_address(HONEYPOT_TOKEN),
            fee_tier
        ).build_transaction({
            'from': wallet_address,
            'gas': 5000000,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for pool creation...")
        web3.eth.wait_for_transaction_receipt(tx_hash)

        pool_address = factory.functions.getPool(
            Web3.to_checksum_address(WETH_ADDRESS),
            Web3.to_checksum_address(HONEYPOT_TOKEN),
            fee_tier
        ).call()

        print(f"✅ Pool created: {pool_address}")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

    # STEP 3: Initialize pool with price
    print("📝 STEP 3: Initializing pool price...")
    # Price: 1 WETH = 10,000 LEGIT
    # sqrtPriceX96 = sqrt(10000) * 2^96
    price = 10000  # 1 WETH = 10,000 LEGIT
    sqrt_price_x96 = int(math.sqrt(price) * (2 ** 96))

    pool = web3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=POOL_ABI)

    try:
        tx = pool.functions.initialize(sqrt_price_x96).build_transaction({
            'from': wallet_address,
            'gas': 1000000,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for initialization...")
        web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Pool initialized (1 WETH = 10,000 LEGIT)")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")
    except Exception as e:
        if "already initialized" in str(e).lower():
            print(f"✅ Pool already initialized\n")
        else:
            print(f"❌ Initialization failed: {e}\n")
            return

    # STEP 4: Add liquidity
    print("📝 STEP 4: Adding liquidity (0.1 WETH + 1000 LEGIT)...")

    position_manager = web3.eth.contract(
        address=Web3.to_checksum_address(UNISWAP_V3_POSITION_MANAGER),
        abi=POSITION_MANAGER_ABI
    )

    weth_amount = web3.to_wei(0.1, 'ether')  # 0.1 WETH
    legit_amount = web3.to_wei(1000, 'ether')  # 1000 LEGIT

    # Approve LEGIT
    print("📝 Approving LEGIT tokens...")
    tx = honeypot.functions.approve(UNISWAP_V3_POSITION_MANAGER, legit_amount).build_transaction({
        'from': wallet_address,
        'gas': 100000,
        'nonce': web3.eth.get_transaction_count(wallet_address),
    })
    signed_tx = account.sign_transaction(tx)
    web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(signed_tx.hash)
    print("✅ LEGIT approved")

    # Determine token order (token0 < token1)
    token0 = min(Web3.to_checksum_address(WETH_ADDRESS), Web3.to_checksum_address(HONEYPOT_TOKEN))
    token1 = max(Web3.to_checksum_address(WETH_ADDRESS), Web3.to_checksum_address(HONEYPOT_TOKEN))

    amount0 = weth_amount if Web3.to_checksum_address(WETH_ADDRESS) == token0 else legit_amount
    amount1 = legit_amount if Web3.to_checksum_address(WETH_ADDRESS) == token0 else weth_amount

    mint_params = {
        'token0': token0,
        'token1': token1,
        'fee': 3000,
        'tickLower': -887220,  # Full range
        'tickUpper': 887220,
        'amount0Desired': amount0,
        'amount1Desired': amount1,
        'amount0Min': 0,
        'amount1Min': 0,
        'recipient': wallet_address,
        'deadline': web3.eth.get_block('latest')['timestamp'] + 1200
    }

    print("📝 Minting liquidity position...")
    tx = position_manager.functions.mint(mint_params).build_transaction({
        'from': wallet_address,
        'value': weth_amount,
        'gas': 5000000,
        'nonce': web3.eth.get_transaction_count(wallet_address),
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"⏳ Waiting for liquidity to be added...")
    web3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"✅ Liquidity added successfully!")
    print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

    print("="*70)
    print("✅ POOL SETUP COMPLETE!")
    print("="*70)
    print(f"\n📍 Pool Address: {pool_address}")
    print(f"💧 Liquidity: 0.1 WETH + 1000 LEGIT")
    print(f"💱 Price: 1 WETH = 10,000 LEGIT")
    print(f"\n🎯 Next: Run the autonomous agent to see honeypot detection!")
    print(f"   Command: python autonomous_agent.py\n")


if __name__ == "__main__":
    main()
