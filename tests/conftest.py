"""
Pytest configuration and shared fixtures for Elfa Tools tests.
"""
import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Dict, Any

from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot

# Try importing signal_composer (may be in optional/)
try:
    from signal_composer import CompositeSignal, SignalStrength
except ImportError:
    # If not available, create a mock
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime
    
    class SignalStrength(Enum):
        STRONG_BULLISH = "strong_bullish"
        BULLISH = "bullish"
        NEUTRAL = "neutral"
        BEARISH = "bearish"
        STRONG_BEARISH = "strong_bearish"
        CONFLICTED = "conflicted"
    
    @dataclass
    class CompositeSignal:
        ticker: str
        timestamp: datetime
        narrative_score: float
        market_score: float
        onchain_score: float
        composite_score: float
        signal_strength: SignalStrength
        confidence: float
        evidence: dict
        warnings: list


@pytest.fixture
def mock_env_elfa_api_key(monkeypatch):
    """Set ELFA_API_KEY environment variable for tests."""
    monkeypatch.setenv("ELFA_API_KEY", "test_api_key_12345")
    yield "test_api_key_12345"
    monkeypatch.delenv("ELFA_API_KEY", raising=False)


@pytest.fixture
def sample_ticker_snapshot():
    """Create a sample TickerNarrativeSnapshot for testing."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="1h",
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1", "account2", "account3"],
        source_query="GET https://api.elfa.ai/v2/data/top-mentions?ticker=BTC&timeWindow=1h"
    )


@pytest.fixture
def sample_enriched_snapshot():
    """Create a sample EnrichedSnapshot for testing."""
    return EnrichedSnapshot(
        ticker="BTC",
        window="1h",
        timestamp=datetime.utcnow(),
        total_mentions=120,
        mindshare_score=0.18,
        top_smart_accounts=["account1", "account2", "account4"],
        delta_mentions=20,
        acceleration=5,
        new_accounts=["account4"],
        lost_accounts=["account3"],
        source_query="GET https://api.elfa.ai/v2/data/top-mentions?ticker=BTC&timeWindow=1h"
    )


@pytest.fixture
def sample_composite_signal():
    """Create a sample CompositeSignal for testing."""
    return CompositeSignal(
        ticker="BTC",
        timestamp=datetime.now(),
        narrative_score=0.5,
        market_score=0.3,
        onchain_score=0.2,
        composite_score=0.35,
        signal_strength=SignalStrength.BULLISH,
        confidence=0.75,
        evidence={
            "Mentions": 120,
            "Mindshare": "0.18",
            "Smart accounts": 3,
            "Velocity": 20
        },
        warnings=[]
    )


@pytest.fixture
def mock_elfa_api_response():
    """Mock Elfa API response."""
    return {
        "results": [
            {
                "ticker": "BTC",
                "total_mentions": 100,
                "mindshare_score": 0.15,
                "top_smart_accounts": [
                    {"username": "account1"},
                    {"username": "account2"},
                    {"username": "account3"}
                ]
            }
        ]
    }


@pytest.fixture
def mock_binance_premium_index():
    """Mock Binance premium index response."""
    return {
        "symbol": "BTCUSDT",
        "lastFundingRate": "0.0001"
    }


@pytest.fixture
def mock_binance_ticker_24hr():
    """Mock Binance 24hr ticker response."""
    return {
        "symbol": "BTCUSDT",
        "lastPrice": "50000",
        "priceChangePercent": "2.5",
        "volume": "1000000"
    }


@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database path for tests."""
    return str(tmp_path / "test_narrative_history.db")


@pytest.fixture
def temp_duckdb_path(tmp_path):
    """Create temporary DuckDB path for tests."""
    return str(tmp_path / "test_narrative_chronicle.duckdb")


@pytest.fixture
def temp_alerts_db_path(tmp_path):
    """Create temporary alerts database path for tests."""
    return str(tmp_path / "test_alerts_history.db")


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test."""
    from elfa_client import clear_cache
    from perp_client import clear_cache as clear_perp_cache
    from onchain_client import clear_cache as clear_onchain_cache
    
    clear_cache()
    clear_perp_cache()
    clear_onchain_cache()
    
    yield
    
    # Clean up after test
    clear_cache()
    clear_perp_cache()
    clear_onchain_cache()
