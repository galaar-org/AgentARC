#!/usr/bin/env python3
"""
Block address from selling honeypot tokens

This script:
1. Removes address 0xc4828792ab7b2a773b35fcb62D1D934282450fa4 from whitelist
2. Optionally blacklists the address (honeypot restrictions apply)

Honeypot Token (LEGIT): 0xFe836592564C37D6cE99657c379a387CC5CE0868
"""

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Contract addresses
HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
ADDRESS_TO_BLOCK = "0xc4828792ab7b2a773b35fcb62D1D934282450fa4"  # Address to block from selling

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
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isBlacklisted",
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
    print("🚫 BLOCKING ADDRESS FROM SELLING HONEYPOT TOKENS")
    print("="*70)

    # Setup Web3 - using the owner's private key
    owner_private_key = "0xfa8f5eed5e9bf1804f7014e299788ba2f4a2fd82b203a317666994ef1cfcce2b"

    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = web3.eth.account.from_key(owner_private_key)
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

    address_to_block = Web3.to_checksum_address(ADDRESS_TO_BLOCK)

    # Check current status
    is_whitelisted = honeypot.functions.isWhitelisted(address_to_block).call()
    is_blacklisted = honeypot.functions.isBlacklisted(address_to_block).call()
    balance = honeypot.functions.balanceOf(address_to_block).call()

    print(f"📊 Current Status of {address_to_block}:")
    print(f"   Balance: {web3.from_wei(balance, 'ether')} LEGIT")
    print(f"   Whitelisted: {'✅ Yes' if is_whitelisted else '❌ No'}")
    print(f"   Blacklisted: {'✅ Yes' if is_blacklisted else '❌ No'}\n")

    # STEP 1: Remove from whitelist
    print("="*70)
    print("STEP 1: REMOVE FROM WHITELIST")
    print("="*70)

    if is_whitelisted:
        print(f"📝 Removing {address_to_block} from whitelist...")
        tx = honeypot.functions.setWhitelist(address_to_block, False).build_transaction({
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
    else:
        print(f"✅ Address already removed from whitelist\n")

    # STEP 2: Blacklist (optional but recommended)
    print("="*70)
    print("STEP 2: BLACKLIST ADDRESS (OPTIONAL)")
    print("="*70)
    print("Blacklisting will completely prevent this address from transferring tokens.")
    print("This is more restrictive than just removing from whitelist.\n")

    if not is_blacklisted:
        response = input("Do you want to blacklist this address? (y/n): ").lower()

        if response == 'y':
            print(f"📝 Blacklisting {address_to_block}...")
            tx = honeypot.functions.setBlacklist(address_to_block, True).build_transaction({
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

            is_blacklisted = True
        else:
            print("⏭️  Skipping blacklist\n")
    else:
        print(f"✅ Address already blacklisted\n")

    # Final status
    print("="*70)
    print("✅ BLOCKING COMPLETE!")
    print("="*70)
    print(f"\n📍 Final Status:")
    print(f"   Address: {address_to_block}")
    print(f"   Whitelisted: ❌ No (Cannot sell)")
    print(f"   Blacklisted: {'✅ Yes (Extra restriction)' if is_blacklisted else '❌ No'}")
    print(f"\n🔒 This address can NO LONGER transfer or sell LEGIT tokens!")
    print(f"   Any transfer attempts will fail due to honeypot restrictions.\n")


if __name__ == "__main__":
    main()