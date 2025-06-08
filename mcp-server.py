import asyncio
import logging
from typing import Any, Dict, List, Optional
import json
import os
from difflib import get_close_matches

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
import mcp.types as types

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CCIP")

# Supported chains mapping
SUPPORTED_CHAINS = {
    "ethereum_sepolia": ["ethereum", "eth", "sepolia", "ethereum sepolia", "eth sepolia", "ethereum_sepolia"],
    "base_sepolia": ["base", "base sepolia", "base_sepolia", "coinbase"],
    "arbitrum_sepolia": ["arbitrum", "arb", "arbitrum sepolia", "arbitrum_sepolia", "arb sepolia"],
    "avalanche_fuji": ["avalanche", "avax", "fuji", "avalanche fuji", "avalanche_fuji", "avax fuji"]
}

def find_closest_chain(user_input: str) -> Optional[str]:
    """Find the closest matching chain from user input"""
    user_input_lower = user_input.lower().strip()
    
    # Direct match first
    for chain_key, aliases in SUPPORTED_CHAINS.items():
        if user_input_lower in [alias.lower() for alias in aliases]:
            return chain_key
    
    # Fuzzy matching
    all_aliases = []
    chain_mapping = {}
    for chain_key, aliases in SUPPORTED_CHAINS.items():
        for alias in aliases:
            all_aliases.append(alias.lower())
            chain_mapping[alias.lower()] = chain_key
    
    matches = get_close_matches(user_input_lower, all_aliases, n=1, cutoff=0.6)
    if matches:
        return chain_mapping[matches[0]]
    
    return None

# Create server instance
server = Server("CCIP")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="execute_ccip_transfer",
            description="Execute complete CCIP cross-chain transfer in one go",
            inputSchema={
                "type": "object",
                "properties": {
                    "sender_chain": {
                        "type": "string",
                        "description": "Source blockchain (ethereum, arbitrum, base, avalanche, etc.)"
                    },
                    "receiver_chain": {
                        "type": "string", 
                        "description": "Destination blockchain"
                    },
                    "private_key": {
                        "type": "string",
                        "description": "Private key for transactions"
                    },
                    "token_type": {
                        "type": "string",
                        "description": "Token to transfer (LINK, CCIP-BnM, USDC, CCIP-LnM)",
                        "default": "CCIP-BnM"
                    },
                    "token_amount": {
                        "type": "number",
                        "description": "Amount of tokens to fund sender contract",
                        "default": 0.1
                    },
                    "eth_amount": {
                        "type": "number", 
                        "description": "Amount of ETH for gas fees",
                        "default": 0.05
                    },
                    "transfer_amount": {
                        "type": "number",
                        "description": "Amount to transfer cross-chain", 
                        "default": 0.069
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send with transfer",
                        "default": "Cross-chain transfer via MCP"
                    }
                },
                "required": ["sender_chain", "receiver_chain", "private_key"]
            }
        ),
        Tool(
            name="find_supported_chain",
            description="Find supported chain name from user input",
            inputSchema={
                "type": "object",
                "properties": {
                    "chain_input": {
                        "type": "string",
                        "description": "User input for chain name"
                    }
                },
                "required": ["chain_input"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    
    if name == "execute_ccip_transfer":
        try:
            # Get and validate inputs
            sender_input = arguments["sender_chain"]
            receiver_input = arguments["receiver_chain"] 
            private_key = arguments["private_key"]
            
            # Map chains
            sender_chain = find_closest_chain(sender_input)
            receiver_chain = find_closest_chain(receiver_input)
            
            if not sender_chain:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Invalid sender chain '{sender_input}'. Supported: {list(SUPPORTED_CHAINS.keys())}"
                )]
                
            if not receiver_chain:
                return [types.TextContent(
                    type="text", 
                    text=f"❌ Invalid receiver chain '{receiver_input}'. Supported: {list(SUPPORTED_CHAINS.keys())}"
                )]
                
            if sender_chain == receiver_chain:
                return [types.TextContent(
                    type="text",
                    text="❌ Sender and receiver chains must be different"
                )]
            
            # Get optional parameters
            token_type = arguments.get("token_type", "CCIP-BnM")
            token_amount = arguments.get("token_amount", 0.1)
            eth_amount = arguments.get("eth_amount", 0.05)
            transfer_amount = arguments.get("transfer_amount", 0.069)
            message = arguments.get("message", "Cross-chain transfer via MCP")
            
            # Import and initialize CCIP client
            from ccip_sdk import CCIPClient
            client = CCIPClient(private_key=private_key)
            
            result_text = f"""🚀 **Starting CCIP Cross-Chain Transfer**

📋 **Configuration:**
• **From:** {sender_chain}
• **To:** {receiver_chain}
• **Token:** {token_type}
• **Amount:** {transfer_amount}
• **Message:** "{message}"

⏳ **Executing all steps...**

"""
            
            # Step 1: Deploy sender contract
            result_text += "🔄 **Step 1:** Deploying sender contract...\n"
            sender_contract = client.deploy_sender_contract(sender_chain)
            result_text += f"✅ Sender contract deployed: `{sender_contract}`\n\n"
            
            # Step 2: Send tokens to sender contract
            result_text += f"🔄 **Step 2:** Sending {token_amount} {token_type} to sender...\n"
            token_txn = client.send_tokens_to_sender_contract(sender_chain, token_type, token_amount)
            result_text += f"✅ Tokens sent: `{token_txn}`\n\n"
            
            # Step 3: Send ETH to contract
            result_text += f"🔄 **Step 3:** Sending {eth_amount} ETH for gas...\n"
            eth_txn = client.send_eth_to_contract(sender_chain, eth_amount)
            result_text += f"✅ ETH sent: `{eth_txn}`\n\n"
            
            # Step 4: Allow destination chain
            result_text += f"🔄 **Step 4:** Configuring destination chain ({receiver_chain})...\n"
            dest_txn = client.allow_destination_chain(current_chain=sender_chain, destination_chain=receiver_chain)
            result_text += f"✅ Destination configured: `{dest_txn}`\n\n"
            
            # Step 5: Deploy receiver contract
            result_text += "🔄 **Step 5:** Deploying receiver contract...\n"
            receiver_contract = client.deploy_receiver_contract(receiver_chain)
            result_text += f"✅ Receiver contract deployed: `{receiver_contract}`\n\n"
            
            # Step 6: Allow source chain
            result_text += f"🔄 **Step 6:** Configuring source chain ({sender_chain})...\n"
            source_txn = client.allow_source_chain(current_chain=receiver_chain, sender_chain=sender_chain)
            result_text += f"✅ Source configured: `{source_txn}`\n\n"
            
            # Step 7: Allow sender on receiver
            result_text += "🔄 **Step 7:** Linking sender and receiver contracts...\n"
            link_txn = client.allow_sender_on_receiver(sender_chain=sender_chain, receiver_chain=receiver_chain)
            result_text += f"✅ Contracts linked: `{link_txn}`\n\n"
            
            # Step 8: Execute transfer
            result_text += f"🔄 **Step 8:** Executing cross-chain transfer of {transfer_amount} {token_type}...\n"
            transfer_url = client.transfer(
                sender_chain=sender_chain,
                receiver_chain=receiver_chain,
                text=message,
                amount=transfer_amount
            )
            
            result_text += f"""🎉 **TRANSFER COMPLETE!**

✨ **Success!** Cross-chain transfer executed successfully!

🔗 **Track Transfer:** {transfer_url}

📊 **Summary:**
• **Sender Contract:** `{sender_contract}`
• **Receiver Contract:** `{receiver_contract}`
• **From:** {sender_chain} 
• **To:** {receiver_chain}
• **Amount:** {transfer_amount} {token_type}
• **Message:** "{message}"

🎯 **All 8 steps completed successfully!**
"""
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            error_msg = f"""❌ **Transfer Failed**

**Error:** {str(e)}

**Troubleshooting:**
• Check your private key has sufficient funds on both chains
• Verify chain names are correct
• Ensure token type is supported
• Check network connectivity

**Supported Chains:** {list(SUPPORTED_CHAINS.keys())}
**Supported Tokens:** LINK, CCIP-BnM, USDC, CCIP-LnM
"""
            return [types.TextContent(type="text", text=error_msg)]
    
    elif name == "find_supported_chain":
        chain_input = arguments["chain_input"]
        match = find_closest_chain(chain_input)
        
        if match:
            return [types.TextContent(
                type="text",
                text=f"✅ **Chain Found:** `{chain_input}` → `{match}`"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ **No Match:** `{chain_input}`\n\nSupported: {list(SUPPORTED_CHAINS.keys())}"
            )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="CCIP",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())