# CCIP SDK

A simple Python SDK for Chainlink CCIP (Cross-Chain Interoperability Protocol) that enables seamless cross-chain token transfers and messaging.

## Features

- 🚀 Deploy sender and receiver contracts across multiple testnets
- 💰 Send tokens and ETH to contracts
- 🔗 Configure cross-chain permissions
- ⚡ Execute cross-chain transfers with built-in monitoring
- 📊 Transaction tracking and URL generation

## Installation

```bash
pip install ccip-sdk
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in your project root:

```env
PRIVATE_KEY=your_private_key_here
```

### 2. Basic Usage

```python
from ccip_sdk import CCIPClient
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize client
client = CCIPClient(private_key=os.environ.get("PRIVATE_KEY"))

# Deploy contracts and perform cross-chain transfer
contract = client.deploy_sender_contract("ethereum_sepolia")
print(f"Deployed contract address: {contract}")

# Fund the contract
txn_hash = client.send_tokens_to_sender_contract("ethereum_sepolia", "CCIP-BnM", 0.1)
print(f"Tokens sent: {txn_hash}")

# Transfer across chains
txn_url = client.transfer(
    sender_chain="ethereum_sepolia", 
    receiver_chain="arbitrum_sepolia", 
    text="Hello Cross-Chain!", 
    amount=0.069
)
print(f"Track transfer: {txn_url}")
```

## Complete Example

```python
from ccip_sdk import CCIPClient
from dotenv import load_dotenv
import os

load_dotenv()

client = CCIPClient(private_key=os.environ.get("PRIVATE_KEY"))

# Step 1: Deploy sender contract on Ethereum Sepolia
contract = client.deploy_sender_contract("ethereum_sepolia")
print(f"Deployed contract address: {contract}\n")

# Step 2: Fund sender contract with tokens
txn_hash = client.send_tokens_to_sender_contract("ethereum_sepolia", "CCIP-BnM", 0.1)
print(f"Token sent via this transaction hash : {txn_hash}\n")

# Step 3: Fund sender contract with ETH (for gas fees)
txn_hash = client.send_eth_to_contract("ethereum_sepolia", 0.05)
print(f"ETH sent via this transaction hash : {txn_hash}\n")

# Step 4: Allow destination chain for cross-chain messaging
txn_hash = client.allow_destination_chain(current_chain="ethereum_sepolia", destination_chain="arbitrum_sepolia")
print(f"Allowed destination chain arbitrum_sepolia done with txnHash : {txn_hash}\n")

# Step 5: Deploy receiver contract on Arbitrum Sepolia
contract = client.deploy_receiver_contract("arbitrum_sepolia")
print(f"Deployed contract address: {contract}\n")

# Step 6: Allow source chain on receiver
txn_hash = client.allow_source_chain(current_chain="arbitrum_sepolia", sender_chain="ethereum_sepolia")
print(f"Allowed sender chain ethereum_sepolia done with txnHash : {txn_hash}\n")

# Step 7: Allow sender contract to send messages to receiver
txn_hash = client.allow_sender_on_receiver(sender_chain="ethereum_sepolia", receiver_chain="arbitrum_sepolia")
print(f"Allowed the sender contract to send messages on reciever chain with txnHash : {txn_hash}\n")

# Step 8: Execute cross-chain transfer
txn_url = client.transfer(sender_chain="ethereum_sepolia", receiver_chain="arbitrum_sepolia", text="Hi dj boi", amount=0.069)
print(f"You can watch the CCIP Transfer here : {txn_url}\n")
```

## Step-by-Step Explanation

### 1. **Contract Deployment**
- `deploy_sender_contract()`: Deploys a contract that can send cross-chain messages
- `deploy_receiver_contract()`: Deploys a contract that can receive cross-chain messages

### 2. **Contract Funding**
- `send_tokens_to_sender_contract()`: Funds the sender with tokens for transfer
- `send_eth_to_contract()`: Funds the sender with ETH for transaction fees

### 3. **Permission Setup**
- `allow_destination_chain()`: Authorizes the sender to communicate with a specific destination chain
- `allow_source_chain()`: Authorizes the receiver to accept messages from a specific source chain
- `allow_sender_on_receiver()`: Links sender and receiver contracts for communication

### 4. **Cross-Chain Transfer**
- `transfer()`: Executes the cross-chain token transfer with optional message

## Supported Networks

| Chain Name | Network | Purpose |
|------------|---------|---------|
| `ethereum_sepolia` | Ethereum Sepolia Testnet | Primary testing network |
| `arbitrum_sepolia` | Arbitrum Sepolia Testnet | L2 scaling solution |
| `base_sepolia` | Base Sepolia Testnet | Coinbase L2 network |
| `avalanche_fuji` | Avalanche Fuji Testnet | High-performance blockchain |

## Supported Tokens

| Token | Description | Use Case |
|-------|-------------|----------|
| `LINK` | Chainlink Token | Network fees and staking |
| `CCIP-BnM` | Burn and Mint Token | Cross-chain transfers |
| `USDC` | USD Coin | Stable value transfers |
| `CCIP-LnM` | Lock and Mint Token | Alternative transfer mechanism |

## Requirements

- Python 3.7+
- Valid private key with testnet funds
- Access to supported testnet RPCs

## Security Note

⚠️ **Never commit your private key to version control.** Always use environment variables or secure key management solutions.

## Contributing

We welcome contributions! Here's how you can help:

### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/your-username/ccip_sdk.git
cd ccip_sdk
pip install -e .
pip install -r requirements-dev.txt
```

### Running Tests
```bash
pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings for public methods
- Ensure 80% test coverage

### Issues and Feature Requests
- Check existing issues before creating new ones
- Provide detailed descriptions and reproduction steps
- Tag issues appropriately (bug, enhancement, documentation)

### Documentation
- Update README.md for new features
- Add inline code documentation
- Provide usage examples

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📖 [Documentation](https://github.com/dhananjaypai08/ccip_sdk/docs) [Coming soon]
- 🐛 [Issue Tracker](https://github.com/dhananjaypai08/ccip_sdk/issues)
