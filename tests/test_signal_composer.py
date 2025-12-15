"""
Tests for signal_composer.py

Tests cover:
- Composition with all data sources
- Weight normalization when data missing
- Conflicting signals
- Scoring logic for each component
- Confidence calculation
- Edge cases
"""
import pytest
from datetime import datetime

from optional.signal_composer import SignalComposer, CompositeSignal, SignalStrength
from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot


class TestCompose:
    """Tests for compose method."""
    
    def test_all_sources_available(self):
        """Test composition with all data sources."""
        composer = SignalComposer()
        
        narrative_data = {
            'mentions': 100,
            'mindshare': 0.15,
            'mentions_velocity': 10,
            'smart_accounts': ['account1', 'account2', 'account3']
        }
        
        market_data = {
            'funding_rate': -0.0001,  # Negative = bullish
            'price_change_24h': 2.5,
            'volume_ratio': 1.5
        }
        
        onchain_data = {
            'exchange_netflow_btc': -1000,  # Negative = bullish
            'whale_balance_change': 1,
            'active_addresses_ratio': 1.2
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=market_data,
            onchain_data=onchain_data
        )
        
        assert signal is not None
        assert isinstance(signal, CompositeSignal)
        assert signal.ticker == "BTC"
        assert -1.0 <= signal.composite_score <= 1.0
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.narrative_score != 0
        assert signal.market_score != 0
        assert signal.onchain_score != 0
    
    def test_missing_onchain_data(self):
        """Test weight normalization when on-chain data missing."""
        composer = SignalComposer()
        
        narrative_data = {
            'mentions': 100,
            'mindshare': 0.15,
            'mentions_velocity': 10,
            'smart_accounts': ['account1']
        }
        
        market_data = {
            'funding_rate': -0.0001,
            'price_change_24h': 2.5,
            'volume_ratio': 1.5
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=market_data,
            onchain_data=None
        )
        
        assert signal is not None
        assert signal.onchain_score == 0
        # Weights should be normalized (narrative + market only)
        # Original: 40% narrative, 35% market, 25% on-chain
        # Normalized: ~53% narrative, ~47% market
        assert signal.composite_score != 0  # Should still calculate
    
    def test_only_narrative_data(self):
        """Test composition with only narrative data."""
        composer = SignalComposer()
        
        narrative_data = {
            'mentions': 100,
            'mindshare': 0.15,
            'mentions_velocity': 10,
            'smart_accounts': ['account1']
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=None,
            onchain_data=None
        )
        
        assert signal is not None
        assert signal.market_score == 0
        assert signal.onchain_score == 0
        # Composite should equal narrative score (100% weight)
        assert abs(signal.composite_score - signal.narrative_score) < 0.01
    
    def test_no_data_sources(self):
        """Test composition with no data sources."""
        composer = SignalComposer()
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=None,
            market_data=None,
            onchain_data=None
        )
        
        assert signal is not None
        assert signal.composite_score == 0.0
        assert signal.confidence == 0.0
    
    def test_conflicting_signals(self):
        """Test confidence calculation with conflicting signals."""
        composer = SignalComposer()
        
        # Narrative bullish
        narrative_data = {
            'mentions': 100,
            'mindshare': 0.20,
            'mentions_velocity': 15,
            'smart_accounts': ['account1', 'account2']
        }
        
        # Market bearish
        market_data = {
            'funding_rate': 0.01,  # Positive = bearish
            'price_change_24h': -5.0,
            'volume_ratio': 0.8
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=market_data,
            onchain_data=None
        )
        
        assert signal is not None
        # Should detect conflict
        assert signal.signal_strength == SignalStrength.CONFLICTED
        # Confidence should be low due to conflict
        assert signal.confidence < 0.5
    
    def test_enriched_snapshot_input(self, sample_enriched_snapshot):
        """Test composition with EnrichedSnapshot input."""
        composer = SignalComposer()
        
        market_data = {
            'funding_rate': -0.0001,
            'price_change_24h': 2.5,
            'volume_ratio': 1.5
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=sample_enriched_snapshot,
            market_data=market_data,
            onchain_data=None
        )
        
        assert signal is not None
        assert signal.narrative_score != 0


class TestScoringLogic:
    """Tests for scoring methods."""
    
    def test_score_narrative(self):
        """Test narrative scoring components."""
        composer = SignalComposer()
        
        # Test mindshare component
        data1 = {'mindshare': 0.25, 'mentions_velocity': 0, 'smart_accounts': []}
        score1 = composer._score_narrative(data1)
        assert 0 <= score1 <= 0.4  # Mindshare capped at 0.4
        
        # Test velocity component
        data2 = {'mindshare': 0, 'mentions_velocity': 20, 'smart_accounts': []}
        score2 = composer._score_narrative(data2)
        assert -0.3 <= score2 <= 0.3  # Velocity range
        
        # Test smart accounts component
        data3 = {'mindshare': 0, 'mentions_velocity': 0, 'smart_accounts': ['a1', 'a2', 'a3']}
        score3 = composer._score_narrative(data3)
        assert 0 <= score3 <= 0.3  # Smart accounts capped at 0.3
        
        # Test score clamping
        data4 = {'mindshare': 1.0, 'mentions_velocity': 100, 'smart_accounts': ['a1'] * 10}
        score4 = composer._score_narrative(data4)
        assert -1.0 <= score4 <= 1.0  # Should be clamped
    
    def test_score_market(self):
        """Test market scoring logic."""
        composer = SignalComposer()
        
        # Test funding rate (negative = bullish)
        data1 = {'funding_rate': -0.01, 'price_change_24h': 0, 'volume_ratio': 1.0}
        score1 = composer._score_market(data1)
        assert score1 > 0  # Negative funding = bullish
        
        # Test price momentum
        data2 = {'funding_rate': 0, 'price_change_24h': 5.0, 'volume_ratio': 1.0}
        score2 = composer._score_market(data2)
        assert score2 > 0  # Positive price change = bullish
        
        # Test volume component
        data3 = {'funding_rate': 0, 'price_change_24h': 0, 'volume_ratio': 2.0}
        score3 = composer._score_market(data3)
        assert score3 > 0  # High volume = bullish
        
        # Test score clamping
        data4 = {'funding_rate': -1.0, 'price_change_24h': 100, 'volume_ratio': 10}
        score4 = composer._score_market(data4)
        assert -1.0 <= score4 <= 1.0
    
    def test_score_onchain(self):
        """Test on-chain scoring logic."""
        composer = SignalComposer()
        
        # Test exchange net flow (negative = bullish)
        data1 = {'exchange_netflow_btc': -5000, 'whale_balance_change': 0, 'active_addresses_ratio': 1.0}
        score1 = composer._score_onchain(data1)
        assert score1 > 0  # Negative flow = bullish
        
        # Test whale accumulation
        data2 = {'exchange_netflow_btc': 0, 'whale_balance_change': 1, 'active_addresses_ratio': 1.0}
        score2 = composer._score_onchain(data2)
        assert score2 > 0  # Accumulating = bullish
        
        # Test active addresses
        data3 = {'exchange_netflow_btc': 0, 'whale_balance_change': 0, 'active_addresses_ratio': 1.5}
        score3 = composer._score_onchain(data3)
        assert score3 > 0  # High activity = bullish


class TestConfidenceCalculation:
    """Tests for confidence calculation."""
    
    def test_high_agreement(self):
        """Test confidence with high agreement (all positive)."""
        composer = SignalComposer()
        
        scores = [0.5, 0.4, 0.3]  # All positive, similar magnitude
        confidence = composer._calculate_confidence(scores)
        
        # With avg_magnitude ~0.4 and std_dev ~0.08, confidence ~0.37
        # This is reasonable for moderate agreement
        assert confidence > 0.3  # Moderate confidence with agreement
        assert confidence < 0.5  # Not extremely high due to variation
    
    def test_mixed_signals(self):
        """Test confidence with mixed signals."""
        composer = SignalComposer()
        
        scores = [0.5, -0.3, 0.2]  # Mixed directions
        confidence = composer._calculate_confidence(scores)
        
        assert confidence < 0.5  # Low confidence with conflict
    
    def test_all_zero(self):
        """Test confidence with all zero scores."""
        composer = SignalComposer()
        
        scores = [0.0, 0.0, 0.0]
        confidence = composer._calculate_confidence(scores)
        
        assert confidence == 0.0
    
    def test_high_magnitude_low_std(self):
        """Test confidence with high magnitude and low std dev."""
        composer = SignalComposer()
        
        scores = [0.8, 0.75, 0.7]  # High magnitude, low variance
        confidence = composer._calculate_confidence(scores)
        
        # With avg_magnitude ~0.75 and std_dev ~0.05, confidence ~0.71
        assert confidence > 0.7  # Very high confidence


class TestSignalClassification:
    """Tests for signal strength classification."""
    
    def test_strong_bullish(self):
        """Test STRONG_BULLISH classification."""
        composer = SignalComposer()
        
        signal = composer._classify_signal(0.7, {
            'narrative': 0.6,
            'market': 0.5,
            'onchain': 0.4
        })
        
        assert signal == SignalStrength.STRONG_BULLISH
    
    def test_bullish(self):
        """Test BULLISH classification."""
        composer = SignalComposer()
        
        signal = composer._classify_signal(0.3, {
            'narrative': 0.3,
            'market': 0.2,
            'onchain': 0.1
        })
        
        assert signal == SignalStrength.BULLISH
    
    def test_neutral(self):
        """Test NEUTRAL classification."""
        composer = SignalComposer()
        
        signal = composer._classify_signal(0.1, {
            'narrative': 0.1,
            'market': 0.0,
            'onchain': -0.1
        })
        
        assert signal == SignalStrength.NEUTRAL
    
    def test_conflicted(self):
        """Test CONFLICTED classification."""
        composer = SignalComposer()
        
        signal = composer._classify_signal(0.0, {
            'narrative': 0.5,  # Strong bullish
            'market': -0.5,   # Strong bearish
            'onchain': 0.0
        })
        
        assert signal == SignalStrength.CONFLICTED


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_extreme_scores(self):
        """Test handling of extreme score values."""
        composer = SignalComposer()
        
        narrative_data = {
            'mentions': 1000000,
            'mindshare': 1.0,
            'mentions_velocity': 1000,
            'smart_accounts': ['a'] * 100
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=None,
            onchain_data=None
        )
        
        # Should be clamped to [-1, 1]
        assert -1.0 <= signal.composite_score <= 1.0
    
    def test_missing_fields(self):
        """Test handling of missing fields in data dicts."""
        composer = SignalComposer()
        
        # Missing some fields
        narrative_data = {
            'mentions': 100
            # Missing mindshare, velocity, smart_accounts
        }
        
        signal = composer.compose(
            ticker="BTC",
            narrative_data=narrative_data,
            market_data=None,
            onchain_data=None
        )
        
        # Should handle gracefully
        assert signal is not None
        assert -1.0 <= signal.composite_score <= 1.0
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        composer = SignalComposer()
        
        # Invalid narrative data type
        signal = composer.compose(
            ticker="BTC",
            narrative_data="invalid_string",
            market_data=None,
            onchain_data=None
        )
        
        # Should handle gracefully (returns None or neutral signal)
        assert signal is not None
