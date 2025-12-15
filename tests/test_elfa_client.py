"""
Tests for elfa_client.py

Tests cover:
- Successful API calls and response parsing
- Cache behavior (hits, misses, expiration)
- Rate limiting
- Error handling (all error scenarios)
- Edge cases
"""
import pytest
import time
from unittest.mock import patch, Mock
from datetime import datetime

from elfa_client import (
    get_ticker_narrative_snapshot,
    TickerNarrativeSnapshot,
    get_rate_limit_stats,
    get_cache_stats,
    clear_cache,
    _is_rate_limited,
    _get_cached_result,
    _cache_result,
    _get_cache_key,
    EventSummary
)


class TestGetTickerNarrativeSnapshot:
    """Tests for get_ticker_narrative_snapshot function."""
    
    def test_success_case(self, mock_env_elfa_api_key, mock_elfa_api_response):
        """Test successful API call and response parsing."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert isinstance(result, TickerNarrativeSnapshot)
            assert result.ticker == "BTC"
            assert result.window == "1h"
            assert result.total_mentions == 100
            assert result.mindshare_score == 0.15
            assert len(result.top_smart_accounts) == 3
            assert "account1" in result.top_smart_accounts
            assert result.source_query.startswith("GET")
    
    def test_cache_hit(self, mock_env_elfa_api_key, mock_elfa_api_response):
        """Test cache retrieval without API call."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            # First call - should make API request
            result1 = get_ticker_narrative_snapshot("BTC", "1h", use_cache=True)
            assert result1 is not None
            assert mock_get.call_count == 1
            
            # Second call - should use cache
            result2 = get_ticker_narrative_snapshot("BTC", "1h", use_cache=True)
            assert result2 is not None
            assert mock_get.call_count == 1  # No additional call
            assert result1.ticker == result2.ticker
            assert result1.total_mentions == result2.total_mentions
    
    def test_cache_miss_when_disabled(self, mock_env_elfa_api_key, mock_elfa_api_response):
        """Test that cache is bypassed when use_cache=False."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            # First call
            get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            # Second call with cache disabled
            get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            # Should make 2 API calls
            assert mock_get.call_count == 2
    
    def test_rate_limit(self, mock_env_elfa_api_key):
        """Test rate limit handling."""
        # Clear rate limit tracker
        from elfa_client import _rate_limit_tracker
        _rate_limit_tracker.clear()
        
        endpoint = "/v2/data/top-mentions"
        now = time.time()
        
        # Simulate 60 requests in the last 60 seconds
        _rate_limit_tracker[endpoint] = [now - i for i in range(60)]
        
        # 61st request should be rate limited
        result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
        assert result is None
    
    def test_ticker_not_found(self, mock_env_elfa_api_key):
        """Test handling when ticker not in response."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Response without requested ticker
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "ETH",
                        "total_mentions": 50,
                        "mindshare_score": 0.10
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            # Should return None, not first result
            assert result is None
    
    def test_api_error_401(self, mock_env_elfa_api_key):
        """Test 401 authentication error."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_api_error_404(self, mock_env_elfa_api_key):
        """Test 404 not found error."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_api_error_429(self, mock_env_elfa_api_key):
        """Test 429 rate limit error."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_response.text = "Rate limit exceeded"
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_api_error_500(self, mock_env_elfa_api_key):
        """Test 500 server error."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_timeout_error(self, mock_env_elfa_api_key):
        """Test timeout error."""
        with patch('elfa_client.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_connection_error(self, mock_env_elfa_api_key):
        """Test connection error."""
        with patch('elfa_client.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_malformed_json(self, mock_env_elfa_api_key):
        """Test malformed JSON response."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_missing_api_key(self, monkeypatch):
        """Test behavior when API key is not set."""
        monkeypatch.delenv("ELFA_API_KEY", raising=False)
        
        result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
        assert result is None
    
    def test_empty_response(self, mock_env_elfa_api_key):
        """Test empty API response."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            assert result is None
    
    def test_flexible_field_mapping(self, mock_env_elfa_api_key):
        """Test that function handles different field names."""
        # Clear cache and rate limit tracker to ensure test isolation
        from elfa_client import _cache, _rate_limit_tracker
        _cache.clear()
        _rate_limit_tracker.clear()
        
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Response with alternative field names
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "mentions": 100,  # Alternative to total_mentions
                        "mindshare": 0.15,  # Alternative to mindshare_score
                        "smart_accounts": ["account1", "account2"]  # Alternative format
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert result.total_mentions == 100
            assert result.mindshare_score == 0.15
    
    def test_new_optional_fields_sentiment(self, mock_env_elfa_api_key):
        """Test handling of new optional sentiment_score field."""
        from elfa_client import _cache, _rate_limit_tracker
        _cache.clear()
        _rate_limit_tracker.clear()
        
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "total_mentions": 100,
                        "mindshare_score": 0.15,
                        "sentiment_score": 0.75,  # New field
                        "top_smart_accounts": []
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert result.sentiment_score == 0.75
    
    def test_new_optional_fields_missing_sentiment(self, mock_env_elfa_api_key):
        """Test backward compatibility when sentiment_score is missing."""
        from elfa_client import _cache, _rate_limit_tracker
        _cache.clear()
        _rate_limit_tracker.clear()
        
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "total_mentions": 100,
                        "mindshare_score": 0.15,
                        "top_smart_accounts": []
                        # No sentiment_score - should default to None
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert result.sentiment_score is None  # Should handle missing field gracefully
    
    def test_new_optional_fields_account_details(self, mock_env_elfa_api_key):
        """Test handling of new account_details field with account types."""
        from elfa_client import AccountInfo
        from elfa_client import _cache, _rate_limit_tracker
        _cache.clear()
        _rate_limit_tracker.clear()
        
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "total_mentions": 100,
                        "mindshare_score": 0.15,
                        "top_smart_accounts": [
                            {"username": "account1", "type": "smart"},
                            {"username": "account2", "type": "ct"},
                            {"username": "account3", "type": "news"}
                        ]
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert len(result.account_details) == 3
            assert result.account_details[0].username == "account1"
            assert result.account_details[0].account_type == "smart"
            assert result.account_details[1].account_type == "ct"
            assert result.account_details[2].account_type == "news"


class TestRateLimitTracking:
    """Tests for rate limit tracking."""
    
    def test_rate_limit_tracking(self):
        """Test rate limit tracker logic."""
        from elfa_client import _rate_limit_tracker
        endpoint = "/v2/data/top-mentions"
        _rate_limit_tracker.clear()
        
        now = time.time()
        
        # Add 60 requests
        _rate_limit_tracker[endpoint] = [now - i for i in range(60)]
        
        # 61st should be rate limited
        assert _is_rate_limited(endpoint) is True
        
        # Wait 61 seconds (simulate by setting old timestamps)
        _rate_limit_tracker[endpoint] = [now - 61]
        
        # Should not be rate limited (old entries cleaned)
        assert _is_rate_limited(endpoint) is False
    
    def test_rate_limit_stats(self):
        """Test rate limit statistics."""
        from elfa_client import _rate_limit_tracker
        endpoint = "/v2/data/top-mentions"
        _rate_limit_tracker.clear()
        
        now = time.time()
        _rate_limit_tracker[endpoint] = [now - i for i in range(30)]
        
        stats = get_rate_limit_stats(endpoint)
        
        assert stats["endpoint"] == endpoint
        assert stats["requests_in_window"] == 30
        assert stats["is_rate_limited"] is False


class TestCacheBehavior:
    """Tests for caching behavior."""
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        clear_cache()
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query=""
        )
        
        cache_key = _get_cache_key("BTC", "1h")
        _cache_result(cache_key, snapshot, ttl=1)  # 1 second TTL
        
        # Should be cached immediately
        result = _get_cached_result(cache_key)
        assert result is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired
        result = _get_cached_result(cache_key)
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        clear_cache()
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query=""
        )
        
        cache_key = _get_cache_key("BTC", "1h")
        _cache_result(cache_key, snapshot, ttl=300)
        
        stats = get_cache_stats()
        
        assert stats["total_entries"] == 1
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 0
    
    def test_cache_key_format(self):
        """Test cache key generation."""
        key = _get_cache_key("BTC", "1h")
        assert key == "ticker:BTC:window:1h"
        
        key = _get_cache_key("ETH", "4h")
        assert key == "ticker:ETH:window:4h"


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_very_long_ticker_name(self, mock_env_elfa_api_key, mock_elfa_api_response):
        """Test handling of very long ticker names."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            long_ticker = "A" * 100
            result = get_ticker_narrative_snapshot(long_ticker, "1h", use_cache=False)
            # Should handle gracefully (may return None if not found)
            # But should not crash
            assert result is None or isinstance(result, TickerNarrativeSnapshot)
    
    def test_special_characters_in_ticker(self, mock_env_elfa_api_key):
        """Test handling of special characters in ticker names."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            # Should not crash with special characters
            result = get_ticker_narrative_snapshot("BTC-USD", "1h", use_cache=False)
            assert result is None  # Not found, but no crash
    
    def test_none_mindshare_score(self, mock_env_elfa_api_key):
        """Test handling when mindshare_score is None."""
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "total_mentions": 100,
                        "mindshare_score": None,
                        "top_smart_accounts": []
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            assert result is not None
            assert result.mindshare_score is None


class TestNewEnhancementFunctions:
    """Tests for new enhancement functions: weighted mentions, organic filtering, platform divergence."""
    
    def test_calculate_weighted_mentions_with_account_types(self):
        """Test weighted mentions calculation with account type information."""
        from elfa_client import TickerNarrativeSnapshot, AccountInfo, calculate_weighted_mentions
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=10,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2"],
            account_details=[
                AccountInfo(username="account1", account_type="smart"),
                AccountInfo(username="account2", account_type="smart"),
                AccountInfo(username="account3", account_type="ct"),
                AccountInfo(username="account4", account_type="ct"),
                AccountInfo(username="account5", account_type="news"),
                AccountInfo(username="account6", account_type="news"),
            ]
        )
        
        result = calculate_weighted_mentions(snapshot)
        
        assert result["smart_account_mentions"] == 2
        assert result["ct_account_mentions"] == 2
        assert result["news_account_mentions"] == 2
        # Default weights: smart=3.0, ct=1.0, news=0.5
        # Expected: 2*3.0 + 2*1.0 + 2*0.5 = 6 + 2 + 1 = 9.0
        assert result["weighted_mentions"] == 9.0
        # Organic (excluding news): 2*3.0 + 2*1.0 = 8.0
        assert result["organic_weighted_mentions"] == 8.0
        assert result["weight_ratio"] == 9.0 / 10
    
    def test_calculate_weighted_mentions_no_account_details(self):
        """Test weighted mentions calculation when account_details is empty."""
        from elfa_client import TickerNarrativeSnapshot, calculate_weighted_mentions
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            account_details=[]  # No account details
        )
        
        result = calculate_weighted_mentions(snapshot)
        
        # Should fall back to total_mentions when no account_details
        assert result["weighted_mentions"] == 100
        assert result["smart_account_mentions"] == 0
        assert result["ct_account_mentions"] == 0
        assert result["news_account_mentions"] == 0
        assert result["organic_weighted_mentions"] == 100
    
    def test_calculate_weighted_mentions_custom_weights(self):
        """Test weighted mentions with custom weights."""
        from elfa_client import TickerNarrativeSnapshot, AccountInfo, calculate_weighted_mentions
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=10,
            mindshare_score=0.15,
            top_smart_accounts=[],
            account_details=[
                AccountInfo(username="account1", account_type="smart"),
                AccountInfo(username="account2", account_type="ct"),
            ]
        )
        
        result = calculate_weighted_mentions(
            snapshot,
            smart_weight=5.0,
            ct_weight=2.0,
            news_weight=0.1
        )
        
        # 1*5.0 + 1*2.0 = 7.0
        assert result["weighted_mentions"] == 7.0
        assert result["organic_weighted_mentions"] == 7.0
    
    def test_is_organic_narrative_spike_organic(self, mock_env_elfa_api_key):
        """Test organic spike detection for organic narrative."""
        from elfa_client import (
            is_organic_narrative_spike, get_ticker_narrative_snapshot,
            get_event_summary, TickerNarrativeSnapshot
        )
        from unittest.mock import patch
        
        # Create snapshot with low news ratio
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            news_mentions=10,  # 10% news
            organic_mentions=90
        )
        
        with patch('elfa_client.get_ticker_narrative_snapshot', return_value=snapshot):
            with patch('elfa_client.get_event_summary', return_value=[]):  # No events
                result = is_organic_narrative_spike("BTC", window="1h", min_mentions=20)
                
                assert result["is_organic"] is True
                assert result["total_mentions"] == 100
                assert result["news_mentions"] == 10
                assert result["organic_mentions"] == 90
                assert result["news_ratio"] == 0.1  # 10%
                assert result["event_ratio"] == 0.0
                assert "Organic spike" in result["reason"]
    
    def test_is_organic_narrative_spike_news_driven(self, mock_env_elfa_api_key):
        """Test organic spike detection for news-driven narrative."""
        from elfa_client import (
            is_organic_narrative_spike, get_ticker_narrative_snapshot,
            get_event_summary, TickerNarrativeSnapshot, EventSummary
        )
        from unittest.mock import patch
        
        # Create snapshot with high news ratio
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            news_mentions=50,  # 50% news
            organic_mentions=50
        )
        
        # Create events with high mentions
        events = [
            EventSummary(
                event_id="1",
                keywords=["BTC"],
                mentions=40,
                description="Major news event",
                top_accounts=[],
                source_query=""
            )
        ]
        
        with patch('elfa_client.get_ticker_narrative_snapshot', return_value=snapshot):
            with patch('elfa_client.get_event_summary', return_value=events):
                result = is_organic_narrative_spike("BTC", window="1h", min_mentions=20)
                
                assert result["is_organic"] is False
                assert result["news_ratio"] == 0.5  # 50%
                assert result["event_ratio"] == 0.4  # 40%
                assert "News/event-driven" in result["reason"]
    
    def test_is_organic_narrative_spike_no_data(self, mock_env_elfa_api_key):
        """Test organic spike detection when no data is available."""
        from elfa_client import is_organic_narrative_spike
        from unittest.mock import patch
        
        with patch('elfa_client.get_ticker_narrative_snapshot', return_value=None):
            result = is_organic_narrative_spike("BTC", window="1h")
            
            assert result["is_organic"] is False
            assert result["reason"] == "No data available"
            assert result["total_mentions"] == 0
    
    def test_is_organic_narrative_spike_below_min_mentions(self, mock_env_elfa_api_key):
        """Test organic spike detection when mentions are below minimum."""
        from elfa_client import (
            is_organic_narrative_spike, get_ticker_narrative_snapshot,
            TickerNarrativeSnapshot
        )
        from unittest.mock import patch
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=10,  # Below min_mentions threshold
            mindshare_score=0.15,
            top_smart_accounts=[],
            news_mentions=1,
            organic_mentions=9
        )
        
        with patch('elfa_client.get_ticker_narrative_snapshot', return_value=snapshot):
            with patch('elfa_client.get_event_summary', return_value=[]):
                result = is_organic_narrative_spike("BTC", window="1h", min_mentions=20)
                
                assert result["is_organic"] is False
                assert "News/event-driven" in result["reason"] or "No data" in result["reason"]
    
    def test_calculate_platform_divergence_both_platforms(self, mock_env_elfa_api_key):
        """Test platform divergence calculation with both platforms."""
        from elfa_client import (
            calculate_platform_divergence, get_cross_platform_snapshot,
            TickerNarrativeSnapshot
        )
        from unittest.mock import patch
        
        twitter_snap = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            platform="twitter"
        )
        
        telegram_snap = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=150,  # Telegram has more mentions
            mindshare_score=0.18,
            top_smart_accounts=[],
            platform="telegram"
        )
        
        platforms = {
            "twitter": twitter_snap,
            "telegram": telegram_snap
        }
        
        with patch('elfa_client.get_cross_platform_snapshot', return_value=platforms):
            result = calculate_platform_divergence("BTC", window="1h")
            
            assert result is not None
            assert result["ticker"] == "BTC"
            assert result["twitter_mentions"] == 100
            assert result["telegram_mentions"] == 150
            assert result["mention_delta"] == 50  # 150 - 100
            assert result["leading_platform"] == "telegram"
            assert result["divergence_ratio"] == 1.5  # 150 / 100
            assert result["early_signal"] is True  # 150 > 100 * 1.2
    
    def test_calculate_platform_divergence_missing_platform(self, mock_env_elfa_api_key):
        """Test platform divergence when one platform is missing."""
        from elfa_client import (
            calculate_platform_divergence, get_cross_platform_snapshot,
            TickerNarrativeSnapshot
        )
        from unittest.mock import patch
        
        # Only Twitter available
        platforms = {
            "twitter": TickerNarrativeSnapshot(
                ticker="BTC",
                window="1h",
                total_mentions=100,
                mindshare_score=0.15,
                top_smart_accounts=[],
                platform="twitter"
            )
        }
        
        with patch('elfa_client.get_cross_platform_snapshot', return_value=platforms):
            result = calculate_platform_divergence("BTC", window="1h")
            
            assert result is None  # Need both platforms
    
    def test_calculate_platform_divergence_no_data(self, mock_env_elfa_api_key):
        """Test platform divergence when no data is available."""
        from elfa_client import calculate_platform_divergence, get_cross_platform_snapshot
        from unittest.mock import patch
        
        with patch('elfa_client.get_cross_platform_snapshot', return_value=None):
            result = calculate_platform_divergence("BTC", window="1h")
            
            assert result is None


class TestBackwardCompatibility:
    """Tests for backward compatibility with old data structures."""
    
    def test_ticker_snapshot_without_new_fields(self, mock_env_elfa_api_key):
        """Test that TickerNarrativeSnapshot works without new optional fields."""
        from elfa_client import _cache, _rate_limit_tracker
        _cache.clear()
        _rate_limit_tracker.clear()
        
        with patch('elfa_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            # Old-style response without new fields
            mock_response.json.return_value = {
                "results": [
                    {
                        "ticker": "BTC",
                        "total_mentions": 100,
                        "mindshare_score": 0.15,
                        "top_smart_accounts": ["account1", "account2"]
                        # No sentiment_score, account_details, platform, news_mentions, organic_mentions
                    }
                ]
            }
            mock_response.headers = {}
            mock_get.return_value = mock_response
            
            result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
            
            # Should work fine with old data
            assert result is not None
            assert result.ticker == "BTC"
            assert result.total_mentions == 100
            assert result.mindshare_score == 0.15
            # New fields should default to None/0
            assert result.sentiment_score is None
            assert result.account_details == []
            assert result.platform is None
            assert result.news_mentions == 0
            assert result.organic_mentions == 0
    
    def test_calculate_weighted_mentions_backward_compat(self):
        """Test weighted mentions works with old-style snapshots (no account_details)."""
        from elfa_client import TickerNarrativeSnapshot, calculate_weighted_mentions
        
        # Old-style snapshot without account_details
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2"]
            # No account_details field
        )
        
        result = calculate_weighted_mentions(snapshot)
        
        # Should fall back to total_mentions when no account_details
        assert result["weighted_mentions"] == 100
        assert result["smart_account_mentions"] == 0
        assert result["ct_account_mentions"] == 0
        assert result["news_account_mentions"] == 0
    
    def test_is_organic_narrative_spike_backward_compat(self, mock_env_elfa_api_key):
        """Test organic spike detection works with old-style snapshots."""
        from elfa_client import (
            is_organic_narrative_spike, get_ticker_narrative_snapshot,
            TickerNarrativeSnapshot
        )
        from unittest.mock import patch
        
        # Old-style snapshot without news_mentions/organic_mentions
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[]
            # No news_mentions or organic_mentions fields
        )
        
        with patch('elfa_client.get_ticker_narrative_snapshot', return_value=snapshot):
            with patch('elfa_client.get_event_summary', return_value=[]):
                result = is_organic_narrative_spike("BTC", window="1h", min_mentions=20)
                
                # Should handle gracefully - news_mentions defaults to 0
                assert result is not None
                assert result["total_mentions"] == 100
                assert result["news_mentions"] == 0  # Default
                assert result["organic_mentions"] == 0  # Default
    
    def test_enriched_snapshot_backward_compat(self, temp_db_path):
        """Test enrichment works with old-style snapshots."""
        from narrative_enricher import NarrativeEnricher
        from elfa_client import TickerNarrativeSnapshot
        from pathlib import Path
        
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # Old-style snapshot without new fields
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1"],
            source_query="test_query"
            # No new fields
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        # Should work fine
        assert enriched is not None
        assert enriched.ticker == "BTC"
        assert enriched.total_mentions == 100
        # New fields should default to None/0
        assert enriched.sentiment_score is None
        assert enriched.news_mentions == 0
        assert enriched.organic_mentions == 0
        assert enriched.platform is None
        # weighted_mentions may be calculated or None
        assert enriched.weighted_mentions is None or isinstance(enriched.weighted_mentions, (int, float))
