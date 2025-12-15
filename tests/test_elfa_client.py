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
    _get_cache_key
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
