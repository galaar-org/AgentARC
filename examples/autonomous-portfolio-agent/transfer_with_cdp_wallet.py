#!/usr/bin/env python3
"""
Transfer all honeypot tokens using CDP Wallet

This script:
1. Whitelists address 0xc4828792ab7b2a773b35fcb62D1D934282450fa4 (using owner wallet)
2. Transfers all tokens to 0x78e85f2a6e2c95096db790d9b78ad168daac8e26 (using CDP wallet)
3. Removes from whitelist (honeypot restrictions apply after)

Honeypot Token (LEGIT): 0xFe836592564C37D6cE99657c379a387CC5CE0868
"""

import asyncio
import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))

from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig

load_dotenv()

# Contract addresses
HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
CDP_WALLET_ADDRESS = "0xc4828792ab7b2a773b35fcb62D1D934282450fa4"  # Address that will send tokens
RECIPIENT_ADDRESS = "0x78e85f2a6e2c95096db790d9b78ad168daac8e26"  # Address to receive tokens

# RPC URL
RPC_URL = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"

# Honeypot Token ABI (only functions we need)
HONEYPOT_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "bool", "name": "status", "type": "bool"}
        ],
        "name": "setWhitelist",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "bool", "name": "status", "type": "bool"}
        ],
        "name": "setBlacklist",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isWhitelisted",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]


async def main():
    print("\n" + "="*70)
    print("🔄 TRANSFERRING HONEYPOT TOKENS WITH CDP WALLET")
    print("="*70)

    # Verify required environment variables
    required_env_vars = ["CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "CDP_WALLET_SECRET"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        sys.exit(1)

    # Initialize web3 for owner operations
    owner_private_key = "0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b"
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    owner_account = web3.eth.account.from_key(owner_private_key)
    owner_address = owner_account.address

    print(f"\n👛 Owner Wallet: {owner_address}")
    print(f"💰 Owner Balance: {web3.from_wei(web3.eth.get_balance(owner_address), 'ether')} ETH")

    # Initialize CDP Wallet
    print(f"\n🔐 Initializing CDP Wallet...")
    cdp_wallet = CdpEvmWalletProvider(CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id="base-sepolia",
        address=CDP_WALLET_ADDRESS,
    ))

    cdp_wallet_address = cdp_wallet.get_address()
    print(f"✅ CDP Wallet Address: {cdp_wallet_address}")

    # Get CDP wallet balance
    cdp_balance = web3.eth.get_balance(cdp_wallet_address)
    print(f"💰 CDP Wallet Balance: {web3.from_wei(cdp_balance, 'ether')} ETH\n")

    # Get honeypot contract
    honeypot = web3.eth.contract(
        address=Web3.to_checksum_address(HONEYPOT_TOKEN),
        abi=HONEYPOT_ABI
    )

    # Verify owner
    contract_owner = honeypot.functions.owner().call()
    if contract_owner.lower() != owner_address.lower():
        print(f"❌ Error: You are not the owner of the contract!")
        print(f"   Contract owner: {contract_owner}")
        print(f"   Your address: {owner_address}")
        return

    # Check token balance
    sender = Web3.to_checksum_address(CDP_WALLET_ADDRESS)
    recipient = Web3.to_checksum_address(RECIPIENT_ADDRESS)
    balance = honeypot.functions.balanceOf(sender).call()

    print(f"📊 Token Balance:")
    print(f"   Sender ({sender}): {web3.from_wei(balance, 'ether')} LEGIT")

    if balance == 0:
        print("\n❌ No tokens to transfer!")
        return

    # STEP 1: Whitelist the CDP wallet address
    print("\n" + "="*70)
    print("STEP 1: WHITELISTING CDP WALLET")
    print("="*70)

    is_whitelisted = honeypot.functions.isWhitelisted(sender).call()

    if not is_whitelisted:
        print(f"📝 Whitelisting {sender}...")
        tx = honeypot.functions.setWhitelist(sender, True).build_transaction({
            'from': owner_address,
            'gas': 100000,
            'nonce': web3.eth.get_transaction_count(owner_address),
        })

        signed_tx = owner_account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for whitelist transaction...")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Address whitelisted!")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")
    else:
        print(f"✅ Address already whitelisted\n")

    # STEP 2: Transfer all tokens using CDP Wallet
    print("="*70)
    print("STEP 2: TRANSFERRING TOKENS WITH CDP WALLET")
    print("="*70)
    print(f"📤 Transferring {web3.from_wei(balance, 'ether')} LEGIT tokens")
    print(f"   From: {sender}")
    print(f"   To: {recipient}\n")

    # Build the transfer transaction data
    # Use web3.py to encode the function call
    tx_data = honeypot.functions.transfer(recipient, balance).build_transaction({
        'from': sender,
        'nonce': 0,  # Dummy nonce, will be set by CDP wallet
        'gas': 200000,
    })

    # Use CDP wallet to send transaction
    print("🔐 Signing with CDP Wallet...")
    tx_hash = cdp_wallet.send_transaction({
        'to': HONEYPOT_TOKEN,
        'data': tx_data['data'],
        'value': 0,
        'chainId': 84532,  # Base Sepolia
    })

    print(f"⏳ Waiting for transfer transaction...")
    print(f"   Transaction hash: {tx_hash}")

    # Wait for confirmation
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] == 1:
        print(f"✅ Transfer successful!")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash}\n")

        # Verify balance after transfer
        new_balance = honeypot.functions.balanceOf(sender).call()
        recipient_balance = honeypot.functions.balanceOf(recipient).call()
        print(f"📊 New Balances:")
        print(f"   Sender: {web3.from_wei(new_balance, 'ether')} LEGIT")
        print(f"   Recipient: {web3.from_wei(recipient_balance, 'ether')} LEGIT\n")
    else:
        print(f"❌ Transfer failed!")
        return

    # STEP 3: Remove from whitelist
    print("="*70)
    print("STEP 3: REMOVE FROM WHITELIST")
    print("="*70)

    response = input("Do you want to remove from whitelist now? (y/n): ").lower()

    if response == 'y':
        print(f"📝 Removing {sender} from whitelist...")
        tx = honeypot.functions.setWhitelist(sender, False).build_transaction({
            'from': owner_address,
            'gas': 100000,
            'nonce': web3.eth.get_transaction_count(owner_address),
        })

        signed_tx = owner_account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for transaction...")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Address removed from whitelist!")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

        # Optional: Blacklist
        response2 = input("Do you want to blacklist it too? (y/n): ").lower()
        if response2 == 'y':
            print(f"📝 Blacklisting {sender}...")
            tx = honeypot.functions.setBlacklist(sender, True).build_transaction({
                'from': owner_address,
                'gas': 100000,
                'nonce': web3.eth.get_transaction_count(owner_address),
            })

            signed_tx = owner_account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"⏳ Waiting for transaction...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            print(f"✅ Address blacklisted!")
            print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

    print("="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"\n📍 Summary:")
    print(f"   Honeypot Token: {HONEYPOT_TOKEN}")
    print(f"   Tokens Transferred: {web3.from_wei(balance, 'ether')} LEGIT")
    print(f"   From: {sender}")
    print(f"   To: {recipient}")
    print(f"   Status: {'Removed from whitelist' if response == 'y' else 'Still whitelisted'} ✅\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
