import os
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, replace
from typing import List, Optional, Dict, Any, Tuple, TypeVar
from collections import defaultdict
import requests  # pyright: ignore[reportMissingModuleSource]

# Create a session for connection pooling and better performance
_session: Optional[requests.Session] = None

def _get_session() -> requests.Session:
    """Get or create a requests session for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Set default headers
        _session.headers.update({
            'User-Agent': 'ElfaTools/1.0 (Python)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
    return _session

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
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

# Type variable for generic cache functions
T = TypeVar('T')


@dataclass
class AccountInfo:
    """Account information with type classification."""
    username: str
    account_type: Optional[str] = None  # "smart", "ct", "news", or None
    platform: Optional[str] = None  # "twitter", "telegram", or None


@dataclass
class TickerNarrativeSnapshot:
    """Snapshot of ticker narrative data including mentions and mindshare."""
    ticker: str
    window: str
    total_mentions: int
    mindshare_score: Optional[float]
    top_smart_accounts: List[str]
    source_query: str = field(default="")  # For audit trail - the exact API query made
    # New fields from enhancements
    sentiment_score: Optional[float] = None  # -1 to +1, bullish/bearish
    account_details: List[AccountInfo] = field(default_factory=list)  # Account info with types
    platform: Optional[str] = None  # "twitter", "telegram", or None (for cross-platform)
    news_mentions: int = 0  # Mentions from news accounts
    organic_mentions: int = 0  # Mentions excluding news


def _get_cache_key(ticker: str, window: str, source: Optional[str] = None) -> str:
    """Generate a cache key for the given ticker, window, and optional source."""
    key = f"ticker:{ticker.upper()}:window:{window}"
    if source:
        key += f":source:{source.lower()}"
    return key


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


def _get_cached_result(cache_key: str) -> Optional[Any]:
    """Get a cached result if it exists and hasn't expired.
    
    Returns:
        Cached result of any type, or None if not found or expired.
    """
    global _cache
    if cache_key in _cache:
        result, expiry_time = _cache[cache_key]
        if time.time() < expiry_time:
            return result
        else:
            # Expired, remove from cache
            del _cache[cache_key]
    return None


def _cache_result(cache_key: str, result: Any, ttl: int = None) -> None:
    """Cache a result with the given TTL.
    
    Args:
        cache_key: Unique key for the cache entry
        result: Result of any type to cache
        ttl: Time to live in seconds (defaults to _cache_ttl)
    """
    global _cache, _cache_ttl
    if ttl is None:
        ttl = _cache_ttl
    expiry_time = time.time() + ttl
    _cache[cache_key] = (result, expiry_time)


def _make_api_request(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    timeout: int = 15
) -> Optional[requests.Response]:
    """
    Make an API request with automatic retry logic for transient errors.
    
    Args:
        url: Request URL
        headers: Request headers
        params: Query parameters
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (exponential backoff)
        timeout: Request timeout in seconds
    
    Returns:
        Response object or None if all retries failed
    """
    session = _get_session()
    
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, params=params, timeout=timeout)
            
            # If successful or non-retryable error, return immediately
            if response.status_code == 200:
                return response
            elif response.status_code in [401, 404]:
                # Don't retry auth or not found errors
                return response
            elif response.status_code == 500 and attempt < max_retries - 1:
                # Retry 500 errors with exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                print(f"Warning: Server error (500) on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 429 and attempt < max_retries - 1:
                # Retry rate limit errors
                retry_after = int(response.headers.get("Retry-After", 60))
                wait_time = min(retry_after, retry_delay * (2 ** attempt))
                print(f"Warning: Rate limited (429) on attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # Other errors or final attempt
                return response
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Warning: Connection error on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Warning: Connection failed after {max_retries} attempts: {str(e)[:200]}")
                return None
        except Exception as e:
            print(f"Warning: Unexpected error during API request: {str(e)[:200]}")
            return None
    
    return None


def get_ticker_narrative_snapshot(
    ticker: str,
    window: str = "1h",
    use_cache: bool = True,
    source: Optional[str] = None
) -> Optional[TickerNarrativeSnapshot]:

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
            cache_key = _get_cache_key(ticker, window, source)
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

        # Validate inputs to prevent server-side errors
        ticker = str(ticker).strip().upper()
        if not ticker or len(ticker) > 20:
            print(f"Warning: Invalid ticker format: {ticker}")
            return None
        
        # Validate window format
        valid_windows = ["1h", "4h", "24h", "1d", "7d"]
        if window not in valid_windows:
            print(f"Warning: Invalid window format: {window}. Using '1h' as fallback.")
            window = "1h"
        
        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "ElfaTools/1.0 (Python)"
        }

        url = f"{base_url}{endpoint}"
        params = {
            "ticker": ticker,
            "timeWindow": window,
            "page": 0,
            "pageSize": 10,
        }
        
        # Add source parameter if specified (for platform filtering)
        normalized_source = None
        if source:
            normalized_source = str(source).strip().lower()
            params["source"] = normalized_source

        # Build source_query for audit trail (use normalized source to match what's actually sent)
        source_query = f"GET {url}?ticker={ticker}&timeWindow={window}&page=0&pageSize=10"
        if normalized_source:
            source_query += f"&source={normalized_source}"

        # Use the retry-enabled request helper
        response = _make_api_request(url, headers, params, max_retries=3, retry_delay=2.0, timeout=15)
        
        if response is None:
            return None

        # Handle rate limiting (429)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            # Update rate limit tracker
            _rate_limit_tracker[endpoint].clear()  # Reset to force wait
            return None

        # Handle other HTTP errors
        if response.status_code == 401:
            print("Warning: API authentication failed (401). Check your API key.")
            print(f"      Request: {source_query}")
            return None

        if response.status_code == 404:
            print(f"Warning: API endpoint not found (404) for ticker {ticker}.")
            print(f"      Request: {source_query}")
            return None

        if response.status_code >= 400:
            error_msg = f"Warning: API returned error {response.status_code}"
            try:
                # Try to parse JSON error response
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict):
                        error_detail = error_json.get('error', error_json.get('message', error_json.get('detail', '')))
                        if error_detail:
                            error_msg += f": {error_detail}"
                except:
                    # Fall back to text
                    error_body = response.text[:500]  # Increased from 200
                    if error_body:
                        error_msg += f": {error_body}"
            except:
                pass
            
            print(error_msg)
            print(f"      Request URL: {url}")
            print(f"      Request params: {params}")
            print(f"      Response headers: {dict(response.headers)}")
            
            # For 500 errors, provide helpful context and suggestions
            if response.status_code == 500:
                print("\nNote: This is a server-side error from Elfa's API.")
                print("      Troubleshooting steps:")
                print("      1. Verify your API key is valid and has proper permissions")
                print("      2. Check if the ticker symbol is correct and supported")
                print("      3. Try a different time window (1h, 4h, 24h)")
                print("      4. Wait a few minutes and retry (may be temporary server issue)")
                print("      5. Check Elfa API status page if available")
                print(f"      6. Request details: {source_query}")
            
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
        
        # Extract sentiment score (if available)
        sentiment_score = ticker_data.get("sentiment_score") or ticker_data.get("sentiment")
        if sentiment_score is not None:
            try:
                sentiment_score = float(sentiment_score)
            except (ValueError, TypeError):
                sentiment_score = None
        
        top_smart_accounts = []
        account_details = []
        news_mentions = 0
        organic_mentions = int(total_mentions) if total_mentions else 0

        accounts_data = (
            ticker_data.get("top_smart_accounts") or
            ticker_data.get("smart_accounts") or
            ticker_data.get("accounts") or
            ticker_data.get("top_accounts") or
            []
        )

        if isinstance(accounts_data, list):
            for account in accounts_data[:10]:  # Extract more accounts for type analysis
                if isinstance(account, dict):
                    username = (
                        account.get("username") or
                        account.get("handle") or
                        account.get("account") or
                        account.get("name") or
                        str(account.get("id", ""))
                    )
                    if username:
                        # Extract account type if available
                        account_type = account.get("type") or account.get("account_type")
                        if account_type:
                            account_type = str(account_type).lower()
                            if account_type not in ["smart", "ct", "news"]:
                                account_type = None
                        
                        # Count news accounts
                        if account_type == "news":
                            news_mentions += 1
                        
                        account_info = AccountInfo(
                            username=username,
                            account_type=account_type,
                            platform=None  # Will be set if source filtering is used
                        )
                        account_details.append(account_info)
                        
                        # Keep top 3 for backward compatibility
                        if len(top_smart_accounts) < 3:
                            top_smart_accounts.append(username)
                elif isinstance(account, str):
                    top_smart_accounts.append(account)
                    account_details.append(AccountInfo(username=account))

        # Calculate organic mentions (excluding news)
        if news_mentions > 0:
            organic_mentions = max(0, organic_mentions - news_mentions)

        result = TickerNarrativeSnapshot(
            ticker=ticker,
            window=window,
            total_mentions=int(total_mentions) if total_mentions else 0,
            mindshare_score=float(mindshare_score) if mindshare_score is not None else None,
            top_smart_accounts=top_smart_accounts[:3],
            source_query=source_query,
            sentiment_score=sentiment_score,
            account_details=account_details,
            platform=source,  # Set platform from source parameter
            news_mentions=news_mentions,
            organic_mentions=organic_mentions
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


# ============================================================================
# NEW ENDPOINTS: Contract Addresses, Trending Tokens, Events, Multi-Keyword
# ============================================================================

@dataclass
class ContractAddressData:
    """Data for a trending contract address."""
    address: str
    mentions: int
    platform: str  # "twitter" or "telegram"
    top_accounts: List[str]
    timestamp: Optional[datetime] = None
    source_query: str = ""


@dataclass
class TrendingToken:
    """Data for a trending token."""
    ticker: str
    mentions: int
    mindshare_score: Optional[float]
    sentiment_score: Optional[float]
    smart_accounts: List[str]
    source_query: str = ""


@dataclass
class EventSummary:
    """Event summary from keyword mentions."""
    event_id: str
    keywords: List[str]
    mentions: int
    description: Optional[str]
    top_accounts: List[str]
    timestamp: Optional[datetime] = None
    source_query: str = ""


def get_trending_contracts(
    platform: str = "twitter",
    window: str = "1h",
    limit: int = 20,
    use_cache: bool = True
) -> Optional[List[ContractAddressData]]:
    """
    Get trending contract addresses on Twitter or Telegram.
    
    Args:
        platform: "twitter" or "telegram"
        window: Time window ("1h", "4h", "24h")
        limit: Maximum number of results
        use_cache: Whether to use cached results
        
    Returns:
        List of ContractAddressData, or None if unavailable
    """
    try:
        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")
        
        if not api_key:
            return None
        
        # Try different possible endpoint formats
        endpoint = f"/v2/data/contracts/{platform}"
        cache_key = f"contracts:{platform}:{window}:{limit}"
        
        if use_cache:
            cached = _get_cached_result(cache_key)
            if cached is not None:
                return cached
        
        if _is_rate_limited(endpoint):
            return None
        
        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}{endpoint}"
        params = {
            "timeWindow": window,
            "limit": limit
        }
        
        source_query = f"GET {url}?platform={platform}&timeWindow={window}&limit={limit}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                # Endpoint might not exist yet, return None gracefully
                return None
            
            data = response.json()
            results = data.get("results", []) or data.get("data", [])
            
            contracts = []
            for item in results:
                address = item.get("address") or item.get("contract_address")
                if not address:
                    continue
                
                mentions = item.get("mentions") or item.get("count") or 0
                accounts_data = item.get("top_accounts") or item.get("accounts") or []
                top_accounts = []
                
                for acc in accounts_data[:5]:
                    if isinstance(acc, dict):
                        username = acc.get("username") or acc.get("handle") or str(acc.get("id", ""))
                    else:
                        username = str(acc)
                    if username:
                        top_accounts.append(username)
                
                contracts.append(ContractAddressData(
                    address=address,
                    mentions=int(mentions),
                    platform=platform,
                    top_accounts=top_accounts,
                    source_query=source_query
                ))
            
            if use_cache:
                _cache_result(cache_key, contracts)
            
            return contracts
            
        except Exception:
            # Endpoint might not exist, fail gracefully
            return None
            
    except Exception:
        return None


def get_trending_tokens(
    window: str = "1h",
    limit: int = 20,
    use_cache: bool = True
) -> Optional[List[TrendingToken]]:
    """
    Get trending tokens leaderboard.
    
    Args:
        window: Time window ("1h", "4h", "24h")
        limit: Maximum number of results
        use_cache: Whether to use cached results
        
    Returns:
        List of TrendingToken, or None if unavailable
    """
    try:
        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")
        
        if not api_key:
            return None
        
        # Try different possible endpoint formats
        endpoint = "/v2/data/trending"
        cache_key = f"trending:{window}:{limit}"
        
        if use_cache:
            cached = _get_cached_result(cache_key)
            if cached is not None:
                return cached
        
        if _is_rate_limited(endpoint):
            return None
        
        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}{endpoint}"
        params = {
            "timeWindow": window,
            "limit": limit
        }
        
        source_query = f"GET {url}?timeWindow={window}&limit={limit}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                # Endpoint might not exist yet, return None gracefully
                return None
            
            data = response.json()
            results = data.get("results", []) or data.get("data", [])
            
            tokens = []
            for item in results:
                ticker = item.get("ticker") or item.get("symbol")
                if not ticker:
                    continue
                
                mentions = item.get("mentions") or item.get("total_mentions") or 0
                mindshare = item.get("mindshare_score") or item.get("mindshare")
                sentiment = item.get("sentiment_score") or item.get("sentiment")
                
                accounts_data = item.get("top_smart_accounts") or item.get("smart_accounts") or []
                smart_accounts = []
                for acc in accounts_data[:5]:
                    if isinstance(acc, dict):
                        username = acc.get("username") or acc.get("handle") or str(acc.get("id", ""))
                    else:
                        username = str(acc)
                    if username:
                        smart_accounts.append(username)
                
                tokens.append(TrendingToken(
                    ticker=str(ticker),
                    mentions=int(mentions),
                    mindshare_score=float(mindshare) if mindshare is not None else None,
                    sentiment_score=float(sentiment) if sentiment is not None else None,
                    smart_accounts=smart_accounts,
                    source_query=source_query
                ))
            
            if use_cache:
                _cache_result(cache_key, tokens)
            
            return tokens
            
        except Exception:
            # Endpoint might not exist, fail gracefully
            return None
            
    except Exception:
        return None


def get_event_summary(
    keywords: List[str],
    window: str = "24h",
    use_cache: bool = True
) -> Optional[List[EventSummary]]:
    """
    Get event summaries from keyword mentions.
    
    Args:
        keywords: List of keywords to search for
        window: Time window ("1h", "4h", "24h")
        use_cache: Whether to use cached results
        
    Returns:
        List of EventSummary, or None if unavailable
    """
    try:
        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")
        
        if not api_key:
            return None
        
        endpoint = "/v2/data/events"
        cache_key = f"events:{':'.join(sorted(keywords))}:{window}"
        
        if use_cache:
            cached = _get_cached_result(cache_key)
            if cached is not None:
                return cached
        
        if _is_rate_limited(endpoint):
            return None
        
        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}{endpoint}"
        params = {
            "keywords": ",".join(keywords),
            "timeWindow": window
        }
        
        source_query = f"GET {url}?keywords={','.join(keywords)}&timeWindow={window}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                # Endpoint might not exist yet, return None gracefully
                return None
            
            data = response.json()
            results = data.get("results", []) or data.get("data", [])
            
            events = []
            for item in results:
                event_id = item.get("id") or item.get("event_id") or str(len(events))
                event_keywords = item.get("keywords") or keywords
                mentions = item.get("mentions") or item.get("count") or 0
                description = item.get("description") or item.get("summary")
                
                accounts_data = item.get("top_accounts") or item.get("accounts") or []
                top_accounts = []
                for acc in accounts_data[:5]:
                    if isinstance(acc, dict):
                        username = acc.get("username") or acc.get("handle") or str(acc.get("id", ""))
                    else:
                        username = str(acc)
                    if username:
                        top_accounts.append(username)
                
                events.append(EventSummary(
                    event_id=str(event_id),
                    keywords=event_keywords if isinstance(event_keywords, list) else [str(k) for k in event_keywords],
                    mentions=int(mentions),
                    description=str(description) if description else None,
                    top_accounts=top_accounts,
                    source_query=source_query
                ))
            
            if use_cache:
                _cache_result(cache_key, events)
            
            return events
            
        except Exception:
            # Endpoint might not exist, fail gracefully
            return None
            
    except Exception:
        return None


def get_multi_keyword_mentions(
    keywords: List[str],
    window: str = "24h",
    use_cache: bool = True
) -> Optional[Dict[str, TickerNarrativeSnapshot]]:
    """
    Get mentions for multiple keywords/tickers in one query.
    
    Args:
        keywords: List of ticker symbols or keywords
        window: Time window ("1h", "4h", "24h")
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary mapping keyword to TickerNarrativeSnapshot, or None if unavailable
    """
    try:
        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")
        
        if not api_key:
            return None
        
        endpoint = "/v2/data/mentions"
        cache_key = f"multi:{':'.join(sorted(keywords))}:{window}"
        
        if use_cache:
            cached = _get_cached_result(cache_key)
            if cached is not None:
                return cached
        
        if _is_rate_limited(endpoint):
            return None
        
        headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{base_url}{endpoint}"
        params = {
            "keywords": ",".join(keywords),
            "timeWindow": window
        }
        
        source_query = f"GET {url}?keywords={','.join(keywords)}&timeWindow={window}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                # Fallback: query each keyword individually
                results = {}
                for keyword in keywords:
                    snapshot = get_ticker_narrative_snapshot(keyword, window, use_cache)
                    if snapshot:
                        results[keyword] = snapshot
                return results if results else None
            
            data = response.json()
            results_data = data.get("results", []) or data.get("data", [])
            
            results = {}
            for item in results_data:
                ticker = item.get("ticker") or item.get("keyword")
                if not ticker:
                    continue
                
                # Reuse existing parsing logic
                total_mentions = item.get("total_mentions") or item.get("mentions") or 0
                mindshare_score = item.get("mindshare_score") or item.get("mindshare")
                sentiment_score = item.get("sentiment_score") or item.get("sentiment")
                
                accounts_data = item.get("top_smart_accounts") or item.get("smart_accounts") or []
                top_smart_accounts = []
                account_details = []
                
                for acc in accounts_data[:10]:
                    if isinstance(acc, dict):
                        username = acc.get("username") or acc.get("handle") or str(acc.get("id", ""))
                        account_type = acc.get("type") or acc.get("account_type")
                    else:
                        username = str(acc)
                        account_type = None
                    
                    if username:
                        top_smart_accounts.append(username)
                        account_details.append(AccountInfo(
                            username=username,
                            account_type=account_type
                        ))
                
                results[ticker] = TickerNarrativeSnapshot(
                    ticker=str(ticker),
                    window=window,
                    total_mentions=int(total_mentions),
                    mindshare_score=float(mindshare_score) if mindshare_score is not None else None,
                    top_smart_accounts=top_smart_accounts[:3],
                    source_query=source_query,
                    sentiment_score=float(sentiment_score) if sentiment_score is not None else None,
                    account_details=account_details
                )
            
            if use_cache:
                _cache_result(cache_key, results)
            
            return results if results else None
            
        except Exception as e:
            # Fallback to individual queries
            results = {}
            for keyword in keywords:
                snapshot = get_ticker_narrative_snapshot(keyword, window, use_cache)
                if snapshot:
                    results[keyword] = snapshot
            return results if results else None
            
    except Exception:
        return None


# ============================================================================
# CROSS-PLATFORM ANALYSIS
# ============================================================================

def get_cross_platform_snapshot(
    ticker: str,
    window: str = "1h",
    use_cache: bool = True
) -> Optional[Dict[str, TickerNarrativeSnapshot]]:
    """
    Get narrative data for a ticker from both Twitter and Telegram.
    
    Args:
        ticker: Ticker symbol
        window: Time window
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with "twitter" and "telegram" keys, or None if unavailable
    """
    results = {}
    
    # Try to get Twitter data (default)
    twitter_snap = get_ticker_narrative_snapshot(ticker, window, use_cache)
    if twitter_snap:
        # Create a copy to avoid mutating the cached object
        twitter_snap = replace(twitter_snap, platform="twitter")
        results["twitter"] = twitter_snap
    
    # Try to get Telegram data (might need source parameter)
    # For now, we'll try the same endpoint with a source parameter
    try:
        base_url = "https://api.elfa.ai"
        api_key = os.getenv("ELFA_API_KEY")
        
        if api_key:
            endpoint = "/v2/data/top-mentions"
            if not _is_rate_limited(endpoint):
                headers = {
                    "x-elfa-api-key": api_key,
                    "Content-Type": "application/json"
                }
                url = f"{base_url}{endpoint}"
                params = {
                    "ticker": ticker,
                    "timeWindow": window,
                    "source": "telegram"  # Try source parameter
                }
                
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        results_data = data.get("results", [])
                        for entry in results_data:
                            if str(entry.get("ticker", "")).upper() == ticker.upper():
                                # Parse similar to main function
                                total_mentions = entry.get("total_mentions") or 0
                                mindshare_score = entry.get("mindshare_score")
                                accounts_data = entry.get("top_smart_accounts") or []
                                top_smart_accounts = [acc.get("username", "") if isinstance(acc, dict) else str(acc) for acc in accounts_data[:3]]
                                
                                telegram_snap = TickerNarrativeSnapshot(
                                    ticker=ticker,
                                    window=window,
                                    total_mentions=int(total_mentions),
                                    mindshare_score=float(mindshare_score) if mindshare_score else None,
                                    top_smart_accounts=top_smart_accounts,
                                    source_query=f"GET {url}?ticker={ticker}&timeWindow={window}&source=telegram",
                                    platform="telegram"
                                )
                                results["telegram"] = telegram_snap
                                break
                except Exception:
                    pass
    except Exception:
        pass
    
    return results if results else None


def calculate_platform_divergence(
    ticker: str,
    window: str = "1h",
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Calculate divergence between Twitter and Telegram narratives.
    
    Returns metrics showing which platform is leading and by how much.
    
    Args:
        ticker: Ticker symbol
        window: Time window
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with divergence metrics, or None if unavailable
    """
    platforms = get_cross_platform_snapshot(ticker, window, use_cache)
    
    if not platforms or len(platforms) < 2:
        return None
    
    twitter = platforms.get("twitter")
    telegram = platforms.get("telegram")
    
    if not twitter or not telegram:
        return None
    
    twitter_mentions = twitter.total_mentions
    telegram_mentions = telegram.total_mentions
    
    divergence = {
        "ticker": ticker,
        "window": window,
        "twitter_mentions": twitter_mentions,
        "telegram_mentions": telegram_mentions,
        "mention_delta": telegram_mentions - twitter_mentions,
        "leading_platform": "telegram" if telegram_mentions > twitter_mentions else "twitter",
        "divergence_ratio": telegram_mentions / twitter_mentions if twitter_mentions > 0 else float('inf'),
        "early_signal": telegram_mentions > twitter_mentions * 1.2,  # Telegram 20%+ higher
        "twitter_snapshot": twitter,
        "telegram_snapshot": telegram
    }
    
    return divergence


# ============================================================================
# ACCOUNT-TYPE WEIGHTING
# ============================================================================

def calculate_weighted_mentions(
    snapshot: TickerNarrativeSnapshot,
    smart_weight: float = 3.0,
    ct_weight: float = 1.0,
    news_weight: float = 0.5
) -> Dict[str, Any]:
    """
    Calculate weighted mentions based on account types.
    
    Smart accounts are weighted higher than CT accounts, which are weighted
    higher than news accounts.
    
    Args:
        snapshot: TickerNarrativeSnapshot with account_details
        smart_weight: Weight for smart accounts (default: 3.0)
        ct_weight: Weight for CT accounts (default: 1.0)
        news_weight: Weight for news accounts (default: 0.5)
        
    Returns:
        Dictionary with weighted metrics
    """
    if not snapshot.account_details:
        return {
            "weighted_mentions": snapshot.total_mentions,
            "smart_account_mentions": 0,
            "ct_account_mentions": 0,
            "news_account_mentions": 0,
            "organic_weighted_mentions": snapshot.total_mentions
        }
    
    smart_count = sum(1 for acc in snapshot.account_details if acc.account_type == "smart")
    ct_count = sum(1 for acc in snapshot.account_details if acc.account_type == "ct")
    news_count = sum(1 for acc in snapshot.account_details if acc.account_type == "news")
    
    weighted_mentions = (
        smart_count * smart_weight +
        ct_count * ct_weight +
        news_count * news_weight
    )
    
    # Organic mentions (excluding news)
    organic_weighted = (
        smart_count * smart_weight +
        ct_count * ct_weight
    )
    
    return {
        "weighted_mentions": weighted_mentions,
        "smart_account_mentions": smart_count,
        "ct_account_mentions": ct_count,
        "news_account_mentions": news_count,
        "organic_weighted_mentions": organic_weighted,
        "weight_ratio": weighted_mentions / snapshot.total_mentions if snapshot.total_mentions > 0 else 0
    }


# ============================================================================
# EVENT-DRIVEN FILTERING
# ============================================================================

def is_organic_narrative_spike(
    ticker: str,
    window: str = "1h",
    min_mentions: int = 20,
    max_event_mentions: int = 100,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Determine if a narrative spike is organic (not news-driven).
    
    Args:
        ticker: Ticker symbol
        window: Time window
        min_mentions: Minimum mentions to consider it a spike
        max_event_mentions: Maximum event mentions to still consider organic
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with analysis results
    """
    snapshot = get_ticker_narrative_snapshot(ticker, window, use_cache)
    if not snapshot:
        return {
            "is_organic": False,
            "reason": "No data available",
            "total_mentions": 0,
            "news_mentions": 0,
            "event_mentions": 0
        }
    
    # Check for events related to this ticker
    events = get_event_summary([ticker], window, use_cache)
    event_mentions = sum(e.mentions for e in events) if events else 0
    
    # Calculate organic score
    news_ratio = snapshot.news_mentions / snapshot.total_mentions if snapshot.total_mentions > 0 else 0
    event_ratio = event_mentions / snapshot.total_mentions if snapshot.total_mentions > 0 else 0
    
    is_organic = (
        snapshot.total_mentions >= min_mentions and
        snapshot.news_mentions <= max_event_mentions and
        event_mentions <= max_event_mentions and
        news_ratio < 0.3 and  # Less than 30% news-driven
        event_ratio < 0.3  # Less than 30% event-driven
    )
    
    return {
        "is_organic": is_organic,
        "total_mentions": snapshot.total_mentions,
        "news_mentions": snapshot.news_mentions,
        "organic_mentions": snapshot.organic_mentions,
        "event_mentions": event_mentions,
        "news_ratio": news_ratio,
        "event_ratio": event_ratio,
        "reason": "Organic spike" if is_organic else f"News/event-driven (news: {news_ratio:.1%}, events: {event_ratio:.1%})",
        "snapshot": snapshot,
        "events": events
    }

