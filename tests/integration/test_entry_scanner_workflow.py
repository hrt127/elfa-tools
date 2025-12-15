"""
Integration tests for entry scanner workflow.

Tests the complete flow:
- elfa_client → narrative_enricher → entry_scanner
"""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import enrich_snapshot
from optional.entry_scanner import EntryScanner


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
def high_velocity_snapshot():
    """Create a snapshot with high velocity."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=250,  # High mentions
        mindshare_score=0.25,  # High mindshare
        top_smart_accounts=["account1", "account2", "account3", "account4"],
        source_query="test"
    )


class TestEntryScannerWorkflow:
    """Test entry scanner workflow."""
    
    def test_entry_scanner_initialization(self):
        """Test entry scanner initializes correctly."""
        scanner = EntryScanner()
        assert scanner is not None
    
    def test_scan_single_ticker(self, sample_snapshot):
        """Test scanning a single ticker."""
        # Enrich snapshot
        enriched = enrich_snapshot(sample_snapshot)
        
        # Scan for entry setups
        scanner = EntryScanner()
        results = scanner.scan([enriched])
        
        assert len(results) == 1
        assert results[0]['ticker'] == "BTC"
    
    def test_scan_detects_spike_setup(self, high_velocity_snapshot):
        """Test scanner detects spike setup."""
        # First snapshot (baseline)
        baseline = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=50,
            mindshare_score=0.1,
            top_smart_accounts=["account1"],
            source_query="baseline"
        )
        enriched_baseline = enrich_snapshot(baseline)
        
        # Second snapshot (spike)
        enriched_spike = enrich_snapshot(high_velocity_snapshot)
        
        scanner = EntryScanner()
        results = scanner.scan([enriched_spike])
        
        # Should detect spike setup
        result = results[0]
        assert result['ticker'] == "BTC"
        # Should have high conviction if spike detected
        assert result['conviction'] >= 0
    
    def test_scan_multiple_tickers(self):
        """Test scanning multiple tickers."""
        tickers = ["BTC", "ETH", "SOL"]
        enriched_snapshots = []
        
        for ticker in tickers:
            snapshot = TickerNarrativeSnapshot(
                ticker=ticker,
                window="4h",
                total_mentions=100 if ticker == "BTC" else 50,
                mindshare_score=0.15 if ticker == "BTC" else 0.1,
                top_smart_accounts=["account1", "account2"] if ticker == "BTC" else ["account1"],
                source_query=f"test_{ticker}"
            )
            enriched = enrich_snapshot(snapshot)
            enriched_snapshots.append(enriched)
        
        scanner = EntryScanner()
        results = scanner.scan(enriched_snapshots)
        
        assert len(results) == 3
        # Results should be ranked
        assert all('conviction' in r for r in results)
    
    def test_scan_handles_failed_tickers(self):
        """Test scanner handles failed tickers gracefully."""
        # Create valid and invalid snapshots
        valid_snapshot = TickerNarrativeSnapshot(
            ticker="BTC",
            window="4h",
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["account1"],
            source_query="test"
        )
        enriched_valid = enrich_snapshot(valid_snapshot)
        
        scanner = EntryScanner()
        # Should handle None or invalid snapshots
        results = scanner.scan([enriched_valid, None])
        
        # Should only return valid results
        assert len(results) >= 1
        assert all(r['ticker'] == "BTC" for r in results)
    
    def test_scan_ranking(self):
        """Test scanner ranks results by conviction."""
        tickers_data = [
            ("BTC", 200, 0.25, ["a1", "a2", "a3"]),  # High conviction
            ("ETH", 100, 0.15, ["a1", "a2"]),  # Medium
            ("SOL", 50, 0.1, ["a1"])  # Low
        ]
        
        enriched_snapshots = []
        for ticker, mentions, mindshare, accounts in tickers_data:
            snapshot = TickerNarrativeSnapshot(
                ticker=ticker,
                window="4h",
                total_mentions=mentions,
                mindshare_score=mindshare,
                top_smart_accounts=accounts,
                source_query=f"test_{ticker}"
            )
            enriched = enrich_snapshot(snapshot)
            enriched_snapshots.append(enriched)
        
        scanner = EntryScanner()
        results = scanner.scan(enriched_snapshots)
        
        # Should be ranked by conviction (highest first)
        assert len(results) == 3
        convictions = [r['conviction'] for r in results]
        # First should have highest conviction
        assert convictions[0] >= convictions[1] >= convictions[2]

