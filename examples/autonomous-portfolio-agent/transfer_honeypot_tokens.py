#!/usr/bin/env python3
"""
Transfer all honeypot tokens and then remove from whitelist

This script:
1. Whitelists address 0xc4828792ab7b2a773b35fcb62D1D934282450fa4
2. Transfers all tokens to 0x78e85f2a6e2c95096db790d9b78ad168daac8e26
3. Removes from whitelist (honeypot restrictions apply after)

Honeypot Token (LEGIT): 0xFe836592564C37D6cE99657c379a387CC5CE0868
"""

import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Contract addresses
HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
SENDER_ADDRESS = "0xc4828792ab7b2a773b35fcb62D1D934282450fa4"  # Address that will send tokens
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


def main():
    print("\n" + "="*70)
    print("🔄 TRANSFERRING HONEYPOT TOKENS")
    print("="*70)

    # Setup Web3 - using the owner's private key from setup_honeypot_pool.py
    private_key = "0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b"

    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = web3.eth.account.from_key(private_key)
    wallet_address = account.address

    print(f"\n👛 Owner Wallet: {wallet_address}")
    print(f"💰 Balance: {web3.from_wei(web3.eth.get_balance(wallet_address), 'ether')} ETH\n")

    # Get honeypot contract
    honeypot = web3.eth.contract(
        address=Web3.to_checksum_address(HONEYPOT_TOKEN),
        abi=HONEYPOT_ABI
    )

    # Verify we're the owner
    owner = honeypot.functions.owner().call()
    if owner.lower() != wallet_address.lower():
        print(f"❌ Error: You are not the owner of the contract!")
        print(f"   Contract owner: {owner}")
        print(f"   Your address: {wallet_address}")
        return

    sender = Web3.to_checksum_address(SENDER_ADDRESS)
    recipient = Web3.to_checksum_address(RECIPIENT_ADDRESS)

    # Check current balance of sender
    balance = honeypot.functions.balanceOf(sender).call()
    print(f"📊 Current balance of {sender}:")
    print(f"   {web3.from_wei(balance, 'ether')} LEGIT tokens\n")

    if balance == 0:
        print("❌ No tokens to transfer!")
        return

    # STEP 1: Check if sender is whitelisted
    print("🔍 STEP 1: Checking whitelist status...")
    is_whitelisted = honeypot.functions.isWhitelisted(sender).call()

    if not is_whitelisted:
        print(f"📝 Whitelisting {sender}...")
        tx = honeypot.functions.setWhitelist(sender, True).build_transaction({
            'from': wallet_address,
            'gas': 100000,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for whitelist transaction...")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Address whitelisted!")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")
    else:
        print(f"✅ Address already whitelisted\n")

    # STEP 2: Transfer tokens (you'll need the sender's private key for this)
    print("⚠️  STEP 2: Transfer tokens")
    print(f"   To transfer tokens, you need to call the transfer function from {sender}")
    print(f"   Since I don't have the private key for {sender}, you'll need to:")
    print(f"\n   Option A: If you have the private key for {sender}, run:")
    print(f"   >>> python transfer_from_sender.py\n")
    print(f"   Option B: Manually call from that address:")
    print(f"   >>> transfer({recipient}, {balance})\n")

    # Create a helper script for the sender
    helper_script = f"""#!/usr/bin/env python3
# Helper script to transfer tokens FROM {sender}
# You need the private key for {sender}

from web3 import Web3

RPC_URL = "{RPC_URL}"
HONEYPOT_TOKEN = "{HONEYPOT_TOKEN}"
RECIPIENT = "{recipient}"

HONEYPOT_ABI = {HONEYPOT_ABI}

# TODO: Replace with your private key for {sender}
SENDER_PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"

web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(SENDER_PRIVATE_KEY)

honeypot = web3.eth.contract(address=Web3.to_checksum_address(HONEYPOT_TOKEN), abi=HONEYPOT_ABI)

# Get balance
balance = honeypot.functions.balanceOf(account.address).call()
print(f"Transferring {{web3.from_wei(balance, 'ether')}} LEGIT tokens to {{RECIPIENT}}")

# Transfer all tokens
tx = honeypot.functions.transfer(RECIPIENT, balance).build_transaction({{
    'from': account.address,
    'gas': 200000,
    'nonce': web3.eth.get_transaction_count(account.address),
}})

signed_tx = account.sign_transaction(tx)
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Transaction sent: {{tx_hash.hex()}}")
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ Transfer complete!")
print(f"🔗 https://sepolia.basescan.org/tx/{{tx_hash.hex()}}")
"""

    with open("transfer_from_sender.py", "w") as f:
        f.write(helper_script)

    print(f"✅ Created helper script: transfer_from_sender.py\n")

    # STEP 3: Ask if they want to remove from whitelist now or later
    print("📝 STEP 3: Remove from whitelist")
    print(f"   After transferring tokens, you can remove {sender} from whitelist")
    print(f"   This will prevent future transfers (honeypot restrictions apply)\n")

    response = input("   Do you want to remove from whitelist now? (y/n): ").lower()

    if response == 'y':
        print(f"📝 Removing {sender} from whitelist...")
        tx = honeypot.functions.setWhitelist(sender, False).build_transaction({
            'from': wallet_address,
            'gas': 100000,
            'nonce': web3.eth.get_transaction_count(wallet_address),
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"⏳ Waiting for transaction...")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Address removed from whitelist!")
        print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

        # Optional: Blacklist
        response2 = input("   Do you want to blacklist it too? (y/n): ").lower()
        if response2 == 'y':
            print(f"📝 Blacklisting {sender}...")
            tx = honeypot.functions.setBlacklist(sender, True).build_transaction({
                'from': wallet_address,
                'gas': 100000,
                'nonce': web3.eth.get_transaction_count(wallet_address),
            })

            signed_tx = account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"⏳ Waiting for transaction...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            print(f"✅ Address blacklisted!")
            print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}\n")

    print("="*70)
    print("✅ SCRIPT COMPLETE!")
    print("="*70)
    print(f"\n📍 Summary:")
    print(f"   Honeypot Token: {HONEYPOT_TOKEN}")
    print(f"   Sender: {sender}")
    print(f"   Recipient: {recipient}")
    print(f"   Status: Whitelisted ✅")
    print(f"\n🎯 Next: Run transfer_from_sender.py with the sender's private key\n")


if __name__ == "__main__":
    main()
