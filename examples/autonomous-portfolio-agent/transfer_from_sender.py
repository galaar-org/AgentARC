#!/usr/bin/env python3
# Helper script to transfer tokens FROM 0xc4828792ab7b2a773b35fcb62D1D934282450fa4
# You need the private key for 0xc4828792ab7b2a773b35fcb62D1D934282450fa4

from web3 import Web3

RPC_URL = "https://base-sepolia.g.alchemy.com/v2/NzDe6iLtMKuH5Fw1A3l_oiIuepsrwoUj"
HONEYPOT_TOKEN = "0xFe836592564C37D6cE99657c379a387CC5CE0868"
RECIPIENT = "0x78e85F2A6e2C95096Db790D9B78AD168daac8e26"

HONEYPOT_ABI = [{'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}, {'internalType': 'bool', 'name': 'status', 'type': 'bool'}], 'name': 'setWhitelist', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}, {'internalType': 'bool', 'name': 'status', 'type': 'bool'}], 'name': 'setBlacklist', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'account', 'type': 'address'}], 'name': 'isWhitelisted', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'owner', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}]

# TODO: Replace with your private key for 0xc4828792ab7b2a773b35fcb62D1D934282450fa4
SENDER_PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"

web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(SENDER_PRIVATE_KEY)

honeypot = web3.eth.contract(address=Web3.to_checksum_address(HONEYPOT_TOKEN), abi=HONEYPOT_ABI)

# Get balance
balance = honeypot.functions.balanceOf(account.address).call()
print(f"Transferring {web3.from_wei(balance, 'ether')} LEGIT tokens to {RECIPIENT}")

# Transfer all tokens
tx = honeypot.functions.transfer(RECIPIENT, balance).build_transaction({
    'from': account.address,
    'gas': 200000,
    'nonce': web3.eth.get_transaction_count(account.address),
})

signed_tx = account.sign_transaction(tx)
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Transaction sent: {tx_hash.hex()}")
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ Transfer complete!")
print(f"🔗 https://sepolia.basescan.org/tx/{tx_hash.hex()}")
