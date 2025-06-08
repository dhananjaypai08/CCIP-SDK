from typing import Optional, Literal
from .utils import (
    get_account_from_private_key, 
    get_ccip_directory_data, 
    deploy_contract, 
    send_erc20_to_contract,
    send_native_eth,
    allowlistDestinationChain,
    allowlistSourceChain,
    allowlistSender,
    transfer,
    getLastReceivedMessage,
    withdraw_token,
    withdraw_eth
)
from pathlib import Path
import time

class CCIPClient:
    """
    CCIPClient handles CCIP state logic for the SDK.
    """
    def __init__(self, **kwargs: str) -> None:
        """
        Initializes the CCIPClient with a private key.

        :param private_key: The private key for the client.
        """
        for key, value in kwargs.items():
            if key == "private_key":
                private_key = value
            else:
                raise ValueError(f"Unknown argument {key}.")
        self.private_key = private_key
        self.account = get_account_from_private_key(private_key)
        self.sender_contracts = {}
        self.receiver_contracts = {}
        SCRIPT_DIR = Path(__file__).parent.absolute()
        DATA_FILE = SCRIPT_DIR / "ccip_directory" / "data.json"
        CONTRACT_FILE = SCRIPT_DIR / "contracts" / "artifacts" / "contracts" / "CCIPContract.sol" / "CCIPContract.json"
        self.contract_compiled_file = str(CONTRACT_FILE)
        self.ccip_directory_path = str(DATA_FILE)
        self.chains_data = get_ccip_directory_data(self.ccip_directory_path)
        self.chains = list(self.chains_data.keys())
        self.tokens = list(self.chains_data["ethereum_sepolia"]["tokens"].keys())


    def deploy_sender_contract(self, chain: str) -> str:
        """
        deploy the sender contract and store address

        :param chain: The name of the chain
        """
        self.validate_chain(chain)
        
        rpc = self.chains_data[chain]["rpc"]
        router = self.chains_data[chain]["router"]
        link = self.chains_data[chain]["tokens"]["LINK"]
        print("Deploying contract on chain:", chain)
        contract_address = deploy_contract(
            rpc=rpc,
            router=router,
            link=link,
            filepath=self.contract_compiled_file,
            account=self.account
        )
        
        self.sender_contracts[chain] = contract_address
        return contract_address
    
    def deploy_receiver_contract(self, chain: str) -> str:
        """
        deploy the receiver contract and store address

        :param chain: The name of the chain
        """
        self.validate_chain(chain)
        
        rpc = self.chains_data[chain]["rpc"]
        router = self.chains_data[chain]["router"]
        link = self.chains_data[chain]["tokens"]["LINK"]
        print("Deploying contract on chain:", chain)
        contract_address = deploy_contract(
            rpc=rpc,
            router=router,
            link=link,
            filepath=self.contract_compiled_file,
            account=self.account
        )
        
        self.receiver_contracts[chain] = contract_address
        return contract_address

    def send_tokens_to_sender_contract(self, chain: str, token: str, amount: float) -> str:
        """
        send the given token to the contract
        :param chain: the network on which the contract is 
        :param token: the token which is to be sent to the contract
        :param amount: the amount to be sent in normal form
        """
        time.sleep(2)
        self.validate_chain(chain)
        self.validate_token(token)

        token_address = self.chains_data[chain]["tokens"].get(token)
        rpc = self.chains_data[chain]["rpc"]

        if not token_address:
            raise ValueError(f"Token {token} not supported on chain {chain}")
        contract_address = self.sender_contracts.get(chain)
        if not contract_address:
            raise ValueError(f"Contract is not deployed on {chain}")
        print(f"Sending {token} to contract on chain : {chain}")
        txn_hash = send_erc20_to_contract(rpc, token_address, self.account, amount, contract_address)
        return txn_hash
    
    def send_eth_to_contract(self, chain:str, amount: float) -> str:
        time.sleep(3)
        self.validate_chain(chain)
        rpc = self.chains_data[chain]["rpc"]

        contract_address = self.sender_contracts.get(chain)
        if not contract_address:
            raise ValueError(f"Contract is not deployed on {chain}")
        print(f"Sending native eth to contract on chain : {chain}")
        txn_hash = send_native_eth(rpc, self.account, amount, contract_address)
        return txn_hash
    
    def allow_destination_chain(self, current_chain = None, destination_chain = None) -> str:
        time.sleep(3)
        if not current_chain or not destination_chain: 
            raise ValueError(f"Please provide valid current and destination chain")
        if not self.validate_chain(current_chain) or not self.sender_contracts.get(current_chain):
            raise ValueError("Chain is not deployed or not a part of CCIP directory")
        rpc = self.chains_data[current_chain]["rpc"]
        if not self.chains_data.get(destination_chain):
            raise ValueError(f"Destination chain not found in CCIP Directory")
        
        chainSelector = self.chains_data[destination_chain]["chain_selector"]
        contract = self.sender_contracts[current_chain]
        if not contract:
            raise ValueError(f"No Sender contract found on {current_chain}")
        print(f"Allowing the destination chain from current chain : {current_chain}")
        txn_hash = allowlistDestinationChain(rpc, chainSelector, contract, self.account, self.contract_compiled_file)
        return txn_hash
    
    def allow_source_chain(self, current_chain = None, sender_chain = None) -> str:
        time.sleep(3)
        if not current_chain or not sender_chain: 
            raise ValueError(f"Please provide valid current and destination chain")
        if not self.validate_chain(current_chain) or not self.sender_contracts.get(sender_chain):
            raise ValueError("Chain is not deployed or not a part of CCIP directory")
        if not self.receiver_contracts.get(current_chain):
            raise ValueError(f"Contract not deployed on chain : {current_chain}")
        rpc = self.chains_data[current_chain]["rpc"]
        if not self.chains_data.get(sender_chain):
            raise ValueError(f"Destination chain not found in CCIP Directory")
        
        chainSelector = self.chains_data[sender_chain]["chain_selector"]
        contract = self.receiver_contracts[current_chain]
        if not contract:
            raise ValueError(f"No Sender contract found on {current_chain}")
        print(f"Allowing the sender chain from receiver chain : {current_chain}")
        txn_hash = allowlistSourceChain(rpc, chainSelector, contract, self.account, self.contract_compiled_file)
        return txn_hash
    
    def allow_sender_on_receiver(self, sender_chain=None, receiver_chain=None):
        time.sleep(3)
        if not sender_chain or not receiver_chain: 
            raise ValueError(f"Please provide valid current and destination chain")
        if not self.sender_contracts.get(sender_chain) or not self.receiver_contracts.get(receiver_chain):
            raise ValueError("Chain is not deployed or not a part of CCIP directory")
        rpc = self.chains_data[receiver_chain]["rpc"]
        sender_contract = self.sender_contracts[sender_chain]
        receiver_contract = self.receiver_contracts[receiver_chain]
        print(f"Allowing the sender contract : {sender_contract} on reciever contract : {receiver_contract}")
        txn_hash = allowlistSender(rpc, sender_contract, receiver_contract, self.account, self.contract_compiled_file)
        return txn_hash
    
    def transfer(self, sender_chain=None, receiver_chain=None, text="None", amount=0.1, token="CCIP-BnM"):
        time.sleep(3)
        if not sender_chain or not receiver_chain: 
            raise ValueError(f"Please provide valid current and destination chain")
        if not self.sender_contracts.get(sender_chain) or not self.receiver_contracts.get(receiver_chain):
            raise ValueError("Chain is not deployed or not a part of CCIP directory")
        rpc = self.chains_data[sender_chain]["rpc"]
        sender_contract = self.sender_contracts[sender_chain]
        receiver_contract = self.receiver_contracts[receiver_chain]
        destination_chain_selector = self.chains_data[receiver_chain]["chain_selector"]
        token_address = self.chains_data[sender_chain]["tokens"][token]
        print(f"CCIP Transfer from chain {sender_chain} to destination chain {receiver_chain}")
        txn_hash = transfer(rpc, sender_contract, destination_chain_selector, receiver_contract, text, token_address, amount, self.account, self.contract_compiled_file)
        return f"https://ccip.chain.link/tx/{txn_hash}"
    
    def get_message_on_reciever_contract(self, receiver_chain: str, contract = None) -> str:
        """
        Function to get the message on the receiver contract
        :param receiver_chain: The chain on which the receiver contract is deployed
        :param[Optional] contract : contract address on the receiver network
        """
        if receiver_chain not in self.receiver_contracts:
            raise ValueError(f"Receiver contract not deployed on {receiver_chain}")
        
        rpc = self.chains_data[receiver_chain]["rpc"]
        if contract is None:
            contract_address = self.receiver_contracts[receiver_chain]
        
        print(f"Getting last received message on receiver contract on chain : {receiver_chain}")
        message = getLastReceivedMessage(rpc, contract_address, self.contract_compiled_file)
        return message
    
    def withdraw_token_to_wallet(self, chain: str, token: str, beneficiary: str) -> str:
        """
        :param chain: The chain on which the contract is deployed
        :param beneficiary: The address to which the tokens will be withdrawn
        """
        if chain not in self.chains:
            raise ValueError(f"Sender contract not deployed on {chain}")
        
        rpc = self.chains_data[chain]["rpc"]
        contract_address = self.receiver_contracts[chain]
        token_address = self.chains_data[chain]["tokens"][token]
        
        print(f"Withdrawing tokens to wallet on chain : {chain}")
        txn_hash = withdraw_token(rpc, contract_address, token_address, beneficiary, self.account, self.contract_compiled_file)
        return txn_hash
    
    def withdraw_eth_to_wallet(self, chain: str, beneficiary: str) -> str:
        """
        :param chain: The chain on which the contract is deployed
        :param beneficiary: The address to which the ETH will be withdrawn
        """
        if chain not in self.chains:
            raise ValueError(f"Sender contract not deployed on {chain}")
        
        rpc = self.chains_data[chain]["rpc"]
        contract_address = self.receiver_contracts[chain]
        
        print(f"Withdrawing ETH to wallet on chain : {chain}")
        txn_hash = withdraw_eth(rpc, contract_address, beneficiary, self.account, self.contract_compiled_file)
        return txn_hash

    def validate_chain(self, chain: str):
        """
        Function that checks if the chain is valid
        """
        if chain not in self.chains:
            raise ValueError(f"Chain {chain} is not supported.")
        return True
    
    def validate_token(self, token: str):
        """
        Function that checks if the token is valid and supported
        """
        if token not in self.tokens:
            raise ValueError(f"Token {token} is not supported")
        return True

    