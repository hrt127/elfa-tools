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
from optional.pre_trade_check import PreTradeCheck, TradeDirection


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
        checker = PreTradeCheck()
        assert checker is not None
    
    def test_check_long_trade(self, bullish_snapshot):
        """Test checking a long trade."""
        enriched = enrich_snapshot(bullish_snapshot)
        
        # Create composite signal
        composer = SignalComposer()
        signal = composer.compose(enriched)
        
        # Check trade
        checker = PreTradeCheck()
        result = checker.check(
            ticker="BTC",
            direction=TradeDirection.LONG,
            signal=signal
        )
        
        assert result is not None
        assert result['ticker'] == "BTC"
        assert 'approved' in result
        assert 'reasoning' in result
    
    def test_check_short_trade(self, sample_snapshot):
        """Test checking a short trade."""
        enriched = enrich_snapshot(sample_snapshot)
        
        # Create composite signal
        composer = SignalComposer()
        signal = composer.compose(enriched)
        
        # Check trade
        checker = PreTradeCheck()
        result = checker.check(
            ticker="BTC",
            direction=TradeDirection.SHORT,
            signal=signal
        )
        
        assert result is not None
        assert result['ticker'] == "BTC"
        assert 'approved' in result
    
    def test_check_blocks_weak_signals(self):
        """Test checker blocks weak signals."""
        # Create weak snapshot
        weak_snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=10,  # Low mentions
            mindshare_score=0.01,  # Low mindshare
            top_smart_accounts=[],
            source_query="test"
        )
        
        enriched = enrich_snapshot(weak_snapshot)
        composer = SignalComposer()
        signal = composer.compose(enriched)
        
        checker = PreTradeCheck()
        result = checker.check(
            ticker="BTC",
            direction=TradeDirection.LONG,
            signal=signal
        )
        
        # Should block or warn about weak signal
        assert result is not None
        # Either blocked or has warnings
        assert not result.get('approved', True) or len(result.get('warnings', [])) > 0
    
    def test_check_validates_confidence(self, bullish_snapshot):
        """Test checker validates confidence levels."""
        enriched = enrich_snapshot(bullish_snapshot)
        composer = SignalComposer()
        signal = composer.compose(enriched)
        
        checker = PreTradeCheck()
        result = checker.check(
            ticker="BTC",
            direction=TradeDirection.LONG,
            signal=signal
        )
        
        assert result is not None
        # Should consider confidence in decision
        if result.get('approved'):
            assert signal.confidence >= 0.5  # Reasonable confidence for approval
    
    def test_check_handles_missing_signal(self):
        """Test checker handles missing signal gracefully."""
        checker = PreTradeCheck()
        result = checker.check(
            ticker="BTC",
            direction=TradeDirection.LONG,
            signal=None
        )
        
        # Should handle gracefully, not crash
        assert result is not None
        assert not result.get('approved', True)  # Should block without signal

