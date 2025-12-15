import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import requests  # pyright: ignore[reportMissingModuleSource]

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


# Global state for rate limiting and caching
_rate_limit_tracker: Dict[str, List[float]] = defaultdict(list)  # endpoint -> list of request timestamps
_cache: Dict[str, Tuple[Any, float]] = {}  # cache_key -> (result, expiry_time)
_cache_ttl = 300  # 5 minutes default cache TTL


@dataclass
class TickerNarrativeSnapshot:
    """Snapshot of ticker narrative data including mentions and mindshare."""
    ticker: str
    window: str
    total_mentions: int
    mindshare_score: Optional[float]
    top_smart_accounts: List[str]
    source_query: str = field(default="")  # For audit trail - the exact API query made


def _get_cache_key(ticker: str, window: str) -> str:
    """Generate a cache key for the given ticker and window."""
    return f"ticker:{ticker.upper()}:window:{window}"


def _is_rate_limited(endpoint: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
    """
    Check if we're rate limited for the given endpoint.
    
    Args:
        endpoint: The API endpoint being called
        max_requests: Maximum requests allowed in the time window
        window_seconds: Time window in seconds
    
    Returns:
        True if rate limited, False otherwise
    """
    global _rate_limit_tracker
    now = time.time()
    
    # Clean old entries outside the window
    _rate_limit_tracker[endpoint] = [
        ts for ts in _rate_limit_tracker[endpoint]
        if now - ts < window_seconds
    ]
    
    # Check if we've exceeded the limit
    if len(_rate_limit_tracker[endpoint]) >= max_requests:
        return True
    
    # Record this request
    _rate_limit_tracker[endpoint].append(now)
    return False


def _get_cached_result(cache_key: str) -> Optional[TickerNarrativeSnapshot]:
    """Get a cached result if it exists and hasn't expired."""
    global _cache
    if cache_key in _cache:
        result, expiry_time = _cache[cache_key]
        if time.time() < expiry_time:
            return result
        else:
            # Expired, remove from cache
            del _cache[cache_key]
    return None


def _cache_result(cache_key: str, result: TickerNarrativeSnapshot, ttl: int = None) -> None:
    """Cache a result with the given TTL."""
    global _cache, _cache_ttl
    if ttl is None:
        ttl = _cache_ttl
    expiry_time = time.time() + ttl
    _cache[cache_key] = (result, expiry_time)


def get_ticker_narrative_snapshot(ticker: str, window: str = "1h", use_cache: bool = True) -> Optional[TickerNarrativeSnapshot]:

    """
    Get mentions and mindshare data for a ticker over the given time window using the Elfa V2 API.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        window: Time window for aggregation (default: "1h")
        use_cache: Whether to use cached results (default: True)

    Returns:
        TickerNarrativeSnapshot with ticker data, or None if API is unavailable.
        Never raises exceptions - all errors are handled gracefully.
    """
    try:
        # Check cache first
        if use_cache:
            cache_key = _get_cache_key(ticker, window)
            cached_result = _get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")

        if not api_key:
            print("Warning: ELFA_API_KEY environment variable is not set.")
            return None

        endpoint = "/v2/data/top-mentions"
        
        # Check rate limiting before making the request
        if _is_rate_limited(endpoint):
            print("Warning: Rate limit reached. Please wait before making more requests.")
            return None

        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json"
        }

        url = f"{base_url}{endpoint}"
        params = {
            "ticker": ticker,
            "timeWindow": window,
            "page": 0,
            "pageSize": 10,
        }

        # Build source_query for audit trail
        source_query = f"GET {url}?ticker={ticker}&timeWindow={window}&page=0&pageSize=10"

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                # Update rate limit tracker
                _rate_limit_tracker[endpoint].clear()  # Reset to force wait
                return None

            # Handle other HTTP errors
            if response.status_code == 401:
                print("Warning: API authentication failed (401). Check your API key.")
                return None

            if response.status_code == 404:
                print(f"Warning: API endpoint not found (404) for ticker {ticker}.")
                return None

            if response.status_code >= 400:
                error_msg = f"Warning: API returned error {response.status_code}"
                try:
                    error_body = response.text[:200]
                    if error_body:
                        error_msg += f": {error_body}"
                except:
                    pass
                print(error_msg)
                return None

            # Parse response
            try:
                data = response.json()
            except (ValueError, TypeError) as e:
                print(f"Warning: Failed to parse JSON response: {str(e)[:200]}")
                return None

            # The response is expected to be a dict with a "results" field containing narratives for tickers.
            # We try to find the entry matching the requested ticker (in case of case mismatch or symbol format).
            results = data.get("results", [])
            ticker_data = None
            for entry in results:
                if (
                    isinstance(entry, dict)
                    and str(entry.get("ticker", "")).upper() == ticker.upper()
                ):
                    ticker_data = entry
                    break

            # Only return data if exact ticker match found (no fallback to avoid wrong data)
            if ticker_data is None:
                print(f"Warning: No narrative data found for ticker {ticker}.")
                return None

            total_mentions = ticker_data.get("total_mentions") or ticker_data.get("mentions") or ticker_data.get("count") or 0
            mindshare_score = ticker_data.get("mindshare_score") or ticker_data.get("mindshare") or ticker_data.get("score")
            top_smart_accounts = []

            accounts_data = (
                ticker_data.get("top_smart_accounts") or
                ticker_data.get("smart_accounts") or
                ticker_data.get("accounts") or
                ticker_data.get("top_accounts") or
                []
            )

            if isinstance(accounts_data, list):
                for account in accounts_data[:3]:
                    if isinstance(account, dict):
                        username = (
                            account.get("username") or
                            account.get("handle") or
                            account.get("account") or
                            account.get("name") or
                            str(account.get("id", ""))
                        )
                        if username:
                            top_smart_accounts.append(username)
                    elif isinstance(account, str):
                        top_smart_accounts.append(account)

            result = TickerNarrativeSnapshot(
                ticker=ticker,
                window=window,
                total_mentions=int(total_mentions) if total_mentions else 0,
                mindshare_score=float(mindshare_score) if mindshare_score is not None else None,
                top_smart_accounts=top_smart_accounts[:3],
                source_query=source_query
            )

            # Cache the result
            if use_cache:
                _cache_result(cache_key, result)

            return result

        except requests.exceptions.Timeout:
            print("Warning: API request timed out.")
            return None
        except requests.exceptions.ConnectionError:
            print("Warning: Could not connect to Elfa API. Check your internet connection.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Warning: API request failed: {str(e)[:200]}")
            return None
        except Exception as e:
            # Catch-all for any unexpected errors - never crash
            print(f"Warning: Unexpected error occurred: {str(e)[:200]}")
            return None

    except Exception as e:
        # Ultimate safety net - catch absolutely everything
        print(f"Warning: Unexpected error in get_ticker_narrative_snapshot: {str(e)[:200]}")
        return None


def get_rate_limit_stats(endpoint: str = "/v2/data/top-mentions", window_seconds: int = 60) -> Dict[str, Any]:
    """
    Get rate limit statistics for the given endpoint.
    
    Args:
        endpoint: The API endpoint to check
        window_seconds: Time window in seconds
    
    Returns:
        Dictionary with rate limit statistics
    """
    global _rate_limit_tracker
    now = time.time()
    
    # Clean old entries
    _rate_limit_tracker[endpoint] = [
        ts for ts in _rate_limit_tracker[endpoint]
        if now - ts < window_seconds
    ]
    
    requests_in_window = len(_rate_limit_tracker[endpoint])
    oldest_request = min(_rate_limit_tracker[endpoint]) if _rate_limit_tracker[endpoint] else None
    time_until_reset = (oldest_request + window_seconds - now) if oldest_request else 0
    
    return {
        "endpoint": endpoint,
        "requests_in_window": requests_in_window,
        "window_seconds": window_seconds,
        "time_until_reset": max(0, time_until_reset) if time_until_reset else 0,
        "is_rate_limited": requests_in_window >= 60  # Default max_requests
    }


def clear_cache() -> None:
    """Clear all cached results."""
    global _cache
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the cache."""
    global _cache
    now = time.time()
    valid_entries = sum(1 for _, expiry in _cache.values() if now < expiry)
    expired_entries = len(_cache) - valid_entries
    
    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "cache_ttl_seconds": _cache_ttl
    }

