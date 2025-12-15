"""
perp_client.py - Perpetual futures market data client

Fetches funding rates, open interest, and price data for perpetual futures.
Designed to be composable with signal_composer and other tools.

Follows the same design principles:
- Narrow: One job (fetch perp market data)
- Explainable: Clear data structures and source queries
- Robust: Never crashes, graceful error handling
- Composable: Works with signal_composer, alerts_engine, etc.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from collections import defaultdict
import requests  # pyright: ignore[reportMissingModuleSource]


# Global state for rate limiting and caching
_rate_limit_tracker: Dict[str, list] = defaultdict(list)
_cache: Dict[str, tuple] = {}
_cache_ttl = 300  # 5 minutes default cache TTL


@dataclass
class PerpMarketData:
    """Market data for a perpetual futures contract."""
    ticker: str
    funding_rate: float  # Daily funding rate (e.g., 0.0001 = 0.01%)
    open_interest: Optional[float] = None  # Total open interest
    price: Optional[float] = None  # Current price
    price_change_24h: Optional[float] = None  # 24h price change %
    volume_24h: Optional[float] = None  # 24h volume
    volume_ratio: Optional[float] = None  # Volume vs 7d average
    timestamp: float = field(default_factory=time.time)
    source_query: str = field(default="")  # For audit trail


def _get_cache_key(ticker: str) -> str:
    """Generate a cache key for the given ticker."""
    return f"perp:{ticker.upper()}"


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


def _get_cached_result(cache_key: str) -> Optional[PerpMarketData]:
    """Get a cached result if it exists and hasn't expired."""
    global _cache
    if cache_key in _cache:
        result, expiry_time = _cache[cache_key]
        if time.time() < expiry_time:
            return result
        else:
            del _cache[cache_key]
    return None


def _cache_result(cache_key: str, result: PerpMarketData, ttl: int = None) -> None:
    """Cache a result with the given TTL."""
    global _cache, _cache_ttl
    if ttl is None:
        ttl = _cache_ttl
    expiry_time = time.time() + ttl
    _cache[cache_key] = (result, expiry_time)


def get_perp_market_data(
    ticker: str, 
    use_cache: bool = True,
    api_provider: str = "binance"  # Default to Binance, can be extended
) -> Optional[PerpMarketData]:
    """
    Get perpetual futures market data for a ticker.
    
    Currently supports Binance. Can be extended to support other exchanges.
    
    Args:
        ticker: Ticker symbol (e.g., "BTC", "ETH")
        use_cache: Whether to use cached results
        api_provider: API provider ("binance" currently supported)
    
    Returns:
        PerpMarketData with funding rate and market metrics, or None if unavailable.
        Never raises exceptions - all errors are handled gracefully.
    """
    try:
        # Check cache first
        if use_cache:
            cache_key = _get_cache_key(ticker)
            cached_result = _get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        if api_provider.lower() == "binance":
            return _fetch_binance_perp_data(ticker, use_cache)
        else:
            print(f"Warning: Unsupported API provider: {api_provider}")
            return None
    
    except Exception as e:
        print(f"Warning: Unexpected error in get_perp_market_data: {str(e)[:200]}")
        return None


def _fetch_binance_perp_data(ticker: str, use_cache: bool) -> Optional[PerpMarketData]:
    """
    Fetch perpetual futures data from Binance API.
    
    Never raises exceptions.
    """
    try:
        endpoint = "https://fapi.binance.com/fapi/v1/premiumIndex"
        
        # Check rate limiting
        if _is_rate_limited(endpoint):
            print("Warning: Rate limit reached for Binance API.")
            return None
        
        # Binance uses symbol format like "BTCUSDT"
        symbol = f"{ticker.upper()}USDT"
        source_query = f"GET {endpoint}?symbol={symbol}"
        
        try:
            response = requests.get(
                endpoint,
                params={"symbol": symbol},
                timeout=10
            )
            
            if response.status_code == 429:
                print("Warning: Binance rate limit exceeded.")
                return None
            
            if response.status_code >= 400:
                print(f"Warning: Binance API error {response.status_code}: {response.text[:200]}")
                return None
            
            data = response.json()
            
            # Extract funding rate (8h funding rate, convert to daily)
            funding_rate = float(data.get("lastFundingRate", 0))
            
            # Get 24h ticker stats for price/volume
            stats_endpoint = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            stats_response = requests.get(
                stats_endpoint,
                params={"symbol": symbol},
                timeout=10
            )
            
            price_change_24h = None
            volume_24h = None
            price = None
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                price = float(stats_data.get("lastPrice", 0))
                price_change_24h = float(stats_data.get("priceChangePercent", 0))
                volume_24h = float(stats_data.get("volume", 0))
            
            result = PerpMarketData(
                ticker=ticker.upper(),
                funding_rate=funding_rate,
                price=price,
                price_change_24h=price_change_24h,
                volume_24h=volume_24h,
                volume_ratio=1.0,  # Would need historical data to calculate
                source_query=source_query
            )
            
            # Cache the result
            if use_cache:
                cache_key = _get_cache_key(ticker)
                _cache_result(cache_key, result)
            
            return result
        
        except requests.exceptions.Timeout:
            print("Warning: Binance API request timed out.")
            return None
        except requests.exceptions.ConnectionError:
            print("Warning: Could not connect to Binance API.")
            return None
        except (ValueError, KeyError, TypeError) as e:
            print(f"Warning: Failed to parse Binance response: {str(e)[:200]}")
            return None
        except Exception as e:
            print(f"Warning: Binance API request failed: {str(e)[:200]}")
            return None
    
    except Exception as e:
        print(f"Warning: Unexpected error fetching Binance data: {str(e)[:200]}")
        return None


def clear_cache() -> None:
    """Clear all cached results."""
    global _cache
    _cache.clear()


# Usage example
if __name__ == "__main__":
    # Example: Get BTC perpetual market data
    btc_data = get_perp_market_data("BTC")
    if btc_data:
        print(f"\nBTC Perpetual Market Data:")
        print(f"Funding Rate: {btc_data.funding_rate*100:.4f}% (daily)")
        if btc_data.price:
            print(f"Price: ${btc_data.price:,.2f}")
        if btc_data.price_change_24h:
            print(f"24h Change: {btc_data.price_change_24h:+.2f}%")
        print(f"Source: {btc_data.source_query}")

