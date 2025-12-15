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
        "results": [
            {
                "ticker": "BTC",
                "total_mentions": 150,
                "mindshare_score": 0.18,
                "top_smart_accounts": ["account1", "account2", "account3"],
            }
        ]
    }


@pytest.fixture
def sample_snapshot(mock_elfa_api_response):
    """Create a sample TickerNarrativeSnapshot."""
    # Extract data from the results array structure
    result_data = (
        mock_elfa_api_response["results"][0]
        if "results" in mock_elfa_api_response
        else mock_elfa_api_response
    )
    return TickerNarrativeSnapshot(
        ticker=result_data.get("ticker", "BTC"),
        window="4h",
        total_mentions=result_data.get("total_mentions", 150),
        mindshare_score=result_data.get("mindshare_score", 0.18),
        top_smart_accounts=result_data.get(
            "top_smart_accounts", ["account1", "account2", "account3"]
        ),
        source_query="test_query",
    )


class TestNarrativeEnrichmentWorkflow:
    """Test narrative enrichment workflow."""

    def test_fetch_and_enrich_workflow(self, mock_elfa_api_response, tmp_path):
        """Test complete workflow: fetch → enrich."""
        import tempfile
        import os
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher

        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"

        with patch.dict("os.environ", {"ELFA_API_KEY": "test_key"}):
            with patch("elfa_client.requests.get") as mock_get:
                # Mock API response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_elfa_api_response
                mock_response.headers = {}
                mock_get.return_value = mock_response

                # Fetch snapshot
                snapshot = get_ticker_narrative_snapshot("BTC", "4h", use_cache=False)

                assert snapshot is not None
                assert snapshot.ticker == "BTC"
                assert snapshot.total_mentions == 150

                # Enrich snapshot using temporary database (first time - no history)
                enricher = NarrativeEnricher(db_path=temp_db)
                enriched = enricher.enrich_snapshot(snapshot)

                assert enriched is not None
                assert isinstance(enriched, EnrichedSnapshot)
                assert enriched.ticker == "BTC"
                assert enriched.delta_mentions == 150  # First snapshot = total mentions
                assert enriched.acceleration is None  # Cannot calculate acceleration yet (needs 3+ snapshots)

    def test_enrichment_with_history(self, sample_snapshot, tmp_path):
        """Test enrichment with historical data."""
        # Use temporary database for test isolation
        temp_db = tmp_path / "test_narrative.db"
        
        # First snapshot
        enriched1 = enrich_snapshot(sample_snapshot, db_path=temp_db)

        assert enriched1 is not None
        assert enriched1.delta_mentions == 150  # First snapshot = total mentions (no previous data)

        # Second snapshot with more mentions
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=200,  # Increased
            mindshare_score=0.20,
            top_smart_accounts=["account1", "account2", "account3", "account4"],
            source_query="test_query_2",
        )

        enriched2 = enrich_snapshot(snapshot2, db_path=temp_db)

        assert enriched2 is not None
        assert enriched2.delta_mentions == 50  # 200 - 150
        assert enriched2.acceleration is None  # Need 3+ snapshots for acceleration

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
            top_smart_accounts=[
                "account1",
                "account2",
                "account5",
            ],  # account3 lost, account5 new
            source_query="test_query_2",
        )

        enriched2 = enrich_snapshot(snapshot2)

        assert enriched2 is not None
        assert "account5" in enriched2.new_accounts
        assert "account3" in enriched2.lost_accounts


class TestDecisionMomentWorkflow:
    """Test Decision Moment workflow."""

    def test_enrichment_to_decision_moment(self, sample_snapshot, tmp_path):
        """Test creating Decision Moment from enriched snapshot."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher

        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)

        # Enrich snapshot
        enriched = enricher.enrich_snapshot(sample_snapshot)

        # Create a second enriched snapshot with significant change
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=250,  # Large increase
            mindshare_score=0.25,
            top_smart_accounts=[
                "account1",
                "account2",
                "account3",
                "account4",
                "account5",
            ],
            source_query="test_query_2",
        )
        enriched2 = enricher.enrich_snapshot(snapshot2)

        # Create Decision Moment manually
        from decision_moment import DecisionMoment, SignalEvidence, DecisionMomentPolicy

        decision_moment = DecisionMoment(
            id="BTC_test_1",
            timestamp=enriched2.timestamp,
            subject_type="ticker",
            symbol="BTC",
            window="4h",
            trigger_description="Narrative velocity spike",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence(
                    name="Narrative Velocity",
                    value=enriched2.delta_mentions,
                    baseline=0,
                    note=f"{enriched2.delta_mentions} mentions increase",
                )
            ],
        )

        # Check if it should trigger
        policy = DecisionMomentPolicy(boring_mode=False)
        should_trigger = policy.should_trigger(decision_moment)

        # Should surface as Decision Moment due to high velocity
        assert should_trigger is True
        assert decision_moment.symbol == "BTC"
        assert len(decision_moment.signals_contributing) > 0

    def test_decision_moment_policy_boring_mode(self, sample_snapshot, tmp_path):
        """Test Decision Moment policy with boring mode."""
        from pathlib import Path
        from narrative_enricher import NarrativeEnricher

        # Use temporary database
        temp_db = tmp_path / "test_narrative.db"
        enricher = NarrativeEnricher(db_path=temp_db)

        # Create two similar snapshots (boring)
        enriched1 = enricher.enrich_snapshot(sample_snapshot)

        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=155,  # Small change
            mindshare_score=0.19,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query_2",
        )
        enriched2 = enricher.enrich_snapshot(snapshot2)

        from decision_moment import (
            DecisionMoment,
            SignalEvidence,
            DecisionMomentPolicy,
            BoringModeConfig,
        )

        # Create Decision Moment with small change
        decision_moment = DecisionMoment(
            id="BTC_test_2",
            timestamp=enriched2.timestamp,
            subject_type="ticker",
            symbol="BTC",
            window="4h",
            trigger_description="Small narrative change",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence(
                    name="Narrative Velocity",
                    value=enriched2.delta_mentions,
                    baseline=0,
                    note="Small change",
                )
            ],
        )

        # Boring mode should filter out small changes
        config = BoringModeConfig(min_velocity_multiplier=2.0)  # Require 2x change
        policy = DecisionMomentPolicy(boring_mode=True, config=config)
        should_trigger = policy.should_trigger(decision_moment)

        # Should be filtered out (False) due to boring mode
        assert should_trigger is False


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    def test_complete_narrative_analysis_workflow(self, mock_elfa_api_response, tmp_path):
        """Test complete workflow from API to Decision Moment."""
        # Use temporary database for test isolation
        temp_db = tmp_path / "test_narrative.db"
        
        with patch("elfa_client.requests.get") as mock_get, \
             patch.dict(os.environ, {"ELFA_API_KEY": "test_key"}):
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_elfa_api_response
            mock_get.return_value = mock_response

            # Step 1: Fetch from API
            snapshot = get_ticker_narrative_snapshot("BTC", "4h", use_cache=False)
            assert snapshot is not None

            # Step 2: Enrich with temporal context
            enriched = enrich_snapshot(snapshot, db_path=temp_db)
            assert enriched is not None

            # Step 3: Create Decision Moment (if significant)
            # This would typically compare with previous snapshot
            # For this test, we'll just verify the enriched data is usable
            assert enriched.ticker == "BTC"
            assert enriched.total_mentions > 0
            assert enriched.mindshare_score is not None

    def test_workflow_handles_api_errors(self):
        """Test workflow handles API errors gracefully."""
        with patch("elfa_client.requests.get") as mock_get:
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
            source_query="test",
        )

        enriched = enrich_snapshot(incomplete_snapshot)
        # Should still work, just with None values
        assert enriched is not None
        assert enriched.mindshare_score is None
