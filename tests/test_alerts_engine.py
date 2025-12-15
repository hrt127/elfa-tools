"""
Tests for alerts_engine.py

Tests cover:
- Rule triggering
- Cooldown persistence (database)
- Cooldown expiration
- Cooldown loading on rule add
- Data normalization
- Alert history
- Edge cases
"""
import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from optional.alerts_engine import (
    AlertRule,
    AlertsEngine,
    RuleFactory
)
from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def engine(temp_db):
    """Create an AlertsEngine with temporary database."""
    return AlertsEngine(db_path=temp_db)


@pytest.fixture
def sample_snapshot():
    """Create a sample TickerNarrativeSnapshot."""
    return TickerNarrativeSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1", "account2", "account3"],
        source_query="test_query"
    )


@pytest.fixture
def sample_enriched_snapshot():
    """Create a sample EnrichedSnapshot."""
    return EnrichedSnapshot(
        ticker="BTC",
        window="4h",
        total_mentions=100,
        mindshare_score=0.15,
        top_smart_accounts=["account1", "account2"],
        source_query="test_query",
        delta_mentions=25,
        acceleration=5.0,
        new_accounts=["new1"],
        lost_accounts=["lost1"]
    )


class TestAlertRule:
    """Tests for AlertRule dataclass."""
    
    def test_rule_creation(self):
        """Test creating an AlertRule."""
        rule = AlertRule(
            name="test_rule",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker} has {mentions} mentions"
        )
        
        assert rule.name == "test_rule"
        assert rule.ticker == "BTC"
        assert rule.cooldown_minutes == 15  # Default
        assert rule.last_triggered is None
    
    def test_rule_check_condition_met(self):
        """Test rule triggers when condition is met."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker} has {mentions} mentions"
        )
        
        data = {'ticker': 'BTC', 'mentions': 75}
        message = rule.check(data)
        
        assert message is not None
        assert "BTC" in message
        assert "75" in message
        assert rule.last_triggered is not None
    
    def test_rule_check_condition_not_met(self):
        """Test rule doesn't trigger when condition not met."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}"
        )
        
        data = {'ticker': 'BTC', 'mentions': 30}
        message = rule.check(data)
        
        assert message is None
    
    def test_rule_check_cooldown_active(self):
        """Test rule doesn't trigger during cooldown."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}",
            cooldown_minutes=60,
            last_triggered=datetime.now() - timedelta(minutes=30)
        )
        
        data = {'ticker': 'BTC', 'mentions': 75}
        message = rule.check(data)
        
        assert message is None  # Still in cooldown
    
    def test_rule_check_cooldown_expired(self):
        """Test rule triggers after cooldown expires."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}",
            cooldown_minutes=15,
            last_triggered=datetime.now() - timedelta(minutes=20)
        )
        
        data = {'ticker': 'BTC', 'mentions': 75}
        message = rule.check(data)
        
        assert message is not None  # Cooldown expired
    
    def test_rule_check_with_persisted_cooldown(self):
        """Test rule uses persisted cooldown state."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}",
            cooldown_minutes=60
        )
        
        # Simulate persisted cooldown state
        persisted_time = datetime.now() - timedelta(minutes=30)
        
        def get_cooldown(name, ticker):
            if name == "spike" and ticker == "BTC":
                return persisted_time
            return None
        
        data = {'ticker': 'BTC', 'mentions': 75}
        message = rule.check(data, get_cooldown_state=get_cooldown)
        
        assert message is None  # Using persisted cooldown


class TestAlertsEngine:
    """Tests for AlertsEngine class."""
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert len(engine.rules) == 0
        assert len(engine.channels) == 0
        assert engine.db_path is not None
    
    def test_add_rule(self, engine):
        """Test adding a rule."""
        rule = AlertRule(
            name="test",
            ticker="BTC",
            condition=lambda d: True,
            message_template="Test"
        )
        
        engine.add_rule(rule)
        assert len(engine.rules) == 1
        assert engine.rules[0] == rule
    
    def test_add_channel(self, engine):
        """Test adding notification channel."""
        def test_channel(msg):
            pass
        
        engine.add_channel(test_channel)
        assert len(engine.channels) == 1
    
    def test_check_all_rule_triggers(self, engine, sample_snapshot):
        """Test checking alerts triggers rule."""
        triggered_messages = []
        
        def capture_channel(msg):
            triggered_messages.append(msg)
        
        engine.add_channel(capture_channel)
        
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker} has {mentions} mentions"
        )
        engine.add_rule(rule)
        
        engine.check_all("BTC", sample_snapshot)
        
        assert len(triggered_messages) == 1
        assert "BTC" in triggered_messages[0]
        assert "100" in triggered_messages[0]
    
    def test_check_all_wrong_ticker(self, engine, sample_snapshot):
        """Test checking alerts for wrong ticker doesn't trigger."""
        triggered_messages = []
        
        def capture_channel(msg):
            triggered_messages.append(msg)
        
        engine.add_channel(capture_channel)
        
        rule = AlertRule(
            name="spike",
            ticker="ETH",  # Different ticker
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}"
        )
        engine.add_rule(rule)
        
        engine.check_all("BTC", sample_snapshot)
        
        assert len(triggered_messages) == 0
    
    def test_check_all_with_dict_data(self, engine):
        """Test checking alerts with dict data."""
        triggered_messages = []
        
        def capture_channel(msg):
            triggered_messages.append(msg)
        
        engine.add_channel(capture_channel)
        
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}"
        )
        engine.add_rule(rule)
        
        data = {'ticker': 'BTC', 'mentions': 75, 'mindshare': 0.1}
        engine.check_all("BTC", data)
        
        assert len(triggered_messages) == 1
    
    def test_check_all_with_enriched_snapshot(self, engine, sample_enriched_snapshot):
        """Test checking alerts with EnrichedSnapshot."""
        triggered_messages = []
        
        def capture_channel(msg):
            triggered_messages.append(msg)
        
        engine.add_channel(capture_channel)
        
        rule = AlertRule(
            name="velocity",
            ticker="BTC",
            condition=lambda d: d.get('mentions_velocity', 0) > 20,
            message_template="Velocity: {mentions_velocity}"
        )
        engine.add_rule(rule)
        
        engine.check_all("BTC", sample_enriched_snapshot)
        
        assert len(triggered_messages) == 1
        assert "25" in triggered_messages[0]  # delta_mentions = 25
    
    def test_check_all_graceful_error_handling(self, engine):
        """Test engine handles errors gracefully."""
        # Create rule that will cause error
        def bad_condition(d):
            raise ValueError("Test error")
        
        rule = AlertRule(
            name="bad_rule",
            ticker="BTC",
            condition=bad_condition,
            message_template="Test"
        )
        engine.add_rule(rule)
        
        # Should not raise exception
        data = {'ticker': 'BTC', 'mentions': 75}
        engine.check_all("BTC", data)  # Should handle error gracefully
    
    def test_alert_persistence(self, engine, sample_snapshot):
        """Test alerts are persisted to database."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}"
        )
        engine.add_rule(rule)
        
        engine.check_all("BTC", sample_snapshot)
        
        # Check database
        history = engine.get_history()
        assert len(history) == 1
        assert history[0]['rule'] == "spike"
        assert history[0]['ticker'] == "BTC"
    
    def test_get_history_filtered_by_ticker(self, engine, sample_snapshot):
        """Test getting alert history filtered by ticker."""
        # Add rules for multiple tickers
        rule1 = AlertRule(
            name="btc_spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="BTC alert"
        )
        rule2 = AlertRule(
            name="eth_spike",
            ticker="ETH",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="ETH alert"
        )
        
        engine.add_rule(rule1)
        engine.add_rule(rule2)
        
        # Trigger BTC alert
        engine.check_all("BTC", sample_snapshot)
        
        # Trigger ETH alert with different data
        eth_snapshot = TickerNarrativeSnapshot(
            ticker="ETH",
            window="4h",
            total_mentions=100,
            mindshare_score=0.1,
            top_smart_accounts=[],
            source_query="test"
        )
        engine.check_all("ETH", eth_snapshot)
        
        # Get history filtered by ticker
        btc_history = engine.get_history(ticker="BTC")
        assert len(btc_history) == 1
        assert btc_history[0]['ticker'] == "BTC"
        
        eth_history = engine.get_history(ticker="ETH")
        assert len(eth_history) == 1
        assert eth_history[0]['ticker'] == "ETH"
    
    def test_cooldown_persistence(self, engine, sample_snapshot):
        """Test cooldown state persists across engine instances."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}",
            cooldown_minutes=60
        )
        engine.add_rule(rule)
        
        # Trigger alert
        engine.check_all("BTC", sample_snapshot)
        
        # Create new engine instance with same database
        engine2 = AlertsEngine(db_path=engine.db_path)
        engine2.add_rule(rule)
        
        # Try to trigger again - should be in cooldown
        triggered_messages = []
        def capture_channel(msg):
            triggered_messages.append(msg)
        engine2.add_channel(capture_channel)
        
        engine2.check_all("BTC", sample_snapshot)
        
        # Should not trigger due to cooldown
        assert len(triggered_messages) == 0
    
    def test_cooldown_expires(self, engine, sample_snapshot):
        """Test cooldown expires and rule can trigger again."""
        rule = AlertRule(
            name="spike",
            ticker="BTC",
            condition=lambda d: d.get('mentions', 0) > 50,
            message_template="Alert: {ticker}",
            cooldown_minutes=1  # Short cooldown for testing
        )
        engine.add_rule(rule)
        
        # Trigger first alert
        engine.check_all("BTC", sample_snapshot)
        
        # Manually expire cooldown in database
        conn = sqlite3.connect(engine.db_path)
        expired_time = (datetime.now() - timedelta(minutes=2)).isoformat()
        conn.execute("""
            UPDATE alert_cooldowns
            SET last_triggered = ?
            WHERE rule_name = ? AND ticker = ?
        """, (expired_time, "spike", "BTC"))
        conn.commit()
        conn.close()
        
        # Create new engine and try again
        engine2 = AlertsEngine(db_path=engine.db_path)
        triggered_messages = []
        def capture_channel(msg):
            triggered_messages.append(msg)
        engine2.add_channel(capture_channel)
        engine2.add_rule(rule)
        
        engine2.check_all("BTC", sample_snapshot)
        
        # Should trigger again after cooldown expired
        assert len(triggered_messages) == 1


class TestRuleFactory:
    """Tests for RuleFactory pre-built rules."""
    
    def test_spike_detector(self):
        """Test spike detector rule."""
        rule = RuleFactory.spike_detector("BTC", threshold=50)
        
        assert rule.name == "BTC_spike"
        assert rule.ticker == "BTC"
        assert rule.cooldown_minutes == 30
        
        # Test condition
        data_high = {'mentions': 75}
        data_low = {'mentions': 30}
        
        assert rule.condition(data_high) is True
        assert rule.condition(data_low) is False
    
    def test_velocity_alert(self):
        """Test velocity alert rule."""
        rule = RuleFactory.velocity_alert("BTC", velocity_threshold=10.0)
        
        assert rule.name == "BTC_velocity"
        
        # Test condition
        data_high = {'mentions_velocity': 15.0}
        data_low = {'mentions_velocity': 5.0}
        
        assert rule.condition(data_high) is True
        assert rule.condition(data_low) is False
    
    def test_smart_money_alert(self):
        """Test smart money alert rule."""
        rule = RuleFactory.smart_money_alert("BTC", min_accounts=3)
        
        assert rule.name == "BTC_smart_money"
        
        # Test condition
        data_high = {'smart_accounts': ['a1', 'a2', 'a3', 'a4']}
        data_low = {'smart_accounts': ['a1', 'a2']}
        
        assert rule.condition(data_high) is True
        assert rule.condition(data_low) is False
    
    def test_mindshare_threshold(self):
        """Test mindshare threshold rule."""
        rule = RuleFactory.mindshare_threshold("BTC", threshold=0.1)
        
        assert rule.name == "BTC_mindshare"
        
        # Test condition
        data_high = {'mindshare': 0.15}
        data_low = {'mindshare': 0.05}
        
        assert rule.condition(data_high) is True
        assert rule.condition(data_low) is False
    
    def test_anomaly_alert(self):
        """Test anomaly alert rule."""
        rule = RuleFactory.anomaly_alert("BTC")
        
        assert rule.name == "BTC_anomaly"
        
        # Test condition
        data_anomaly = {'z_score': 2.5}
        data_normal = {'z_score': 1.0}
        data_no_zscore = {}
        
        assert rule.condition(data_anomaly) is True
        assert rule.condition(data_normal) is False
        assert rule.condition(data_no_zscore) is False


class TestDataNormalization:
    """Tests for data normalization."""
    
    def test_normalize_ticker_narrative_snapshot(self, engine, sample_snapshot):
        """Test normalizing TickerNarrativeSnapshot."""
        data = engine._normalize_data(sample_snapshot)
        
        assert data is not None
        assert data['ticker'] == "BTC"
        assert data['mentions'] == 100
        assert data['mindshare'] == 0.15
        assert data['smart_accounts_count'] == 3
        assert data['mentions_velocity'] == 0  # Not in TickerNarrativeSnapshot
    
    def test_normalize_enriched_snapshot(self, engine, sample_enriched_snapshot):
        """Test normalizing EnrichedSnapshot."""
        data = engine._normalize_data(sample_enriched_snapshot)
        
        assert data is not None
        assert data['ticker'] == "BTC"
        assert data['mentions'] == 100
        assert data['mentions_velocity'] == 25  # delta_mentions
        assert data['acceleration'] == 5.0
    
    def test_normalize_dict(self, engine):
        """Test normalizing dict data."""
        data_dict = {'ticker': 'BTC', 'mentions': 75}
        result = engine._normalize_data(data_dict)
        
        assert result == data_dict
    
    def test_normalize_unsupported_type(self, engine):
        """Test normalizing unsupported type returns None."""
        result = engine._normalize_data("not a valid type")
        
        assert result is None
    
    def test_normalize_handles_errors(self, engine):
        """Test normalization handles errors gracefully."""
        # Create a mock object that will cause error
        bad_obj = Mock()
        bad_obj.ticker = property(lambda self: raise_(AttributeError("test")))
        
        result = engine._normalize_data(bad_obj)
        
        assert result is None


def raise_(ex):
    """Helper to raise exception in lambda."""
    raise ex

