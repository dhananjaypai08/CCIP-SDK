import json
from eth_account import Account
from web3 import Web3
import importlib.resources

multiplier = 2

ERC20_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }
]

def get_account_from_private_key(private_key: str):
    """
    Returns an account object from a private key.

    :param private_key: The private key to create the account from.
    :return: An account object.
    """
    return Account.from_key(private_key)

def get_contract_interface(file_path: str) -> dict:
    """
    Reads a contract ABI from a JSON file.

    :param file_path: The path to the JSON file containing the ABI.
    :return: The ABI as a dictionary.
    """
    
    with open(file_path, 'r') as f:
        return json.load(f)
    
def get_ccip_directory_data(file_path: str) -> dict:
    """
    Reads CCIP directory data from a JSON file.

    :param file_path: The path to the JSON file containing the CCIP directory data.
    :return: The CCIP directory data as a dictionary.
    """
    with open(file_path, 'r') as f:
        return json.load(f)
    
def deploy_contract(rpc: str, router: str, link: str, filepath: str, account: Account, multiplier=multiplier):
    """
    Deploy contract on the given chain

    :param rpc: The rpc url of the chain 
    :param router: The address of the CCIP router
    :param link: The address of the LINK token
    :param filepath: The path to the interface containing abi, bytecode
    :return : The contract address in string format
    """
    w3 = Web3(Web3.HTTPProvider(rpc))
    contract_interface = get_contract_interface(filepath)
    abi = contract_interface["abi"]
    bytecode = contract_interface["bytecode"]

    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    balance = w3.eth.get_balance(account.address)
    print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")

    gas_estimate = contract.constructor(router, link).estimate_gas({"from": account.address})

    transaction = {
        'nonce': nonce,
        'gas': int(gas_estimate * multiplier),
        'gasPrice': w3.eth.gas_price,
        'from': account.address,
    }
    try:
        # Deploy contract
        contract_tx = contract.constructor(router, link).build_transaction(transaction)
        
        signed_tx = w3.eth.account.sign_transaction(contract_tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt['contractAddress']
        
        print(f"Contract deployed successfully!")
        print(f"Contract address: {contract_address}")
        print(f"Transaction hash: {tx_hash.hex()}")
        
        return contract_address
        
    except Exception as e:
        print(f"Error deploying contract: {str(e)}")
        return None

def send_erc20_to_contract(rpc: str, token: str, account: Account, amount: float, contract: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    amount = Web3.to_wei(amount, "ether")
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=ERC20_ABI)
    gas_estimate = token_contract.functions.transfer(
        Web3.to_checksum_address(contract),
        amount
    ).estimate_gas({"from": account.address})
    
    try:

        tx = token_contract.functions.transfer(
            Web3.to_checksum_address(contract),
            amount
        ).build_transaction({
            "chainId": w3.eth.chain_id,
            "gas": int(gas_estimate * multiplier),
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error sending token to contract: {str(e)}")
        return None
    
def send_native_eth(rpc: str, account: Account, amount: float, contract: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    amount = Web3.to_wei(amount, "ether")
    tx = {
        'to': Web3.to_checksum_address(contract),
        'value': amount,
        'gas': 25000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': w3.eth.chain_id,
    }
    try:
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction hash: 0x{tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error transferring native tokens: {str(e)}")
        return False

def allowlistDestinationChain(rpc: str, chainSelector: int, contract: str, account: Account, filepath: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    contract_interface = get_contract_interface(filepath)
    abi = contract_interface["abi"]
    contract = w3.eth.contract(address=contract, abi=abi)
    chainSelector = int(chainSelector)
    allowed = True
    gas_estimate = contract.functions.allowlistDestinationChain(chainSelector, allowed).estimate_gas({"from": account.address})

    transaction = {
        'nonce': nonce,
        'gas': int(gas_estimate * multiplier),
        'gasPrice': w3.eth.gas_price,
        'from': account.address,
    }

    try:
        tx = contract.functions.allowlistDestinationChain(chainSelector, allowed).build_transaction(transaction)
        signed_tx = w3.eth.account.sign_transaction(tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)    
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction hash: 0x{tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error allowing destination chain: {str(e)}")
        return False

def allowlistSourceChain(rpc: str, chainSelector: int, contract: str, account: Account, filepath: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    contract_interface = get_contract_interface(filepath)
    abi = contract_interface["abi"]
    contract = w3.eth.contract(address=contract, abi=abi)
    allowed = True
    chainSelector = int(chainSelector)
    gas_estimate = contract.functions.allowlistSourceChain(chainSelector, allowed).estimate_gas({"from": account.address})

    transaction = {
        'nonce': nonce,
        'gas': int(gas_estimate * multiplier),
        'gasPrice': w3.eth.gas_price,
        'from': account.address,
    }

    try:
        tx = contract.functions.allowlistSourceChain(chainSelector, allowed).build_transaction(transaction)
        signed_tx = w3.eth.account.sign_transaction(tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)    
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction hash: 0x{tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error allowing destination chain: {str(e)}")
        return False

def allowlistSender(rpc: str, sender_contract: str, current_contract: str, account: Account, filepath: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    contract_interface = get_contract_interface(filepath)
    abi = contract_interface["abi"]
    contract = w3.eth.contract(address=current_contract, abi=abi)

    allowed = True
    gas_estimate = contract.functions.allowlistSender(sender_contract, allowed).estimate_gas({"from": account.address})

    transaction = {
        'nonce': nonce,
        'gas': int(gas_estimate * multiplier),
        'gasPrice': w3.eth.gas_price,
        'from': account.address,
    }

    try:
        tx = contract.functions.allowlistSender(sender_contract, allowed).build_transaction(transaction)
        signed_tx = w3.eth.account.sign_transaction(tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)    
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction hash: 0x{tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error allowing destination chain: {str(e)}")
        return False
    
def transfer(rpc: str, current_contract: str, destination_chain_selector: int, receiver_contract: str, text: str, token: str, amount: float, account: Account, filepath: str, multiplier=multiplier):
    w3 = Web3(Web3.HTTPProvider(rpc))
    nonce = max(
        w3.eth.get_transaction_count(account.address, 'pending'),
        w3.eth.get_transaction_count(account.address, 'latest')
    )
    contract_interface = get_contract_interface(filepath)
    abi = contract_interface["abi"]
    contract = w3.eth.contract(address=current_contract, abi=abi)
    chainSelector = int(destination_chain_selector)
    amount = Web3.to_wei(amount, "ether")
    gas_estimate = contract.functions.sendMessagePayNative(chainSelector, receiver_contract, text, token, amount).estimate_gas({"from": account.address})

    transaction = {
        'nonce': nonce,
        'gas': int(gas_estimate * multiplier),
        'gasPrice': w3.eth.gas_price,
        'from': account.address,
    }

    try:
        tx = contract.functions.sendMessagePayNative(chainSelector, receiver_contract, text, token, amount).build_transaction(transaction)
        signed_tx = w3.eth.account.sign_transaction(tx, account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)    
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction hash: 0x{tx_hash.hex()}")
        return f"0x{tx_hash.hex()}"
    except Exception as e:
        print(f"Error allowing destination chain: {str(e)}")
        return False