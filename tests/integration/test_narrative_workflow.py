"""
Integration tests for narrative workflow.

Tests the complete flow:
- elfa_client → narrative_enricher → narrative_radar
- elfa_client → narrative_enricher → decision_moment
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elfa_client import TickerNarrativeSnapshot, get_ticker_narrative_snapshot
from narrative_enricher import enrich_snapshot, EnrichedSnapshot
from decision_moment import DecisionMoment, DecisionMomentPolicy, BoringModeConfig


@pytest.fixture
def mock_elfa_api_response():
    """Mock Elfa API response."""
    return {
        "ticker": "BTC",
        "window": "4h",
        "total_mentions": 150,
        "mindshare_score": 0.18,
        "top_smart_accounts": ["account1", "account2", "account3"],
        "timestamp": datetime.utcnow().isoformat(),
        "source_query": "test_query"
    }


@pytest.fixture
def sample_snapshot(mock_elfa_api_response):
    """Create a sample TickerNarrativeSnapshot."""
    return TickerNarrativeSnapshot(
        ticker=mock_elfa_api_response["ticker"],
        window=mock_elfa_api_response["window"],
        total_mentions=mock_elfa_api_response["total_mentions"],
        mindshare_score=mock_elfa_api_response["mindshare_score"],
        top_smart_accounts=mock_elfa_api_response["top_smart_accounts"],
        source_query=mock_elfa_api_response["source_query"]
    )


class TestNarrativeEnrichmentWorkflow:
    """Test narrative enrichment workflow."""
    
    def test_fetch_and_enrich_workflow(self, mock_elfa_api_response):
        """Test complete workflow: fetch → enrich."""
        with patch('elfa_client.requests.get') as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_get.return_value = mock_response
            
            # Fetch snapshot
            snapshot = get_ticker_narrative_snapshot("BTC", "4h")
            
            assert snapshot is not None
            assert snapshot.ticker == "BTC"
            assert snapshot.total_mentions == 150
            
            # Enrich snapshot (first time - no history)
            enriched = enrich_snapshot(snapshot)
            
            assert enriched is not None
            assert isinstance(enriched, EnrichedSnapshot)
            assert enriched.ticker == "BTC"
            assert enriched.delta_mentions == 0  # First snapshot, no previous
            assert enriched.acceleration == 0.0
    
    def test_enrichment_with_history(self, sample_snapshot):
        """Test enrichment with historical data."""
        # First snapshot
        enriched1 = enrich_snapshot(sample_snapshot)
        
        assert enriched1 is not None
        assert enriched1.delta_mentions == 0
        
        # Second snapshot with more mentions
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=200,  # Increased
            mindshare_score=0.20,
            top_smart_accounts=["account1", "account2", "account3", "account4"],
            source_query="test_query_2"
        )
        
        enriched2 = enrich_snapshot(snapshot2)
        
        assert enriched2 is not None
        assert enriched2.delta_mentions == 50  # 200 - 150
        assert enriched2.acceleration > 0  # Positive acceleration
    
    def test_enrichment_tracks_account_churn(self, sample_snapshot):
        """Test enrichment tracks account churn."""
        # First snapshot
        enriched1 = enrich_snapshot(sample_snapshot)
        
        # Second snapshot with different accounts
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=150,
            mindshare_score=0.18,
            top_smart_accounts=["account1", "account2", "account5"],  # account3 lost, account5 new
            source_query="test_query_2"
        )
        
        enriched2 = enrich_snapshot(snapshot2)
        
        assert enriched2 is not None
        assert "account5" in enriched2.new_accounts
        assert "account3" in enriched2.lost_accounts


class TestDecisionMomentWorkflow:
    """Test Decision Moment workflow."""
    
    def test_enrichment_to_decision_moment(self, sample_snapshot):
        """Test creating Decision Moment from enriched snapshot."""
        # Enrich snapshot
        enriched = enrich_snapshot(sample_snapshot)
        
        # Create a second enriched snapshot with significant change
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=250,  # Large increase
            mindshare_score=0.25,
            top_smart_accounts=["account1", "account2", "account3", "account4", "account5"],
            source_query="test_query_2"
        )
        enriched2 = enrich_snapshot(snapshot2)
        
        # Create Decision Moment from the diff
        from decision_moment import DecisionMomentDiff
        
        diff = DecisionMomentDiff(
            ticker="BTC",
            window="4h",
            previous=enriched,
            current=enriched2,
            signals=[
                {
                    "name": "Narrative Velocity",
                    "value": enriched2.delta_mentions,
                    "baseline": 0,
                    "note": f"{enriched2.delta_mentions} mentions increase"
                }
            ]
        )
        
        # Check if it's a Decision Moment
        policy = DecisionMomentPolicy(BoringModeConfig())
        decision_moment = policy.evaluate(diff)
        
        # Should surface as Decision Moment due to high velocity
        assert decision_moment is not None
        assert decision_moment.ticker == "BTC"
        assert len(decision_moment.signals) > 0
    
    def test_decision_moment_policy_boring_mode(self, sample_snapshot):
        """Test Decision Moment policy with boring mode."""
        # Create two similar snapshots (boring)
        enriched1 = enrich_snapshot(sample_snapshot)
        
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=155,  # Small change
            mindshare_score=0.19,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query_2"
        )
        enriched2 = enrich_snapshot(snapshot2)
        
        from decision_moment import DecisionMomentDiff
        
        diff = DecisionMomentDiff(
            ticker="BTC",
            window="4h",
            previous=enriched1,
            current=enriched2,
            signals=[
                {
                    "name": "Narrative Velocity",
                    "value": enriched2.delta_mentions,
                    "baseline": 0,
                    "note": "Small change"
                }
            ]
        )
        
        # Boring mode should filter out small changes
        policy = DecisionMomentPolicy(BoringModeConfig())
        decision_moment = policy.evaluate(diff)
        
        # Should be None or marked as boring
        if decision_moment is not None:
            assert decision_moment.is_boring is True


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""
    
    def test_complete_narrative_analysis_workflow(self, mock_elfa_api_response):
        """Test complete workflow from API to Decision Moment."""
        with patch('elfa_client.requests.get') as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_get.return_value = mock_response
            
            # Step 1: Fetch from API
            snapshot = get_ticker_narrative_snapshot("BTC", "4h")
            assert snapshot is not None
            
            # Step 2: Enrich with temporal context
            enriched = enrich_snapshot(snapshot)
            assert enriched is not None
            
            # Step 3: Create Decision Moment (if significant)
            # This would typically compare with previous snapshot
            # For this test, we'll just verify the enriched data is usable
            assert enriched.ticker == "BTC"
            assert enriched.total_mentions > 0
            assert enriched.mindshare_score is not None
    
    def test_workflow_handles_api_errors(self):
        """Test workflow handles API errors gracefully."""
        with patch('elfa_client.requests.get') as mock_get:
            # Mock API error
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            # Should return None, not crash
            snapshot = get_ticker_narrative_snapshot("BTC", "4h")
            assert snapshot is None
    
    def test_workflow_handles_missing_data(self):
        """Test workflow handles missing data gracefully."""
        # Try to enrich None snapshot
        enriched = enrich_snapshot(None)
        assert enriched is None
        
        # Try to enrich snapshot with missing fields
        incomplete_snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=100,
            mindshare_score=None,
            top_smart_accounts=None,
            source_query="test"
        )
        
        enriched = enrich_snapshot(incomplete_snapshot)
        # Should still work, just with None values
        assert enriched is not None
        assert enriched.mindshare_score is None

