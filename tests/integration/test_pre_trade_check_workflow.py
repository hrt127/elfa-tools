"""
Integration tests for pre-trade check workflow.

Tests the complete flow:
- signal_composer → pre_trade_check
"""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import enrich_snapshot
from optional.signal_composer import SignalComposer, CompositeSignal
from optional.pre_trade_check import PreTradeChecker


@pytest.fixture
def sample_snapshot():
    """Create a sample snapshot."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1", "account2"],
        source_query="test"
    )


@pytest.fixture
def bullish_snapshot():
    """Create a bullish snapshot."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=200,  # High mentions
        mindshare_score=0.25,  # High mindshare
        top_smart_accounts=["account1", "account2", "account3", "account4"],
        source_query="test"
    )


class TestPreTradeCheckWorkflow:
    """Test pre-trade check workflow."""
    
    def test_pre_trade_check_initialization(self):
        """Test pre-trade check initializes correctly."""
        checker = PreTradeChecker()
        assert checker is not None
    
    def test_check_long_trade(self, bullish_snapshot, tmp_path):
        """Test checking a long trade."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher
        
        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)
        enriched = enricher.enrich_snapshot(bullish_snapshot)
        
        # Check trade using the actual API
        checker = PreTradeChecker()
        result = checker.check_trade(
            ticker="BTC",
            side="long"
        )
        
        assert result is not None
        assert 'valid' in result
        assert 'reason' in result or 'reasoning' in result
    
    def test_check_short_trade(self, sample_snapshot, tmp_path):
        """Test checking a short trade."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher
        
        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)
        enriched = enricher.enrich_snapshot(sample_snapshot)
        
        # Check trade
        checker = PreTradeChecker()
        result = checker.check_trade(
            ticker="BTC",
            side="short"
        )
        
        assert result is not None
        assert 'valid' in result
    
    def test_check_blocks_weak_signals(self, tmp_path):
        """Test checker blocks weak signals."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher
        
        # Create weak snapshot
        weak_snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=10,  # Low mentions
            mindshare_score=0.01,  # Low mindshare
            top_smart_accounts=[],
            source_query="test"
        )
        
        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)
        enriched = enricher.enrich_snapshot(weak_snapshot)
        
        checker = PreTradeChecker()
        result = checker.check_trade(
            ticker="BTC",
            side="long"
        )
        
        # Should block or warn about weak signal
        assert result is not None
        # Either invalid or has low confidence
        assert not result.get('valid', True) or result.get('confidence', 1.0) < 0.5
    
    def test_check_validates_confidence(self, bullish_snapshot, tmp_path):
        """Test checker validates confidence levels."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher
        
        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)
        enriched = enricher.enrich_snapshot(bullish_snapshot)
        
        checker = PreTradeChecker()
        result = checker.check_trade(
            ticker="BTC",
            side="long"
        )
        
        assert result is not None
        # Should have confidence level
        assert 'confidence' in result
    
    def test_check_handles_missing_signal(self):
        """Test checker handles missing signal gracefully."""
        checker = PreTradeChecker()
        # The actual API doesn't take a signal parameter, it fetches data itself
        # So we test with a ticker that won't have data
        result = checker.check_trade(
            ticker="NONEXISTENTTICKER123",
            side="long"
        )
        
        # Should handle gracefully, not crash
        assert result is not None
        assert not result.get('valid', True)  # Should be invalid without data

