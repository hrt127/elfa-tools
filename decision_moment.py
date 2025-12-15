#!/usr/bin/env python3
"""
Decision Moment System

A Decision Moment is a structured explanation of why now matters.
This module provides the core data structures and policy engine for
surfacing Decision Moments only when they matter.

Design Principles:
- Narrow: Focuses solely on Decision Moment structure and policy
- Explainable: All fields document what changed and why
- Robust: Graceful handling of missing or invalid data
- Composable: Works standalone and integrates with other Elfa tools
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


# -------------------------------
# Signal Evidence
# -------------------------------
@dataclass
class SignalEvidence:
    """
    Evidence from a contributing signal.
    
    Attributes:
        name: Human-readable signal name (e.g., "Narrative Velocity")
        value: Current signal value (float or str)
        baseline: Reference value for comparison (float or str)
        note: Human-readable explanation of what this means
    """
    name: str
    value: float | str
    baseline: float | str
    note: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignalEvidence':
        """Create from dictionary."""
        return cls(**data)


# -------------------------------
# Decision Moment Diff
# -------------------------------
@dataclass
class DecisionMomentDiff:
    """
    Tracks what changed since the last Decision Moment for the same subject.
    
    Attributes:
        since: Timestamp of the previous Decision Moment
        added: List of signal names that appeared
        removed: List of signal names that disappeared
        intensified: List of signal names that strengthened
        weakened: List of signal names that weakened
        interpretation_delta: Human-readable summary of interpretation changes
    """
    since: datetime
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    intensified: List[str] = field(default_factory=list)
    weakened: List[str] = field(default_factory=list)
    interpretation_delta: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['since'] = self.since.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionMomentDiff':
        """Create from dictionary."""
        if isinstance(data.get('since'), str):
            data['since'] = datetime.fromisoformat(data['since'])
        return cls(**data)


# -------------------------------
# Core Decision Moment
# -------------------------------
@dataclass
class DecisionMoment:
    """
    A structured explanation of why now matters.
    
    A Decision Moment surfaces when meaningful change is detected,
    providing context, evidence, and uncertainty to support human judgment.
    
    Attributes:
        id: Unique identifier (e.g., "BTC_20251213_1h")
        timestamp: When this moment was detected
        subject_type: Type of subject (e.g., "ticker", "theme")
        symbol: Subject identifier (e.g., "BTC")
        window: Time window analyzed (e.g., "1h", "4h")
        trigger_description: Human-readable description of what triggered this
        anomaly_type: Type of anomaly detected ("acceleration", "churn", "divergence")
        signals_contributing: Evidence from signals that contributed
        signals_excluded: Evidence from signals that were considered but excluded
        narrative_state: Current narrative state (e.g., "building", "fading")
        alignment: Signal alignment ("aligned", "divergent", "")
        novelty: Pattern novelty ("new", "recurring", "")
        conviction: Confidence level ("low", "medium", "high")
        uncertainty: Human-readable uncertainty description
        interpretation_summary: What this moment means
        interpretation_exclusion: What this moment is NOT
        provenance_sources: List of data sources used
        generated_by: Tool/pipeline that generated this moment
        diff: Optional diff from previous moment
    """
    id: str
    timestamp: datetime
    subject_type: str        # e.g., "ticker", "theme"
    symbol: str              # e.g., "BTC"
    window: str              # e.g., "1h", "4h"

    trigger_description: str
    anomaly_type: str        # "acceleration", "churn", "divergence"

    signals_contributing: List[SignalEvidence] = field(default_factory=list)
    signals_excluded: List[SignalEvidence] = field(default_factory=list)

    narrative_state: str = ""
    alignment: str = ""
    novelty: str = ""

    conviction: str = "medium"      # low, medium, high
    uncertainty: str = ""           # human readable

    interpretation_summary: str = ""
    interpretation_exclusion: str = ""  # what it is not

    provenance_sources: List[str] = field(default_factory=list)
    generated_by: str = ""

    diff: Optional[DecisionMomentDiff] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['signals_contributing'] = [s.to_dict() for s in self.signals_contributing]
        result['signals_excluded'] = [s.to_dict() for s in self.signals_excluded]
        if self.diff:
            result['diff'] = self.diff.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionMoment':
        """Create from dictionary."""
        # Handle timestamp
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Handle signal evidence lists
        if 'signals_contributing' in data:
            data['signals_contributing'] = [
                SignalEvidence.from_dict(s) if isinstance(s, dict) else s
                for s in data['signals_contributing']
            ]
        if 'signals_excluded' in data:
            data['signals_excluded'] = [
                SignalEvidence.from_dict(s) if isinstance(s, dict) else s
                for s in data['signals_excluded']
            ]
        
        # Handle diff
        if data.get('diff'):
            data['diff'] = DecisionMomentDiff.from_dict(data['diff'])
        
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'DecisionMoment':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def explain(self) -> str:
        """
        Generate a human-readable explanation of this Decision Moment.
        
        Returns:
            A formatted explanation string.
        """
        lines = [
            f"Decision Moment: {self.symbol} ({self.window})",
            f"Trigger: {self.trigger_description}",
            f"Anomaly Type: {self.anomaly_type}",
            "",
            "Contributing Signals:",
        ]
        
        for signal in self.signals_contributing:
            lines.append(f"  • {signal.name}: {signal.value} (baseline: {signal.baseline})")
            if signal.note:
                lines.append(f"    {signal.note}")
        
        if self.signals_excluded:
            lines.append("")
            lines.append("Excluded Signals:")
            for signal in self.signals_excluded:
                lines.append(f"  • {signal.name}: {signal.note}")
        
        if self.interpretation_summary:
            lines.append("")
            lines.append(f"Interpretation: {self.interpretation_summary}")
        
        if self.interpretation_exclusion:
            lines.append(f"Not: {self.interpretation_exclusion}")
        
        if self.uncertainty:
            lines.append(f"Uncertainty: {self.uncertainty}")
        
        return "\n".join(lines)


# -------------------------------
# Boring Mode Policy
# -------------------------------
@dataclass
class BoringModeConfig:
    """
    Configuration for "boring mode" - filters out noise to surface only
    meaningful Decision Moments.
    
    Attributes:
        min_signals: Minimum number of contributing signals required
        min_velocity_multiplier: Minimum velocity multiplier threshold
        require_alignment: Whether alignment must be specified
        cooldown_seconds: Minimum seconds between moments for same subject
        allow_recurring_patterns: Whether to allow recurring patterns
    """
    min_signals: int = 2
    min_velocity_multiplier: float = 2.0
    require_alignment: bool = True
    cooldown_seconds: int = 3600
    allow_recurring_patterns: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoringModeConfig':
        """Create from dictionary."""
        return cls(**data)


class DecisionMomentPolicy:
    """
    Policy engine for determining whether a Decision Moment should trigger.
    
    Enforces "boring mode" rules to prevent noise and respect attention.
    Tracks cooldowns per subject to avoid spam.
    
    Usage:
        policy = DecisionMomentPolicy(boring_mode=True)
        if policy.should_trigger(dm):
            # Surface the Decision Moment
            pass
    """
    
    def __init__(self, boring_mode: bool = False, config: BoringModeConfig = None):
        """
        Initialize policy engine.
        
        Args:
            boring_mode: Whether to enforce strict filtering
            config: Configuration for boring mode (uses defaults if None)
        """
        self.boring_mode = boring_mode
        self.config = config or BoringModeConfig()
        # Track last moments per subject to enforce cooldown
        self._last_moment: Dict[str, datetime] = {}

    def should_trigger(self, dm: DecisionMoment) -> bool:
        """
        Determine if a Decision Moment should trigger.
        
        Args:
            dm: The Decision Moment to evaluate
            
        Returns:
            True if the moment should trigger, False otherwise
        """
        if not dm or not dm.symbol:
            return False
        
        # Cooldown check
        last_ts = self._last_moment.get(dm.symbol)
        if last_ts:
            elapsed = (dm.timestamp - last_ts).total_seconds()
            if elapsed < self.config.cooldown_seconds:
                return False

        # Boring mode enforcement
        if self.boring_mode:
            # Minimum signals check
            if len(dm.signals_contributing) < self.config.min_signals:
                return False
            
            # Velocity multiplier check
            multipliers = []
            for signal in dm.signals_contributing:
                if isinstance(signal.value, (int, float)) and isinstance(signal.baseline, (int, float)):
                    if signal.baseline != 0:
                        multiplier = abs(signal.value / signal.baseline)
                        multipliers.append(multiplier)
            
            if multipliers and max(multipliers) < self.config.min_velocity_multiplier:
                return False
            
            # Alignment requirement
            if self.config.require_alignment:
                if not dm.alignment or dm.alignment.lower() not in ["aligned", "divergent"]:
                    return False
            
            # Recurring patterns check
            if not self.config.allow_recurring_patterns:
                if dm.novelty.lower() == "recurring":
                    return False

        # Passed all checks - record timestamp and return True
        self._last_moment[dm.symbol] = dm.timestamp
        return True

    def reset_cooldown(self, symbol: Optional[str] = None):
        """
        Reset cooldown for a symbol (or all symbols).
        
        Args:
            symbol: Symbol to reset, or None to reset all
        """
        if symbol:
            self._last_moment.pop(symbol, None)
        else:
            self._last_moment.clear()

    def get_cooldown_status(self, symbol: str, current_time: datetime) -> Optional[float]:
        """
        Get remaining cooldown seconds for a symbol.
        
        Args:
            symbol: Symbol to check
            current_time: Current timestamp
            
        Returns:
            Remaining seconds, or None if no cooldown
        """
        last_ts = self._last_moment.get(symbol)
        if not last_ts:
            return None
        
        elapsed = (current_time - last_ts).total_seconds()
        remaining = self.config.cooldown_seconds - elapsed
        return max(0, remaining) if remaining > 0 else None


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    # Example Decision Moment
    dm = DecisionMoment(
        id="BTC_20251213_1h",
        timestamp=datetime.utcnow(),
        subject_type="ticker",
        symbol="BTC",
        window="1h",
        trigger_description="Narrative acceleration detected",
        anomaly_type="acceleration",
        signals_contributing=[
            SignalEvidence(
                name="Narrative Velocity",
                value=3.5,
                baseline=1.0,
                note="3.5x vs last hour"
            ),
            SignalEvidence(
                name="Smart Accounts Active",
                value=5,
                baseline=2,
                note="3 new whales"
            )
        ],
        signals_excluded=[
            SignalEvidence(
                name="Retail chatter",
                value=0,
                baseline=10,
                note="No retail spike"
            )
        ],
        narrative_state="building",
        alignment="divergent",
        novelty="new",
        conviction="medium",
        uncertainty="Medium — event-driven",
        interpretation_summary="Attention-worthy anomaly; timing uncertain",
        interpretation_exclusion="Not a trade recommendation",
        provenance_sources=["GET /v2/data/top-mentions?ticker=BTC&timeWindow=1h"],
        generated_by="narrative_radar -> narrative_enricher"
    )

    # Initialize policy
    policy = DecisionMomentPolicy(boring_mode=True)

    # Decide whether to trigger
    if policy.should_trigger(dm):
        print(f"[TRIGGER] Decision Moment: {dm.symbol} | {dm.anomaly_type}")
        print("\n" + dm.explain())
    else:
        print(f"[SUPPRESSED] Decision Moment: {dm.symbol}")
        print("Reason: Did not meet boring mode criteria")
