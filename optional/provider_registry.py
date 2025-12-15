"""
provider_registry.py - Multi-provider on-chain data registry with fallback logic

Provides a unified interface to multiple on-chain data providers with automatic
fallback when primary providers fail or are rate-limited.

Design Principles:
- Redundancy: Multiple providers for the same data
- Graceful degradation: Fallback to backup providers
- Provider-agnostic: Same OnChainData structure regardless of source
- Robust: Never crashes, handles all errors gracefully
"""

import os
import time
from typing import Optional, Callable, List, Dict
from optional.onchain_client import OnChainData


# Provider function type
ProviderFunc = Callable[[str], Optional[OnChainData]]


def fetch_glassnode(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from Glassnode API.
    
    Glassnode provides comprehensive on-chain metrics including:
    - Exchange netflow
    - Active addresses
    - Transaction counts
    - Whale wallet metrics
    
    Requires GLASSNODE_API_KEY environment variable.
    """
    try:
        from optional.onchain_client import _fetch_glassnode_onchain_data
        return _fetch_glassnode_onchain_data(ticker)
    except Exception as e:
        print(f"Warning: Glassnode fetch failed: {str(e)[:100]}")
        return None


def fetch_cryptoquant(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from CryptoQuant API.
    
    CryptoQuant provides:
    - Exchange flows
    - Miner reserves
    - Stablecoin metrics
    - Network activity
    
    Requires CRYPTOQUANT_API_KEY environment variable.
    """
    try:
        from optional.onchain_client import _fetch_cryptoquant_onchain_data
        return _fetch_cryptoquant_onchain_data(ticker)
    except Exception as e:
        print(f"Warning: CryptoQuant fetch failed: {str(e)[:100]}")
        return None


def fetch_zapper(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from Zapper API.
    
    Zapper provides:
    - Portfolio balances
    - DeFi positions
    - Multi-chain data
    - Wallet analytics
    
    Note: This is a placeholder - implement based on Zapper API docs.
    Zapper API: https://docs.zapper.fi/
    """
    try:
        api_key = os.getenv("ZAPPER_API_KEY")
        if not api_key:
            # Silently fail if no API key (not all providers need keys)
            return None
        
        # TODO: Implement Zapper API integration
        # Example endpoints:
        # - GET /v2/balances/apps?addresses[]={address}
        # - GET /v2/balances/tokens?addresses[]={address}
        
        print("Warning: Zapper integration not yet implemented")
        return None
    
    except Exception as e:
        print(f"Warning: Zapper fetch failed: {str(e)[:100]}")
        return None


def fetch_zerion(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from Zerion API.
    
    Zerion provides:
    - Wallet balances
    - NFT holdings
    - DeFi positions
    - Multi-chain portfolio data
    
    Note: This is a placeholder - implement based on Zerion API docs.
    Zerion API: https://docs.zerion.io/
    """
    try:
        api_key = os.getenv("ZERION_API_KEY")
        if not api_key:
            return None
        
        # TODO: Implement Zerion API integration
        # Example endpoints:
        # - GET /v1/wallets/{address}/positions
        # - GET /v1/wallets/{address}/nfts
        
        print("Warning: Zerion integration not yet implemented")
        return None
    
    except Exception as e:
        print(f"Warning: Zerion fetch failed: {str(e)[:100]}")
        return None


def fetch_covalent(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from Covalent API.
    
    Covalent provides:
    - Multi-chain transactions
    - Token balances
    - Historical data
    - NFT metadata
    
    Note: This is a placeholder - implement based on Covalent API docs.
    Covalent API: https://www.covalenthq.com/docs/api/
    """
    try:
        api_key = os.getenv("COVALENT_API_KEY")
        if not api_key:
            return None
        
        # TODO: Implement Covalent API integration
        # Example endpoints:
        # - GET /v1/{chain_id}/address/{address}/balances_v2/
        # - GET /v1/{chain_id}/transactions_v2/
        
        print("Warning: Covalent integration not yet implemented")
        return None
    
    except Exception as e:
        print(f"Warning: Covalent fetch failed: {str(e)[:100]}")
        return None


# Provider registry
PROVIDERS: Dict[str, ProviderFunc] = {
    "glassnode": fetch_glassnode,
    "cryptoquant": fetch_cryptoquant,
    "zapper": fetch_zapper,
    "zerion": fetch_zerion,
    "covalent": fetch_covalent,
}


def get_provider(provider_name: str) -> Optional[ProviderFunc]:
    """
    Get a provider function by name.
    
    Args:
        provider_name: Name of the provider (case-insensitive)
        
    Returns:
        Provider function or None if not found
    """
    return PROVIDERS.get(provider_name.lower())


def list_providers() -> List[str]:
    """List all available provider names."""
    return list(PROVIDERS.keys())


def fetch_with_fallback(
    ticker: str,
    primary_provider: str = "glassnode",
    fallback_providers: Optional[List[str]] = None
) -> Optional[OnChainData]:
    """
    Fetch on-chain data with automatic fallback to backup providers.
    
    Args:
        ticker: Ticker symbol (e.g., "BTC", "ETH")
        primary_provider: Primary provider to try first
        fallback_providers: List of backup providers to try if primary fails.
                          If None, uses default fallback chain:
                          ["glassnode", "cryptoquant", "zapper", "zerion", "covalent"]
    
    Returns:
        OnChainData from first successful provider, or None if all fail
    """
    if fallback_providers is None:
        # Default fallback chain: try all providers in order
        fallback_providers = ["glassnode", "cryptoquant", "zapper", "zerion", "covalent"]
    
    # Ensure primary is first in the list
    providers_to_try = [primary_provider]
    for provider in fallback_providers:
        if provider.lower() != primary_provider.lower() and provider.lower() in PROVIDERS:
            providers_to_try.append(provider.lower())
    
    # Try each provider until one succeeds
    for provider_name in providers_to_try:
        provider_fn = get_provider(provider_name)
        if not provider_fn:
            print(f"Warning: Unknown provider '{provider_name}', skipping")
            continue
        
        try:
            result = provider_fn(ticker)
            if result is not None:
                # Add provider name to source_query for audit trail
                if result.source_query:
                    result.source_query = f"{provider_name}:{result.source_query}"
                else:
                    result.source_query = provider_name
                return result
        except Exception as e:
            print(f"Warning: Provider '{provider_name}' raised exception: {str(e)[:100]}")
            continue
    
    # All providers failed
    print(f"Warning: All providers failed for ticker {ticker}")
    return None


# Usage example
if __name__ == "__main__":
    # Example: Try Glassnode first, fallback to CryptoQuant
    btc_data = fetch_with_fallback("BTC", primary_provider="glassnode", 
                                    fallback_providers=["cryptoquant"])
    
    if btc_data:
        print(f"\n✅ Got on-chain data for {btc_data.ticker}")
        print(f"   Source: {btc_data.source_query}")
        if btc_data.exchange_netflow_btc:
            print(f"   Exchange Netflow: {btc_data.exchange_netflow_btc:+.2f} BTC")
    else:
        print("❌ Failed to get on-chain data from any provider")

