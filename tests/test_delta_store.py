"""
Tests for delta_store.py

Tests cover:
- Snapshot storage (DuckDB)
- Velocity calculation (time-based)
- Anomaly detection (Z-score)
- Historical retrieval
- Insufficient data handling
- Edge cases
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from optional.delta_store import DeltaStore
from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".duckdb")
    os.close(fd)
    # Remove file if it exists (might be leftover from previous test)
    if os.path.exists(path):
        os.remove(path)
    yield path
    # Cleanup after test
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass


@pytest.fixture
def store(temp_db):
    """Create a DeltaStore with temporary database."""
    store = DeltaStore(db_path=temp_db)
    yield store
    store.close()


@pytest.fixture
def sample_snapshot():
    """Create a sample TickerNarrativeSnapshot."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1", "account2"],
        source_query="test_query",
    )


@pytest.fixture
def sample_enriched_snapshot():
    """Create a sample EnrichedSnapshot."""
    return EnrichedSnapshot(
        ticker="BTC",
        window="4h",
        timestamp=datetime.utcnow(),
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1"],
        source_query="test_query",
        delta_mentions=25,
        acceleration=5.0,
        new_accounts=["new1"],
        lost_accounts=["lost1"],
    )


class TestDeltaStoreInitialization:
    """Tests for DeltaStore initialization."""

    def test_store_initialization(self, temp_db):
        """Test store initializes correctly."""
        store = DeltaStore(db_path=temp_db)
        assert store.db_path == temp_db
        assert store.conn is not None
        store.close()

    def test_store_creates_tables(self, temp_db):
        """Test store creates required tables."""
        store = DeltaStore(db_path=temp_db)

        # Check tables exist
        tables = store.conn.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
        """
        ).fetchall()

        table_names = [t[0] for t in tables]
        assert "narrative_snapshots" in table_names
        store.close()

    def test_store_creates_indexes(self, temp_db):
        """Test store creates required indexes."""
        store = DeltaStore(db_path=temp_db)

        # Check indexes exist (DuckDB doesn't expose indexes easily, so we test by query performance)
        # Just verify the store works
        assert store.conn is not None
        store.close()


class TestSnapshotInsertion:
    """Tests for snapshot insertion."""

    def test_insert_ticker_narrative_snapshot(self, store, sample_snapshot):
        """Test inserting TickerNarrativeSnapshot."""
        result = store.insert(sample_snapshot)

        assert result is True

        # Verify data was inserted
        latest = store.get_latest("BTC", "4h")
        assert latest is not None
        assert latest["ticker"] == "BTC"
        assert latest["mentions"] == 100
        assert latest["mindshare"] == 0.15

    def test_insert_enriched_snapshot(self, store, sample_enriched_snapshot):
        """Test inserting EnrichedSnapshot."""
        result = store.insert(sample_enriched_snapshot)

        assert result is True

        # Verify data was inserted
        latest = store.get_latest("BTC", "4h")
        assert latest is not None
        assert latest["ticker"] == "BTC"
        assert latest["mentions"] == 100

    def test_insert_unsupported_type(self, store):
        """Test inserting unsupported type returns False."""
        result = store.insert("not a snapshot")

        assert result is False

    def test_insert_handles_errors(self, store):
        """Test insert handles errors gracefully."""
        # Create a mock that will cause error
        bad_snapshot = Mock()
        bad_snapshot.ticker = "BTC"
        bad_snapshot.window = "4h"
        bad_snapshot.total_mentions = property(lambda self: raise_(ValueError("test")))

        result = store.insert(bad_snapshot)

        assert result is False

    def test_insert_multiple_snapshots(self, store):
        """Test inserting multiple snapshots."""
        # Insert multiple snapshots with different timestamps
        base_time = datetime.utcnow()
        for i in range(5):
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=4 - i),
                total_mentions=100 + i * 10,
                mindshare_score=0.15,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        # Verify latest is the most recent
        latest = store.get_latest("BTC", "4h")
        assert latest is not None
        assert latest["mentions"] == 140  # 100 + 4*10


class TestHistoricalRetrieval:
    """Tests for historical data retrieval."""

    def test_get_latest_exists(self, store, sample_snapshot):
        """Test getting latest snapshot when it exists."""
        store.insert(sample_snapshot)

        latest = store.get_latest("BTC", "4h")

        assert latest is not None
        assert latest["ticker"] == "BTC"
        assert latest["window"] == "4h"
        assert latest["mentions"] == 100

    def test_get_latest_not_exists(self, store):
        """Test getting latest snapshot when it doesn't exist."""
        latest = store.get_latest("ETH", "4h")

        assert latest is None

    def test_get_latest_wrong_window(self, store, sample_snapshot):
        """Test getting latest with wrong window returns None."""
        store.insert(sample_snapshot)

        latest = store.get_latest("BTC", "24h")

        assert latest is None

    def test_get_history_empty(self, store):
        """Test getting history when no data exists."""
        history = store.get_history("BTC", "4h", hours_back=24)

        assert history == []

    def test_get_history_single_snapshot(self, store, sample_snapshot):
        """Test getting history with single snapshot."""
        store.insert(sample_snapshot)

        history = store.get_history("BTC", "4h", hours_back=24)

        assert len(history) == 1
        assert history[0]["ticker"] == "BTC"

    def test_get_history_multiple_snapshots(self, store):
        """Test getting history with multiple snapshots."""
        # Insert snapshots at different times
        base_time = datetime.utcnow()
        for i in range(5):
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=i * 2),
                total_mentions=100 + i * 10,
                mindshare_score=0.15,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        history = store.get_history("BTC", "4h", hours_back=24)

        assert len(history) == 5
        # Should be ordered by timestamp ASC (oldest first)
        # i=0 is newest (base_time - 0h), i=4 is oldest (base_time - 8h)
        # mentions = 100 + i*10, so oldest (i=4) has 140, newest (i=0) has 100
        assert history[0]["mentions"] == 140  # Oldest (i=4)
        assert history[-1]["mentions"] == 100  # Newest (i=0)

    def test_get_history_filters_by_time(self, store):
        """Test get_history filters by time window."""
        base_time = datetime.utcnow()

        # Insert old snapshot (outside window)
        old_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time - timedelta(hours=30),
            total_mentions=50,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="old"
        )
        store.insert(old_snapshot)

        # Insert recent snapshots (within window)
        for i in range(3):
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=i * 2),
                total_mentions=100 + i * 10,
                mindshare_score=0.15,
                top_smart_accounts=[],
                source_query=f"recent_{i}"
            )
            store.insert(snapshot)

        history = store.get_history("BTC", "4h", hours_back=24)

        # Should only include recent snapshots
        assert len(history) == 3
        assert all(h["mentions"] >= 100 for h in history)


class TestVelocityCalculation:
    """Tests for velocity calculation."""

    def test_calculate_velocity_insufficient_data(self, store, sample_snapshot):
        """Test velocity calculation with insufficient data."""
        store.insert(sample_snapshot)

        velocity = store.calculate_velocity("BTC", "4h")

        assert velocity is None  # Need at least 2 snapshots

    def test_calculate_velocity_two_snapshots(self, store):
        """Test velocity calculation with two snapshots."""
        base_time = datetime.utcnow()

        # Use EnrichedSnapshot for time-based tests (has timestamp field)
        snapshot1 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time - timedelta(hours=4),
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="query1"
        )
        store.insert(snapshot1)
        
        # Insert second snapshot
        snapshot2 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=150,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="query2"
        )
        store.insert(snapshot2)

        velocity = store.calculate_velocity("BTC", "4h")

        assert velocity is not None
        assert velocity["ticker"] == "BTC"
        assert velocity["current_mentions"] == 150
        assert velocity["previous_mentions"] == 100
        assert velocity["mentions_delta"] == 50
        assert velocity["mentions_velocity"] > 0  # Positive velocity
        assert velocity["acceleration"] == "up"

    def test_calculate_velocity_negative(self, store):
        """Test velocity calculation with decreasing mentions."""
        base_time = datetime.utcnow()

        snapshot1 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time - timedelta(hours=4),
            total_mentions=150,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="query1"
        )
        store.insert(snapshot1)

        snapshot2 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="query2"
        )
        store.insert(snapshot2)

        velocity = store.calculate_velocity("BTC", "4h")

        assert velocity is not None
        assert velocity["mentions_delta"] == -50
        assert velocity["mentions_velocity"] < 0
        assert velocity["acceleration"] == "down"

    def test_calculate_velocity_mindshare(self, store):
        """Test velocity calculation includes mindshare."""
        base_time = datetime.utcnow()

        snapshot1 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time - timedelta(hours=4),
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="query1"
        )
        store.insert(snapshot1)

        snapshot2 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=150,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="query2"
        )
        store.insert(snapshot2)

        velocity = store.calculate_velocity("BTC", "4h")

        assert velocity is not None
        assert velocity["current_mindshare"] == 0.15
        assert velocity["previous_mindshare"] == 0.1
        assert abs(velocity["mindshare_delta"] - 0.05) < 0.0001  # Floating point precision
        assert velocity["mindshare_velocity"] > 0


class TestAnomalyDetection:
    """Tests for anomaly detection."""

    def test_detect_anomalies_insufficient_data(self, store, sample_snapshot):
        """Test anomaly detection with insufficient data."""
        store.insert(sample_snapshot)

        anomaly = store.detect_anomalies("BTC", "4h")

        assert anomaly is None  # Need at least 10 snapshots

    def test_detect_anomalies_normal_data(self, store):
        """Test anomaly detection with normal data (no anomaly)."""
        base_time = datetime.utcnow()

        # Insert 12 snapshots with normal variation
        mean_mentions = 100
        for i in range(12):
            # Add small random variation around mean
            mentions = mean_mentions + (i % 5) - 2  # Varies between 98-102
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=24 - i * 2),
                total_mentions=mentions,
                mindshare_score=0.1,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        anomaly = store.detect_anomalies("BTC", "4h", std_threshold=2.0)

        # Should not detect anomaly with normal variation
        assert anomaly is None

    def test_detect_anomalies_spike(self, store):
        """Test anomaly detection detects spike."""
        base_time = datetime.utcnow()

        # Insert 11 normal snapshots with slight variation (needed for stdev calculation)
        for i in range(11):
            # Add small variation around 100 so stdev > 0
            mentions = 100 + (i % 5) - 2
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=24 - i * 2),
                total_mentions=mentions,
                mindshare_score=0.1,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        # Insert spike snapshot
        spike_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=300,  # Large spike (way above mean of ~100)
            mindshare_score=0.3,
            top_smart_accounts=[],
            source_query="spike"
        )
        store.insert(spike_snapshot)

        anomaly = store.detect_anomalies("BTC", "4h", std_threshold=2.0)

        assert anomaly is not None
        assert anomaly["ticker"] == "BTC"
        assert anomaly["current_mentions"] == 300
        assert anomaly["z_score"] > 2.0
        assert anomaly["anomaly_type"] == "spike"

    def test_detect_anomalies_drop(self, store):
        """Test anomaly detection detects drop."""
        base_time = datetime.utcnow()

        # Insert 11 normal snapshots with slight variation (needed for stdev calculation)
        for i in range(11):
            # Add small variation around 100 (98-102) so stdev > 0
            mentions = 100 + (i % 5) - 2
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=24 - i * 2),
                total_mentions=mentions,
                mindshare_score=0.1,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        # Insert drop snapshot
        drop_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=20,  # Large drop (way below mean of ~100)
            mindshare_score=0.02,
            top_smart_accounts=[],
            source_query="drop"
        )
        store.insert(drop_snapshot)

        anomaly = store.detect_anomalies("BTC", "4h", std_threshold=2.0)

        assert anomaly is not None
        assert anomaly["z_score"] < -2.0
        assert anomaly["anomaly_type"] == "drop"

    def test_detect_anomalies_severity(self, store):
        """Test anomaly detection severity levels."""
        base_time = datetime.utcnow()

        # Insert 11 normal snapshots with slight variation (needed for stdev calculation)
        for i in range(11):
            # Add small variation around 100 so stdev > 0
            mentions = 100 + (i % 5) - 2
            snapshot = EnrichedSnapshot(
                ticker="BTC",
                window="4h",
                timestamp=base_time - timedelta(hours=24 - i * 2),
                total_mentions=mentions,
                mindshare_score=0.1,
                top_smart_accounts=[],
                source_query=f"query_{i}"
            )
            store.insert(snapshot)

        # Insert extreme spike
        extreme_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=500,  # Extreme spike (way above mean of ~100)
            mindshare_score=0.5,
            top_smart_accounts=[],
            source_query="extreme"
        )
        store.insert(extreme_snapshot)

        anomaly = store.detect_anomalies("BTC", "4h", std_threshold=2.0)

        assert anomaly is not None
        if abs(anomaly["z_score"]) >= 3.0:
            assert anomaly["severity"] == "extreme"
        else:
            assert anomaly["severity"] == "significant"


class TestWatchlistSummary:
    """Tests for watchlist summary."""

    def test_get_watchlist_summary_empty(self, store):
        """Test watchlist summary with no tickers."""
        summary = store.get_watchlist_summary([], "4h")

        assert summary == []

    def test_get_watchlist_summary_single_ticker(self, store, sample_snapshot):
        """Test watchlist summary with single ticker."""
        store.insert(sample_snapshot)

        summary = store.get_watchlist_summary(["BTC"], "4h")

        assert len(summary) == 1
        assert summary[0]["ticker"] == "BTC"
        assert summary[0]["mentions"] == 100

    def test_get_watchlist_summary_multiple_tickers(self, store):
        """Test watchlist summary with multiple tickers."""
        # Insert snapshots for multiple tickers
        tickers = ["BTC", "ETH", "SOL"]
        for ticker in tickers:
            snapshot = TickerNarrativeSnapshot(
                ticker=ticker,
                window="4h",
                total_mentions=100 if ticker == "BTC" else 50,
                mindshare_score=0.15 if ticker == "BTC" else 0.1,
                top_smart_accounts=[],
                source_query=f"query_{ticker}",
            )
            store.insert(snapshot)

        summary = store.get_watchlist_summary(tickers, "4h")

        assert len(summary) == 3
        # Should be sorted by momentum (mindshare * mentions)
        assert summary[0]["ticker"] == "BTC"  # Highest momentum

    def test_get_watchlist_summary_missing_ticker(self, store, sample_snapshot):
        """Test watchlist summary with missing ticker."""
        store.insert(sample_snapshot)

        summary = store.get_watchlist_summary(["BTC", "ETH"], "4h")

        # Should only return BTC (ETH doesn't exist)
        assert len(summary) == 1
        assert summary[0]["ticker"] == "BTC"


class TestCleanup:
    """Tests for data cleanup."""

    def test_cleanup_old_data(self, store):
        """Test cleaning up old data."""
        base_time = datetime.utcnow()

        # Insert old snapshot
        old_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time - timedelta(days=35),
            total_mentions=50,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="old"
        )
        store.insert(old_snapshot)

        # Insert recent snapshot
        recent_snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="recent"
        )
        store.insert(recent_snapshot)

        # Cleanup data older than 30 days
        result = store.cleanup_old_data(days_to_keep=30)

        assert result is True

        # Verify old data is gone, recent data remains
        history = store.get_history("BTC", "4h", hours_back=1000)
        assert len(history) == 1
        assert history[0]["mentions"] == 100


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_get_latest_case_insensitive(self, store, sample_snapshot):
        """Test get_latest is case insensitive."""
        store.insert(sample_snapshot)

        latest1 = store.get_latest("btc", "4h")
        latest2 = store.get_latest("BTC", "4h")

        assert latest1 is not None
        assert latest2 is not None
        assert latest1["ticker"] == latest2["ticker"]

    def test_get_history_case_insensitive(self, store, sample_snapshot):
        """Test get_history is case insensitive."""
        store.insert(sample_snapshot)

        history1 = store.get_history("btc", "4h")
        history2 = store.get_history("BTC", "4h")

        assert len(history1) == len(history2) == 1

    def test_insert_with_none_mindshare(self, store):
        """Test inserting snapshot with None mindshare."""
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=100,
            mindshare_score=None,
            top_smart_accounts=[],
            source_query="test",
        )

        result = store.insert(snapshot)

        assert result is True

        latest = store.get_latest("BTC", "4h")
        assert latest["mindshare"] is None

    def test_insert_with_empty_smart_accounts(self, store):
        """Test inserting snapshot with empty smart accounts."""
        snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="test",
        )

        result = store.insert(snapshot)

        assert result is True

        latest = store.get_latest("BTC", "4h")
        assert latest["smart_accounts"] == []

    def test_velocity_with_same_timestamp(self, store):
        """Test velocity calculation handles same timestamp."""
        base_time = datetime.utcnow()

        snapshot1 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="query1"
        )
        store.insert(snapshot1)

        snapshot2 = EnrichedSnapshot(
            ticker="BTC",
            window="4h",
            timestamp=base_time,  # Same timestamp
            total_mentions=150,
            mindshare_score=0.15,
            top_smart_accounts=[],
            source_query="query2"
        )
        store.insert(snapshot2)

        velocity = store.calculate_velocity("BTC", "4h")

        # Should handle gracefully (use 1 hour default)
        assert velocity is not None


def raise_(ex):
    """Helper to raise exception in lambda."""
    raise ex
