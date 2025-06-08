from dataclasses import dataclass


@dataclass(frozen=True)
class CCIPConfig:
    """
    config for ccip client
    RPC_URL's for ccip directory based chains 
    """
    chains = {}
    ccip_explorer = "https://ccip.chain.link/#/side-drawer/"
