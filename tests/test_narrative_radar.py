"""
Tests for narrative_radar.py

Tests cover:
- Formatting functions (format_number, format_percentage, indicators)
- CLI display functionality
- Markdown export functionality
- Main CLI argument parsing
- Error handling
- Edge cases
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
from io import StringIO

from narrative_radar import (
    format_number,
    format_percentage,
    get_velocity_indicator,
    get_acceleration_indicator,
    display_cli_radar,
    export_markdown,
    main
)
from narrative_enricher import EnrichedSnapshot


class TestFormattingFunctions:
    """Tests for formatting utility functions."""
    
    def test_format_number_positive(self):
        """Test formatting positive numbers."""
        assert format_number(5) == "+5"
        assert format_number(0) == "0"  # Zero is formatted as "0", not "+0"
        assert format_number(100) == "+100"
    
    def test_format_number_negative(self):
        """Test formatting negative numbers."""
        assert format_number(-5) == "-5"
        assert format_number(-100) == "-100"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(50, 100) == "+50.0%"
        assert format_percentage(25, 100) == "+25.0%"
        assert format_percentage(0, 100) == "+0.0%"
        assert format_percentage(100, 0) == "N/A"
    
    def test_format_percentage_negative(self):
        """Test negative percentage formatting."""
        assert format_percentage(-10, 100) == "-10.0%"


class TestVelocityIndicators:
    """Tests for velocity indicator logic."""
    
    def test_velocity_indicator_strong_upward(self):
        """Test strong upward momentum indicators."""
        assert get_velocity_indicator(15) == "🚀"  # > 10
        assert get_velocity_indicator(11) == "🚀"
    
    def test_velocity_indicator_moderate_upward(self):
        """Test moderate upward indicators."""
        assert get_velocity_indicator(8) == "📈"  # > 5, <= 10
        assert get_velocity_indicator(6) == "📈"
    
    def test_velocity_indicator_slight_upward(self):
        """Test slight upward indicators."""
        assert get_velocity_indicator(3) == "↗️"  # > 0, <= 5
        assert get_velocity_indicator(1) == "↗️"
    
    def test_velocity_indicator_stable(self):
        """Test stable indicator."""
        assert get_velocity_indicator(0) == "➡️"
    
    def test_velocity_indicator_slight_downward(self):
        """Test slight downward indicators."""
        assert get_velocity_indicator(-3) == "↘️"  # > -5, < 0
        assert get_velocity_indicator(-1) == "↘️"
    
    def test_velocity_indicator_moderate_downward(self):
        """Test moderate downward indicators."""
        assert get_velocity_indicator(-8) == "📉"  # > -10, <= -5
        assert get_velocity_indicator(-6) == "📉"
    
    def test_velocity_indicator_strong_downward(self):
        """Test strong downward indicators."""
        assert get_velocity_indicator(-15) == "💥"  # <= -10
        assert get_velocity_indicator(-11) == "💥"


class TestAccelerationIndicators:
    """Tests for acceleration indicator logic."""
    
    def test_acceleration_indicator_none(self):
        """Test None acceleration (insufficient data)."""
        assert get_acceleration_indicator(None) == "➡️"
    
    def test_acceleration_indicator_strong_positive(self):
        """Test strong positive acceleration."""
        assert get_acceleration_indicator(8) == "⚡"  # > 5
        assert get_acceleration_indicator(10) == "⚡"
    
    def test_acceleration_indicator_positive(self):
        """Test positive acceleration."""
        assert get_acceleration_indicator(3) == "🔺"  # > 0, <= 5
        assert get_acceleration_indicator(1) == "🔺"
    
    def test_acceleration_indicator_stable(self):
        """Test stable acceleration."""
        assert get_acceleration_indicator(0) == "➡️"
    
    def test_acceleration_indicator_negative(self):
        """Test negative acceleration."""
        assert get_acceleration_indicator(-3) == "🔻"  # > -5, < 0
        assert get_acceleration_indicator(-1) == "🔻"
    
    def test_acceleration_indicator_strong_negative(self):
        """Test strong negative acceleration."""
        assert get_acceleration_indicator(-8) == "⚡"  # <= -5
        assert get_acceleration_indicator(-10) == "⚡"


class TestDisplayCLIRadar:
    """Tests for CLI display functionality."""
    
    def test_display_empty_list(self, capsys):
        """Test display with empty snapshot list."""
        display_cli_radar([], "1h")
        captured = capsys.readouterr()
        assert "No data available" in captured.out
    
    def test_display_single_ticker(self, sample_enriched_snapshot, capsys):
        """Test display with single ticker."""
        display_cli_radar([sample_enriched_snapshot], "4h")
        captured = capsys.readouterr()
        
        assert "NARRATIVE RADAR" in captured.out
        assert "4H WINDOW" in captured.out
        assert "BTC" in captured.out
        assert "120" in captured.out  # total_mentions
        assert "ACCOUNT CHURN DETAILS" in captured.out
    
    def test_display_multiple_tickers(self, capsys):
        """Test display with multiple tickers."""
        snapshots = [
            EnrichedSnapshot(
                ticker="BTC",
                window="1h",
                timestamp=datetime.utcnow(),
                total_mentions=150,
                mindshare_score=0.20,
                top_smart_accounts=["acc1", "acc2"],
                delta_mentions=25,
                acceleration=5,
                new_accounts=["acc3"],
                lost_accounts=[],
                source_query="test"
            ),
            EnrichedSnapshot(
                ticker="ETH",
                window="1h",
                timestamp=datetime.utcnow(),
                total_mentions=100,
                mindshare_score=0.15,
                top_smart_accounts=["acc4"],
                delta_mentions=-5,
                acceleration=-2,
                new_accounts=[],
                lost_accounts=["acc5"],
                source_query="test"
            )
        ]
        
        display_cli_radar(snapshots, "1h")
        captured = capsys.readouterr()
        
        assert "BTC" in captured.out
        assert "ETH" in captured.out
        assert "150" in captured.out
        assert "100" in captured.out
        # Should be sorted by mentions (BTC first)
        assert captured.out.find("BTC") < captured.out.find("ETH")
    
    def test_display_account_churn(self, capsys):
        """Test account churn details display."""
        snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["acc1", "acc2"],
            delta_mentions=10,
            acceleration=2,
            new_accounts=["acc3", "acc4"],
            lost_accounts=["acc5"],
            source_query="test"
        )
        
        display_cli_radar([snapshot], "1h")
        captured = capsys.readouterr()
        
        assert "New accounts" in captured.out
        assert "Lost accounts" in captured.out
        assert "acc3" in captured.out
        assert "acc4" in captured.out
        assert "acc5" in captured.out


class TestExportMarkdown:
    """Tests for markdown export functionality."""
    
    def test_export_single_ticker(self, sample_enriched_snapshot, tmp_path):
        """Test markdown export with single ticker."""
        output_path = tmp_path / "test_report.md"
        
        export_markdown([sample_enriched_snapshot], "4h", output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        
        assert "# Narrative Radar" in content
        assert "4H Window" in content  # Title case, not uppercase
        assert "BTC" in content
        assert "120" in content
        assert "## Summary" in content
        assert "## Detailed Analysis" in content
        assert "### BTC" in content
    
    def test_export_multiple_tickers(self, tmp_path):
        """Test markdown export with multiple tickers."""
        snapshots = [
            EnrichedSnapshot(
                ticker="BTC",
                window="1h",
                timestamp=datetime.utcnow(),
                total_mentions=150,
                mindshare_score=0.20,
                top_smart_accounts=["acc1"],
                delta_mentions=25,
                acceleration=5,
                new_accounts=["acc2"],
                lost_accounts=[],
                source_query="test"
            ),
            EnrichedSnapshot(
                ticker="ETH",
                window="1h",
                timestamp=datetime.utcnow(),
                total_mentions=100,
                mindshare_score=0.15,
                top_smart_accounts=["acc3"],
                delta_mentions=-5,
                acceleration=-2,
                new_accounts=[],
                lost_accounts=["acc4"],
                source_query="test"
            )
        ]
        
        output_path = tmp_path / "test_report.md"
        export_markdown(snapshots, "1h", output_path)
        
        content = output_path.read_text()
        assert "BTC" in content
        assert "ETH" in content
        assert "150" in content
        assert "100" in content
        assert "### BTC" in content
        assert "### ETH" in content
    
    def test_export_with_source_query(self, tmp_path):
        """Test markdown export includes source query."""
        snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="GET /v2/data/top-mentions?ticker=BTC"
        )
        
        output_path = tmp_path / "test_report.md"
        export_markdown([snapshot], "1h", output_path)
        
        content = output_path.read_text()
        assert "Source Query" in content
        assert "top-mentions" in content
    
    def test_export_with_none_acceleration(self, tmp_path):
        """Test markdown export handles None acceleration."""
        snapshot = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=None,  # None acceleration
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        
        output_path = tmp_path / "test_report.md"
        export_markdown([snapshot], "1h", output_path)
        
        content = output_path.read_text()
        assert "N/A" in content  # Should show N/A for acceleration


class TestMainCLI:
    """Tests for main CLI function."""
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    @patch('narrative_radar.display_cli_radar')
    def test_main_single_ticker_success(
        self, mock_display, mock_enricher_class, mock_get_snapshot, sample_ticker_snapshot
    ):
        """Test main with single successful ticker."""
        # Setup mocks
        mock_get_snapshot.return_value = sample_ticker_snapshot
        mock_enricher = Mock()
        mock_enricher.enrich_snapshot.return_value = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=["acc1"],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        mock_enricher_class.return_value = mock_enricher
        
        # Test
        with patch('sys.argv', ['narrative_radar.py', 'BTC', '--window', '1h']):
            main()
        
        # Verify
        mock_get_snapshot.assert_called_once_with("BTC", window="1h", use_cache=True)
        mock_enricher.enrich_snapshot.assert_called_once()
        mock_display.assert_called_once()
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    @patch('narrative_radar.display_cli_radar')
    @patch('narrative_radar.export_markdown')
    def test_main_with_export(
        self, mock_export, mock_display, mock_enricher_class, mock_get_snapshot,
        sample_ticker_snapshot, tmp_path
    ):
        """Test main with markdown export."""
        # Setup mocks
        mock_get_snapshot.return_value = sample_ticker_snapshot
        mock_enricher = Mock()
        mock_enricher.enrich_snapshot.return_value = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        mock_enricher_class.return_value = mock_enricher
        
        output_path = tmp_path / "test_export.md"
        
        # Test
        with patch('sys.argv', [
            'narrative_radar.py', 'BTC', '--window', '1h', '--export', str(output_path)
        ]):
            main()
        
        # Verify
        mock_display.assert_called_once()
        mock_export.assert_called_once()
        # Don't check file existence when export_markdown is mocked
        # The mock doesn't actually create the file
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    def test_main_no_cache_flag(
        self, mock_enricher_class, mock_get_snapshot, sample_ticker_snapshot
    ):
        """Test main with --no-cache flag."""
        mock_get_snapshot.return_value = sample_ticker_snapshot
        mock_enricher = Mock()
        mock_enricher.enrich_snapshot.return_value = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        mock_enricher_class.return_value = mock_enricher
        
        with patch('sys.argv', ['narrative_radar.py', 'BTC', '--no-cache']):
            main()
        
        # Verify use_cache=False was passed
        mock_get_snapshot.assert_called_once_with("BTC", window="1h", use_cache=False)
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    def test_main_failed_ticker(self, mock_enricher_class, mock_get_snapshot, capsys):
        """Test main with failed ticker fetch."""
        mock_get_snapshot.return_value = None  # Failed fetch
        mock_enricher_class.return_value = Mock()
        
        with patch('sys.argv', ['narrative_radar.py', 'INVALID', '--window', '1h']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Failed to fetch data" in captured.out or "No data available" in captured.out
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    def test_main_multiple_tickers_partial_failure(
        self, mock_enricher_class, mock_get_snapshot, sample_ticker_snapshot, capsys
    ):
        """Test main with multiple tickers, some failing."""
        def side_effect(ticker, **kwargs):
            if ticker == "BTC":
                return sample_ticker_snapshot
            return None  # ETH fails
        
        mock_get_snapshot.side_effect = side_effect
        mock_enricher = Mock()
        mock_enricher.enrich_snapshot.return_value = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        mock_enricher_class.return_value = mock_enricher
        
        with patch('sys.argv', ['narrative_radar.py', 'BTC', 'ETH', '--window', '1h']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should exit with error due to failed ticker
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "ETH" in captured.out or "Failed" in captured.out
    
    @patch('narrative_radar.get_ticker_narrative_snapshot')
    @patch('narrative_radar.NarrativeEnricher')
    def test_main_default_window(self, mock_enricher_class, mock_get_snapshot, sample_ticker_snapshot):
        """Test main uses default window when not specified."""
        mock_get_snapshot.return_value = sample_ticker_snapshot
        mock_enricher = Mock()
        mock_enricher.enrich_snapshot.return_value = EnrichedSnapshot(
            ticker="BTC",
            window="1h",
            timestamp=datetime.utcnow(),
            total_mentions=100,
            mindshare_score=0.15,
            top_smart_accounts=[],
            delta_mentions=10,
            acceleration=2,
            new_accounts=[],
            lost_accounts=[],
            source_query="test"
        )
        mock_enricher_class.return_value = mock_enricher
        
        with patch('sys.argv', ['narrative_radar.py', 'BTC']):
            main()
        
        # Should use default window "1h"
        mock_get_snapshot.assert_called_once_with("BTC", window="1h", use_cache=True)

