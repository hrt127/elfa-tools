"""
onchain_client.py - On-chain metrics client

Fetches on-chain data like exchange flows, whale activity, and address metrics.
Designed to be composable with signal_composer and other tools.

Follows the same design principles:
- Narrow: One job (fetch on-chain metrics)
- Explainable: Clear data structures and source queries
- Robust: Never crashes, graceful error handling
- Composable: Works with signal_composer, alerts_engine, etc.

Note: This is a template/skeleton. Actual implementation depends on:
- Which on-chain data provider you use (Glassnode, CryptoQuant, custom APIs, etc.)
- Which metrics you need (exchange flows, whale wallets, active addresses, etc.)
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from collections import defaultdict
import requests  # pyright: ignore[reportMissingModuleSource]


# Global state for rate limiting and caching
_rate_limit_tracker: Dict[str, list] = defaultdict(list)
_cache: Dict[str, tuple] = {}
_cache_ttl = 600  # 10 minutes default cache TTL (on-chain data changes slower)


@dataclass
class OnChainData:
    """On-chain metrics for a cryptocurrency."""
    ticker: str
    exchange_netflow_btc: Optional[float] = None  # Net flow to/from exchanges (BTC)
    whale_balance_change: Optional[int] = None  # Change in whale wallet balances (+1 = accumulating, -1 = distributing)
    active_addresses_24h: Optional[int] = None  # Active addresses in 24h
    active_addresses_ratio: Optional[float] = None  # Active addresses vs 7d average
    transaction_count_24h: Optional[int] = None  # Transaction count in 24h
    timestamp: float = field(default_factory=time.time)
    source_query: str = field(default="")  # For audit trail


def _get_cache_key(ticker: str) -> str:
    """Generate a cache key for the given ticker."""
    return f"onchain:{ticker.upper()}"


def _is_rate_limited(endpoint: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
    """Check if we're rate limited for the given endpoint."""
    global _rate_limit_tracker
    now = time.time()
    
    # Clean old entries
    _rate_limit_tracker[endpoint] = [
        ts for ts in _rate_limit_tracker[endpoint]
        if now - ts < window_seconds
    ]
    
    if len(_rate_limit_tracker[endpoint]) >= max_requests:
        return True
    
    _rate_limit_tracker[endpoint].append(now)
    return False


def _get_cached_result(cache_key: str) -> Optional[OnChainData]:
    """Get a cached result if it exists and hasn't expired."""
    global _cache
    if cache_key in _cache:
        result, expiry_time = _cache[cache_key]
        if time.time() < expiry_time:
            return result
        else:
            del _cache[cache_key]
    return None


def _cache_result(cache_key: str, result: OnChainData, ttl: int = None) -> None:
    """Cache a result with the given TTL."""
    global _cache, _cache_ttl
    if ttl is None:
        ttl = _cache_ttl
    expiry_time = time.time() + ttl
    _cache[cache_key] = (result, expiry_time)


def get_onchain_data(
    ticker: str,
    use_cache: bool = True,
    api_provider: str = "glassnode",
    use_fallback: bool = True,
    fallback_providers: Optional[List[str]] = None
) -> Optional[OnChainData]:
    """
    Get on-chain metrics for a ticker with automatic fallback to backup providers.
    
    Args:
        ticker: Ticker symbol (e.g., "BTC", "ETH")
        use_cache: Whether to use cached results
        api_provider: Primary API provider ("glassnode", "cryptoquant", "zapper", "zerion", "covalent")
        use_fallback: If True, automatically try backup providers if primary fails
        fallback_providers: List of backup providers to try. If None and use_fallback=True,
                          uses default fallback chain: ["glassnode", "cryptoquant", "zapper", "zerion", "covalent"]
    
    Returns:
        OnChainData with on-chain metrics, or None if unavailable.
        Never raises exceptions - all errors are handled gracefully.
    """
    try:
        # Check cache first
        if use_cache:
            cache_key = _get_cache_key(ticker)
            cached_result = _get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Check rate limiting for primary provider
        primary_rate_limited = _is_rate_limited(api_provider, max_requests=10, window_seconds=60)
        if primary_rate_limited:
            if use_fallback:
                print(f"Warning: Rate limit reached for {api_provider}, trying fallback providers...")
                # Skip the rate-limited primary provider in fallback chain
                if fallback_providers is None:
                    from optional.provider_registry import list_providers
                    fallback_providers = list_providers()
                # Remove primary from fallback list and use first fallback as primary
                fallback_list = [p for p in fallback_providers if p.lower() != api_provider.lower()]
                if fallback_list:
                    # Use first fallback as new primary, rest as fallbacks
                    new_primary = fallback_list[0]
                    remaining_fallbacks = fallback_list[1:] if len(fallback_list) > 1 else []
                    from optional.provider_registry import fetch_with_fallback
                    result = fetch_with_fallback(
                        ticker=ticker,
                        primary_provider=new_primary,
                        fallback_providers=remaining_fallbacks
                    )
                else:
                    print(f"Warning: No fallback providers available after excluding rate-limited {api_provider}")
                    return None
            else:
                print(f"Warning: Rate limit reached for {api_provider}")
                return None
        elif use_fallback:
            # Primary not rate-limited, use normal fallback
            from optional.provider_registry import fetch_with_fallback
            result = fetch_with_fallback(
                ticker=ticker,
                primary_provider=api_provider,
                fallback_providers=fallback_providers
            )
        else:
            # Single provider mode (legacy behavior)
            from optional.provider_registry import get_provider, list_providers
            provider_fn = get_provider(api_provider)
            if not provider_fn:
                available = list_providers()
                print(f"Warning: Unknown provider '{api_provider}'. Available: {', '.join(available)}")
                return None
            result = provider_fn(ticker)
        
        # Cache result if successful
        if result and use_cache:
            cache_key = _get_cache_key(ticker)
            _cache_result(cache_key, result)
        
        return result
    
    except Exception as e:
        print(f"Warning: Unexpected error in get_onchain_data: {str(e)[:200]}")
        return None


def _fetch_glassnode_onchain_data(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from Glassnode API.
    
    Requires GLASSNODE_API_KEY environment variable.
    
    Glassnode API Documentation: https://docs.glassnode.com/
    """
    try:
        api_key = os.getenv("GLASSNODE_API_KEY")
        if not api_key:
            print("Warning: GLASSNODE_API_KEY environment variable not set.")
            return None
        
        # Map ticker to Glassnode asset symbol
        asset_map = {
            "BTC": "btc",
            "ETH": "eth",
            "SOL": "sol",
            "BNB": "bnb",
            "ADA": "ada",
            "DOT": "dot",
            "MATIC": "matic",
            "AVAX": "avax"
        }
        
        asset = asset_map.get(ticker.upper())
        if not asset:
            print(f"Warning: Ticker {ticker} not supported by Glassnode")
            return None
        
        base_url = "https://api.glassnode.com/v1/metrics"
        params = {
            "a": asset,
            "api_key": api_key,
            "i": "24h"  # 24-hour interval
        }
        
        source_queries = []
        exchange_netflow = None
        active_addresses_24h = None
        transaction_count_24h = None
        whale_balance_change = None
        active_addresses_ratio = None
        
        # Fetch exchange netflow
        try:
            url = f"{base_url}/transactions/transfers_volume_exchanges_net"
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Get most recent value
                    latest = data[-1]
                    exchange_netflow = latest.get("v", 0) / 1e8  # Convert satoshis to BTC
                    source_queries.append(f"exchange_netflow:{url}")
        except Exception as e:
            print(f"Warning: Failed to fetch exchange netflow: {str(e)[:100]}")
        
        # Fetch active addresses (24h)
        try:
            url = f"{base_url}/addresses/active_count"
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest = data[-1]
                    active_addresses_24h = int(latest.get("v", 0))
                    source_queries.append(f"active_addresses:{url}")
                    
                    # Calculate ratio vs 7-day average
                    if len(data) >= 7:
                        recent_7d = [d.get("v", 0) for d in data[-7:]]
                        avg_7d = sum(recent_7d) / len(recent_7d) if recent_7d else 0
                        if avg_7d > 0:
                            active_addresses_ratio = active_addresses_24h / avg_7d
        except Exception as e:
            print(f"Warning: Failed to fetch active addresses: {str(e)[:100]}")
        
        # Fetch transaction count (24h)
        try:
            url = f"{base_url}/transactions/count"
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest = data[-1]
                    transaction_count_24h = int(latest.get("v", 0))
                    source_queries.append(f"transaction_count:{url}")
        except Exception as e:
            print(f"Warning: Failed to fetch transaction count: {str(e)[:100]}")
        
        # Fetch whale balance change (large holders)
        # Using addresses_count with balance threshold as proxy
        try:
            # Get addresses with >1000 BTC (or equivalent for other assets)
            threshold_map = {"btc": 1000, "eth": 10000, "sol": 100000}
            threshold = threshold_map.get(asset, 1000)
            
            url = f"{base_url}/addresses/count"
            whale_params = {**params, "threshold": threshold}
            response = requests.get(url, params=whale_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) >= 2:
                    # Compare current vs 7 days ago
                    current = data[-1].get("v", 0)
                    previous = data[-7].get("v", 0) if len(data) >= 7 else data[0].get("v", 0)
                    whale_balance_change = 1 if current > previous else (-1 if current < previous else 0)
                    source_queries.append(f"whale_balance:{url}")
        except Exception as e:
            print(f"Warning: Failed to fetch whale metrics: {str(e)[:100]}")
        
        # Only return data if we got at least one metric
        if not any([exchange_netflow is not None, active_addresses_24h is not None, 
                   transaction_count_24h is not None, whale_balance_change is not None]):
            return None
        
        return OnChainData(
            ticker=ticker.upper(),
            exchange_netflow_btc=exchange_netflow,
            whale_balance_change=whale_balance_change,
            active_addresses_24h=active_addresses_24h,
            active_addresses_ratio=active_addresses_ratio,
            transaction_count_24h=transaction_count_24h,
            source_query="; ".join(source_queries) if source_queries else f"glassnode:{asset}"
        )
    
    except Exception as e:
        print(f"Warning: Failed to fetch Glassnode data: {str(e)[:200]}")
        return None


def _fetch_cryptoquant_onchain_data(ticker: str) -> Optional[OnChainData]:
    """
    Fetch on-chain data from CryptoQuant API.
    
    Requires CRYPTOQUANT_API_KEY environment variable.
    
    This is a template - implement based on CryptoQuant API docs.
    """
    try:
        api_key = os.getenv("CRYPTOQUANT_API_KEY")
        if not api_key:
            print("Warning: CRYPTOQUANT_API_KEY environment variable not set.")
            return None
        
        # TODO: Implement actual API calls
        print("Warning: CryptoQuant integration not yet implemented")
        return None
    
    except Exception as e:
        print(f"Warning: Failed to fetch CryptoQuant data: {str(e)[:200]}")
        return None


def clear_cache() -> None:
    """Clear all cached results."""
    global _cache
    _cache.clear()


# Usage example
if __name__ == "__main__":
    # Example 1: Get BTC on-chain data with automatic fallback
    print("Example 1: Automatic fallback (Glassnode → CryptoQuant → ...)")
    btc_data = get_onchain_data("BTC", use_cache=False, use_fallback=True)
    if btc_data:
        print(f"\n✅ BTC On-Chain Data (from {btc_data.source_query.split(':')[0]}):")
        if btc_data.exchange_netflow_btc:
            print(f"   Exchange Net Flow: {btc_data.exchange_netflow_btc:+.2f} BTC")
        if btc_data.whale_balance_change:
            status = "Accumulating" if btc_data.whale_balance_change > 0 else "Distributing"
            print(f"   Whale Activity: {status}")
        if btc_data.active_addresses_24h:
            print(f"   Active Addresses (24h): {btc_data.active_addresses_24h:,}")
        print(f"   Source: {btc_data.source_query}")
    else:
        print("❌ On-chain data not available (all providers failed)")
    
    # Example 2: Single provider (no fallback)
    print("\n\nExample 2: Single provider mode (no fallback)")
    btc_data2 = get_onchain_data("BTC", use_cache=False, api_provider="glassnode", use_fallback=False)
    if btc_data2:
        print(f"✅ Got data from: {btc_data2.source_query}")
    else:
        print("❌ Provider failed")
    
    # Example 3: Custom fallback chain
    print("\n\nExample 3: Custom fallback chain")
    btc_data3 = get_onchain_data("BTC", use_cache=False, api_provider="cryptoquant", 
                                  use_fallback=True, fallback_providers=["glassnode", "zapper"])
    if btc_data3:
        print(f"✅ Got data from: {btc_data3.source_query}")
    else:
        print("❌ All providers failed")

