"""
Tests for narrative_enricher.py

Tests cover:
- First snapshot (no previous data)
- Second snapshot (velocity calculation)
- Third snapshot (true acceleration)
- Account churn detection
- Database persistence
- Edge cases
"""
import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from narrative_enricher import NarrativeEnricher, EnrichedSnapshot
from elfa_client import TickerNarrativeSnapshot


class TestEnrichSnapshot:
    """Tests for enrich_snapshot method."""
    
    def test_first_snapshot(self, temp_db_path):
        """Test enrichment with no previous data."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query"
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.ticker == "BTC"
        assert enriched.total_mentions == 100
        assert enriched.delta_mentions == 100  # First snapshot = total
        assert enriched.acceleration is None  # Cannot calculate acceleration yet (needs 3+ snapshots)
        # For first snapshot, all accounts are considered "new" since there's no baseline
        assert len(enriched.new_accounts) == 3  # All accounts are new on first snapshot
        assert len(enriched.lost_accounts) == 0
    
    def test_second_snapshot(self, temp_db_path):
        """Test enrichment with one previous snapshot."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # First snapshot
        snapshot1 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query"
        )
        enriched1 = enricher.enrich_snapshot(snapshot1)
        
        # Second snapshot
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=120,
            mindshare_score=0.18,
            top_smart_accounts=["account1", "account2", "account4"],
            source_query="test_query"
        )
        enriched2 = enricher.enrich_snapshot(snapshot2)
        
        assert enriched2.delta_mentions == 20  # 120 - 100
        assert enriched2.acceleration is None  # Only 2 snapshots, cannot calculate acceleration
        assert "account4" in enriched2.new_accounts
        assert "account3" in enriched2.lost_accounts
    
    def test_third_snapshot_true_acceleration(self, temp_db_path):
        """Test enrichment with two previous snapshots (true acceleration)."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # First snapshot
        snapshot1 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2"],
            source_query="test_query"
        )
        enricher.enrich_snapshot(snapshot1)
        
        # Second snapshot
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=110,
            mindshare_score=0.16,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query"
        )
        enricher.enrich_snapshot(snapshot2)
        
        # Third snapshot
        snapshot3 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=130,
            mindshare_score=0.20,
            top_smart_accounts=["account1", "account3", "account4"],
            source_query="test_query"
        )
        enriched3 = enricher.enrich_snapshot(snapshot3)
        
        # Velocity: 130 - 110 = 20
        # Previous velocity: 110 - 100 = 10
        # Acceleration: 20 - 10 = 10
        assert enriched3.delta_mentions == 20
        assert enriched3.acceleration == 10  # True acceleration calculated
    
    def test_account_churn(self, temp_db_path):
        """Test account churn detection."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # First snapshot
        snapshot1 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2", "account3"],
            source_query="test_query"
        )
        enricher.enrich_snapshot(snapshot1)
        
        # Second snapshot with different accounts
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=120,
            mindshare_score=0.18,
            top_smart_accounts=["account2", "account4", "account5"],
            source_query="test_query"
        )
        enriched2 = enricher.enrich_snapshot(snapshot2)
        
        # account4 and account5 are new
        assert "account4" in enriched2.new_accounts
        assert "account5" in enriched2.new_accounts
        # account1 and account3 are lost
        assert "account1" in enriched2.lost_accounts
        assert "account3" in enriched2.lost_accounts
        # account2 remains
        assert "account2" not in enriched2.new_accounts
        assert "account2" not in enriched2.lost_accounts
    
    def test_negative_delta(self, temp_db_path):
        """Test handling of negative delta (decreasing mentions)."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # First snapshot
        snapshot1 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enricher.enrich_snapshot(snapshot1)
        
        # Second snapshot with fewer mentions
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=80,
            mindshare_score=0.12,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enriched2 = enricher.enrich_snapshot(snapshot2)
        
        assert enriched2.delta_mentions == -20  # Negative delta
        assert enriched2.acceleration is None  # Only 2 snapshots, cannot calculate acceleration


class TestDatabasePersistence:
    """Tests for database persistence."""
    
    def test_store_snapshot(self, temp_db_path):
        """Test snapshot storage to SQLite."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1", "account2"],
            source_query="test_query"
        )
        
        enricher.store_snapshot(snapshot)
        
        # Verify stored in database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, total_mentions FROM snapshots WHERE ticker = ?", ("BTC",))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[0] == "BTC"
        assert row[1] == 100
    
    def test_get_last_snapshot(self, temp_db_path):
        """Test retrieving last snapshot."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # Store multiple snapshots
        snapshot1 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enricher.store_snapshot(snapshot1)
        
        snapshot2 = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=120,
            mindshare_score=0.18,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enricher.store_snapshot(snapshot2)
        
        # Get last snapshot
        last = enricher.get_last_snapshot("BTC", "1h")
        
        assert last is not None
        assert last.total_mentions == 120  # Most recent
    
    def test_get_last_two_snapshots(self, temp_db_path):
        """Test retrieving last two snapshots."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # Store three snapshots
        for mentions in [100, 110, 120]:
            snapshot = TickerNarrativeSnapshot(
                ticker="BTC",
                window="1h",
                total_mentions=mentions,
                mindshare_score=0.15,
                top_smart_accounts=[],
                source_query="test_query"
            )
            enricher.store_snapshot(snapshot)
        
        last, prev = enricher.get_last_two_snapshots("BTC", "1h")
        
        assert last is not None
        assert prev is not None
        assert last.total_mentions == 120
        assert prev.total_mentions == 110


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_account_list(self, temp_db_path):
        """Test handling of empty account lists."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],  # Empty list
            source_query="test_query"
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert len(enriched.top_smart_accounts) == 0
        assert len(enriched.new_accounts) == 0
        assert len(enriched.lost_accounts) == 0
    
    def test_none_mindshare(self, temp_db_path):
        """Test handling when mindshare_score is None."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=None,
            top_smart_accounts=[],
            source_query="test_query"
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.mindshare_score is None
    
    def test_very_large_mention_count(self, temp_db_path):
        """Test handling of very large mention counts."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=1000000,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query"
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.total_mentions == 1000000
    
    def test_different_windows(self, temp_db_path):
        """Test that different windows are tracked separately."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        # Snapshot with 1h window
        snapshot1h = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enricher.enrich_snapshot(snapshot1h)
        
        # Snapshot with 4h window
        snapshot4h = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=200,
            mindshare_score=0.20,
            top_smart_accounts=[],
            source_query="test_query"
        )
        enriched4h = enricher.enrich_snapshot(snapshot4h)
        
        # Should be treated as first snapshot for 4h window
        assert enriched4h.delta_mentions == 200  # First snapshot for 4h window


class TestNewEnhancementFields:
    """Tests for new enhancement fields in EnrichedSnapshot."""
    
    def test_enrich_with_sentiment_score(self, temp_db_path):
        """Test enrichment preserves sentiment_score from snapshot."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query",
            sentiment_score=0.75  # New field
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.sentiment_score == 0.75
    
    def test_enrich_without_sentiment_score(self, temp_db_path):
        """Test backward compatibility when sentiment_score is missing."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query"
            # No sentiment_score - should default to None
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.sentiment_score is None  # Should handle missing field gracefully
    
    def test_enrich_with_news_organic_mentions(self, temp_db_path):
        """Test enrichment preserves news_mentions and organic_mentions."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query",
            news_mentions=20,  # New field
            organic_mentions=80  # New field
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.news_mentions == 20
        assert enriched.organic_mentions == 80
    
    def test_enrich_with_platform(self, temp_db_path):
        """Test enrichment preserves platform field."""
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query",
            platform="twitter"  # New field
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.platform == "twitter"
    
    def test_enrich_with_weighted_mentions(self, temp_db_path):
        """Test enrichment can calculate and store weighted_mentions."""
        from elfa_client import AccountInfo, calculate_weighted_mentions
        
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=10,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="test_query",
            account_details=[
                AccountInfo(username="account1", account_type="smart"),
                AccountInfo(username="account2", account_type="ct"),
            ]
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        # Calculate weighted mentions manually to verify
        weighted = calculate_weighted_mentions(snapshot)
        
        assert enriched is not None
        # The enricher may or may not calculate weighted_mentions automatically
        # But if it does, it should match our calculation
        if enriched.weighted_mentions is not None:
            assert enriched.weighted_mentions == weighted["weighted_mentions"]
    
    def test_enrich_all_new_fields_together(self, temp_db_path):
        """Test enrichment with all new fields present."""
        from elfa_client import AccountInfo
        
        enricher = NarrativeEnricher(db_path=Path(temp_db_path))
        
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="1h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1"],
            source_query="test_query",
            sentiment_score=0.65,
            account_details=[
                AccountInfo(username="account1", account_type="smart"),
            ],
            platform="twitter",
            news_mentions=10,
            organic_mentions=90
        )
        
        enriched = enricher.enrich_snapshot(snapshot)
        
        assert enriched is not None
        assert enriched.sentiment_score == 0.65
        assert enriched.platform == "twitter"
        assert enriched.news_mentions == 10
        assert enriched.organic_mentions == 90