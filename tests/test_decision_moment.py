"""
Tests for decision_moment.py

Tests cover:
- SignalEvidence creation and serialization
- DecisionMomentDiff creation and serialization
- DecisionMoment creation and serialization
- BoringModeConfig
- DecisionMomentPolicy logic
- Explanation generation
- Edge cases
"""
import pytest
from datetime import datetime, timedelta
from decision_moment import (
    SignalEvidence,
    DecisionMomentDiff,
    DecisionMoment,
    BoringModeConfig,
    DecisionMomentPolicy
)


class TestSignalEvidence:
    """Tests for SignalEvidence dataclass."""
    
    def test_create_signal_evidence(self):
        """Test creating SignalEvidence."""
        evidence = SignalEvidence(
            name="Narrative Velocity",
            value=3.5,
            baseline=1.0,
            note="3.5x vs last hour"
        )
        
        assert evidence.name == "Narrative Velocity"
        assert evidence.value == 3.5
        assert evidence.baseline == 1.0
        assert evidence.note == "3.5x vs last hour"
    
    def test_signal_evidence_to_dict(self):
        """Test SignalEvidence serialization."""
        evidence = SignalEvidence(
            name="Test Signal",
            value=10,
            baseline=5,
            note="Test note"
        )
        
        result = evidence.to_dict()
        assert result["name"] == "Test Signal"
        assert result["value"] == 10
        assert result["baseline"] == 5
        assert result["note"] == "Test note"
    
    def test_signal_evidence_from_dict(self):
        """Test SignalEvidence deserialization."""
        data = {
            "name": "Test Signal",
            "value": 10,
            "baseline": 5,
            "note": "Test note"
        }
        
        evidence = SignalEvidence.from_dict(data)
        assert evidence.name == "Test Signal"
        assert evidence.value == 10
        assert evidence.baseline == 5
        assert evidence.note == "Test note"
    
    def test_signal_evidence_string_value(self):
        """Test SignalEvidence with string value."""
        evidence = SignalEvidence(
            name="Status",
            value="active",
            baseline="inactive",
            note="Changed status"
        )
        
        assert isinstance(evidence.value, str)
        assert evidence.value == "active"


class TestDecisionMomentDiff:
    """Tests for DecisionMomentDiff dataclass."""
    
    def test_create_diff(self):
        """Test creating DecisionMomentDiff."""
        since = datetime.utcnow() - timedelta(hours=1)
        diff = DecisionMomentDiff(
            since=since,
            added=["signal1", "signal2"],
            removed=["signal3"],
            intensified=["signal4"],
            weakened=["signal5"],
            interpretation_delta="Narrative shifted from bearish to bullish"
        )
        
        assert diff.since == since
        assert len(diff.added) == 2
        assert len(diff.removed) == 1
        assert len(diff.intensified) == 1
        assert len(diff.weakened) == 1
    
    def test_diff_to_dict(self):
        """Test DecisionMomentDiff serialization."""
        since = datetime.utcnow()
        diff = DecisionMomentDiff(
            since=since,
            added=["signal1"],
            interpretation_delta="Test delta"
        )
        
        result = diff.to_dict()
        assert result["since"] == since.isoformat()
        assert result["added"] == ["signal1"]
        assert result["interpretation_delta"] == "Test delta"
    
    def test_diff_from_dict(self):
        """Test DecisionMomentDiff deserialization."""
        since = datetime.utcnow()
        data = {
            "since": since.isoformat(),
            "added": ["signal1"],
            "removed": [],
            "intensified": [],
            "weakened": [],
            "interpretation_delta": "Test"
        }
        
        diff = DecisionMomentDiff.from_dict(data)
        assert diff.since == since
        assert diff.added == ["signal1"]


class TestDecisionMoment:
    """Tests for DecisionMoment dataclass."""
    
    def test_create_decision_moment(self):
        """Test creating DecisionMoment."""
        dm = DecisionMoment(
            id="BTC_20251213_1h",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Narrative acceleration detected",
            anomaly_type="acceleration"
        )
        
        assert dm.id == "BTC_20251213_1h"
        assert dm.symbol == "BTC"
        assert dm.window == "1h"
        assert dm.trigger_description == "Narrative acceleration detected"
        assert dm.anomaly_type == "acceleration"
        assert dm.conviction == "medium"  # default
    
    def test_decision_moment_with_signals(self):
        """Test DecisionMoment with contributing signals."""
        signals = [
            SignalEvidence(
                name="Velocity",
                value=3.5,
                baseline=1.0,
                note="3.5x increase"
            )
        ]
        
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=signals
        )
        
        assert len(dm.signals_contributing) == 1
        assert dm.signals_contributing[0].name == "Velocity"
    
    def test_decision_moment_to_dict(self):
        """Test DecisionMoment serialization."""
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        result = dm.to_dict()
        assert result["id"] == "BTC_1"
        assert result["symbol"] == "BTC"
        assert isinstance(result["timestamp"], str)  # ISO format
        assert "signals_contributing" in result
        assert "signals_excluded" in result
    
    def test_decision_moment_from_dict(self):
        """Test DecisionMoment deserialization."""
        timestamp = datetime.utcnow()
        data = {
            "id": "BTC_1",
            "timestamp": timestamp.isoformat(),
            "subject_type": "ticker",
            "symbol": "BTC",
            "window": "1h",
            "trigger_description": "Test",
            "anomaly_type": "acceleration",
            "signals_contributing": [],
            "signals_excluded": [],
            "narrative_state": "",
            "alignment": "",
            "novelty": "",
            "conviction": "medium",
            "uncertainty": "",
            "interpretation_summary": "",
            "interpretation_exclusion": "",
            "provenance_sources": [],
            "generated_by": ""
        }
        
        dm = DecisionMoment.from_dict(data)
        assert dm.id == "BTC_1"
        assert dm.symbol == "BTC"
        assert dm.timestamp == timestamp
    
    def test_decision_moment_to_json(self):
        """Test DecisionMoment JSON serialization."""
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        json_str = dm.to_json()
        assert isinstance(json_str, str)
        assert "BTC_1" in json_str
        assert "BTC" in json_str
    
    def test_decision_moment_from_json(self):
        """Test DecisionMoment JSON deserialization."""
        timestamp = datetime.utcnow()
        json_str = f'''{{
            "id": "BTC_1",
            "timestamp": "{timestamp.isoformat()}",
            "subject_type": "ticker",
            "symbol": "BTC",
            "window": "1h",
            "trigger_description": "Test",
            "anomaly_type": "acceleration",
            "signals_contributing": [],
            "signals_excluded": [],
            "narrative_state": "",
            "alignment": "",
            "novelty": "",
            "conviction": "medium",
            "uncertainty": "",
            "interpretation_summary": "",
            "interpretation_exclusion": "",
            "provenance_sources": [],
            "generated_by": ""
        }}'''
        
        dm = DecisionMoment.from_json(json_str)
        assert dm.id == "BTC_1"
        assert dm.symbol == "BTC"
    
    def test_decision_moment_explain(self):
        """Test DecisionMoment explanation generation."""
        signals = [
            SignalEvidence(
                name="Velocity",
                value=3.5,
                baseline=1.0,
                note="3.5x increase"
            ),
            SignalEvidence(
                name="Smart Accounts",
                value=5,
                baseline=2,
                note="3 new accounts"
            )
        ]
        
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Narrative acceleration",
            anomaly_type="acceleration",
            signals_contributing=signals,
            interpretation_summary="Attention-worthy anomaly",
            interpretation_exclusion="Not a trade recommendation",
            uncertainty="Medium — event-driven"
        )
        
        explanation = dm.explain()
        assert "BTC" in explanation
        assert "Narrative acceleration" in explanation
        assert "Velocity" in explanation
        assert "3.5x increase" in explanation
        assert "Attention-worthy anomaly" in explanation
        assert "Not a trade recommendation" in explanation
    
    def test_decision_moment_explain_with_excluded(self):
        """Test explanation includes excluded signals."""
        excluded = [
            SignalEvidence(
                name="Retail chatter",
                value=0,
                baseline=10,
                note="No retail spike"
            )
        ]
        
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[],
            signals_excluded=excluded
        )
        
        explanation = dm.explain()
        assert "Excluded Signals" in explanation
        assert "Retail chatter" in explanation


class TestBoringModeConfig:
    """Tests for BoringModeConfig."""
    
    def test_default_config(self):
        """Test default BoringModeConfig values."""
        config = BoringModeConfig()
        
        assert config.min_signals == 2
        assert config.min_velocity_multiplier == 2.0
        assert config.require_alignment is True
        assert config.cooldown_seconds == 3600
        assert config.allow_recurring_patterns is True
    
    def test_custom_config(self):
        """Test custom BoringModeConfig."""
        config = BoringModeConfig(
            min_signals=3,
            min_velocity_multiplier=3.0,
            require_alignment=False,
            cooldown_seconds=1800,
            allow_recurring_patterns=False
        )
        
        assert config.min_signals == 3
        assert config.min_velocity_multiplier == 3.0
        assert config.require_alignment is False
        assert config.cooldown_seconds == 1800
        assert config.allow_recurring_patterns is False
    
    def test_config_serialization(self):
        """Test BoringModeConfig serialization."""
        config = BoringModeConfig(min_signals=3)
        result = config.to_dict()
        
        assert result["min_signals"] == 3
        assert result["min_velocity_multiplier"] == 2.0
    
    def test_config_deserialization(self):
        """Test BoringModeConfig deserialization."""
        data = {
            "min_signals": 3,
            "min_velocity_multiplier": 3.0,
            "require_alignment": False,
            "cooldown_seconds": 1800,
            "allow_recurring_patterns": False
        }
        
        config = BoringModeConfig.from_dict(data)
        assert config.min_signals == 3
        assert config.require_alignment is False


class TestDecisionMomentPolicy:
    """Tests for DecisionMomentPolicy."""
    
    def test_policy_without_boring_mode(self):
        """Test policy without boring mode (allows all)."""
        policy = DecisionMomentPolicy(boring_mode=False)
        
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm) is True
    
    def test_policy_boring_mode_min_signals(self):
        """Test boring mode minimum signals requirement."""
        policy = DecisionMomentPolicy(boring_mode=True)
        config = BoringModeConfig(min_signals=2, require_alignment=False)
        policy.config = config
        
        # Not enough signals
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence("Signal1", 1, 0, "test")
            ]
        )
        
        assert policy.should_trigger(dm) is False
        
        # Enough signals
        dm.signals_contributing.append(
            SignalEvidence("Signal2", 2, 1, "test")
        )
        assert policy.should_trigger(dm) is True
    
    def test_policy_boring_mode_velocity_multiplier(self):
        """Test boring mode velocity multiplier requirement."""
        policy = DecisionMomentPolicy(boring_mode=True)
        config = BoringModeConfig(min_velocity_multiplier=2.0, require_alignment=False)
        policy.config = config
        
        # Multiplier too low (max is 2.0x which meets threshold, but test expects False)
        # Actually, max(1.5, 2.0) = 2.0, which meets threshold, so should pass
        # But test expects False, so let's use a case where max is below threshold
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence("Velocity", 1.5, 1.0, "test"),  # 1.5x multiplier
                SignalEvidence("Other", 1.8, 1, "test")  # 1.8x multiplier (both below 2.0)
            ]
        )
        
        assert policy.should_trigger(dm) is False
        
        # Multiplier high enough
        dm.signals_contributing[0] = SignalEvidence("Velocity", 3.0, 1.0, "test")  # 3.0x
        assert policy.should_trigger(dm) is True
    
    def test_policy_boring_mode_require_alignment(self):
        """Test boring mode alignment requirement."""
        policy = DecisionMomentPolicy(boring_mode=True)
        config = BoringModeConfig(require_alignment=True)
        policy.config = config
        
        # No alignment
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence("S1", 1, 0, "test"),
                SignalEvidence("S2", 2, 1, "test")
            ],
            alignment=""  # Empty alignment
        )
        
        assert policy.should_trigger(dm) is False
        
        # With alignment
        dm.alignment = "aligned"
        assert policy.should_trigger(dm) is True
    
    def test_policy_boring_mode_recurring_patterns(self):
        """Test boring mode recurring patterns filter."""
        policy = DecisionMomentPolicy(boring_mode=True)
        config = BoringModeConfig(allow_recurring_patterns=False, require_alignment=False)
        policy.config = config
        
        # Recurring pattern
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence("S1", 1, 0, "test"),
                SignalEvidence("S2", 2, 1, "test")
            ],
            novelty="recurring"
        )
        
        assert policy.should_trigger(dm) is False
        
        # New pattern
        dm.novelty = "new"
        assert policy.should_trigger(dm) is True
    
    def test_policy_cooldown(self):
        """Test policy cooldown enforcement."""
        policy = DecisionMomentPolicy(boring_mode=False)
        config = BoringModeConfig(cooldown_seconds=3600)
        policy.config = config
        
        now = datetime.utcnow()
        
        # First trigger - should pass
        dm1 = DecisionMoment(
            id="BTC_1",
            timestamp=now,
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm1) is True
        
        # Second trigger within cooldown - should fail
        dm2 = DecisionMoment(
            id="BTC_2",
            timestamp=now + timedelta(seconds=1800),  # 30 minutes later
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm2) is False
        
        # Third trigger after cooldown - should pass
        dm3 = DecisionMoment(
            id="BTC_3",
            timestamp=now + timedelta(seconds=3700),  # > 1 hour later
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm3) is True
    
    def test_policy_reset_cooldown(self):
        """Test resetting cooldown."""
        policy = DecisionMomentPolicy(boring_mode=False)
        config = BoringModeConfig(cooldown_seconds=3600)
        policy.config = config
        
        now = datetime.utcnow()
        
        # Trigger once
        dm1 = DecisionMoment(
            id="BTC_1",
            timestamp=now,
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        policy.should_trigger(dm1)
        
        # Reset cooldown
        policy.reset_cooldown("BTC")
        
        # Should be able to trigger again immediately
        dm2 = DecisionMoment(
            id="BTC_2",
            timestamp=now + timedelta(seconds=1),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm2) is True
    
    def test_policy_reset_all_cooldowns(self):
        """Test resetting all cooldowns."""
        policy = DecisionMomentPolicy(boring_mode=False)
        
        now = datetime.utcnow()
        
        # Trigger for multiple symbols
        dm1 = DecisionMoment(
            id="BTC_1",
            timestamp=now,
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        policy.should_trigger(dm1)
        
        dm2 = DecisionMoment(
            id="ETH_1",
            timestamp=now,
            subject_type="ticker",
            symbol="ETH",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        policy.should_trigger(dm2)
        
        # Reset all
        policy.reset_cooldown()
        
        # Both should be able to trigger again
        assert policy.should_trigger(dm1) is True
        assert policy.should_trigger(dm2) is True
    
    def test_policy_get_cooldown_status(self):
        """Test getting cooldown status."""
        policy = DecisionMomentPolicy(boring_mode=False)
        config = BoringModeConfig(cooldown_seconds=3600)
        policy.config = config
        
        now = datetime.utcnow()
        
        # Trigger
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=now,
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        policy.should_trigger(dm)
        
        # Check cooldown status
        remaining = policy.get_cooldown_status("BTC", now + timedelta(seconds=1800))
        assert remaining is not None
        assert remaining > 0
        assert remaining < 3600
        
        # After cooldown expires
        remaining = policy.get_cooldown_status("BTC", now + timedelta(seconds=3700))
        assert remaining is None
    
    def test_policy_invalid_decision_moment(self):
        """Test policy with invalid DecisionMoment."""
        policy = DecisionMomentPolicy(boring_mode=False)
        
        # None DecisionMoment
        assert policy.should_trigger(None) is False
        
        # DecisionMoment without symbol
        dm = DecisionMoment(
            id="test",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="",  # Empty symbol
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration"
        )
        
        assert policy.should_trigger(dm) is False
    
    def test_policy_velocity_multiplier_zero_baseline(self):
        """Test velocity multiplier with zero baseline (should skip)."""
        policy = DecisionMomentPolicy(boring_mode=True)
        config = BoringModeConfig(min_velocity_multiplier=2.0, require_alignment=False)
        policy.config = config
        
        # Signal with zero baseline should be skipped in multiplier check
        dm = DecisionMoment(
            id="BTC_1",
            timestamp=datetime.utcnow(),
            subject_type="ticker",
            symbol="BTC",
            window="1h",
            trigger_description="Test",
            anomaly_type="acceleration",
            signals_contributing=[
                SignalEvidence("Velocity", 10, 0, "test"),  # baseline=0, should skip
                SignalEvidence("Other", 2, 1, "test")  # 2.0x multiplier
            ]
        )
        
        # Should pass because zero baseline signals are skipped
        assert policy.should_trigger(dm) is True

