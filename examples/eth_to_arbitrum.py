from ccip_sdk import CCIPClient
from dotenv import load_dotenv
import os

load_dotenv()

client = CCIPClient(private_key=os.environ.get("PRIVATE_KEY"))

contract = client.deploy_sender_contract("ethereum_sepolia")
print(f"Deployed contract address: {contract}\n")
txn_hash = client.send_tokens_to_sender_contract("ethereum_sepolia", "CCIP-BnM", 0.1)
print(f"Token sent via this transaction hash : {txn_hash}\n")
txn_hash = client.send_eth_to_contract("ethereum_sepolia", 0.05)
print(f"ETH sent via this transaction hash : {txn_hash}\n")
txn_hash = client.allow_destination_chain(current_chain="ethereum_sepolia", destination_chain="arbitrum_sepolia")
print(f"Allowed destination chain arbitrum_sepolia done with txnHash : {txn_hash}\n")

contract = client.deploy_receiver_contract("arbitrum_sepolia")
print(f"Deployed contract address: {contract}\n")
txn_hash = client.allow_source_chain(current_chain="arbitrum_sepolia", sender_chain="ethereum_sepolia")
print(f"Allowed sender chain ethereum_sepolia done with txnHash : {txn_hash}\n")
txn_hash = client.allow_sender_on_receiver(sender_chain="ethereum_sepolia", receiver_chain="arbitrum_sepolia")
print(f"Allowed the sender contract to send messages on reciever chain with txnHash : {txn_hash}\n")

txn_url = client.transfer(sender_chain="ethereum_sepolia", receiver_chain="arbitrum_sepolia", text="Hi dj boi", amount=0.069)
print(f"You can watch the CCIP Transfer here : {txn_url}\n")

