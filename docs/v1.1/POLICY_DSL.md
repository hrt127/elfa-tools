# Policy Domain-Specific Language (DSL)

**Canonical Reference** — How to configure Decision Moment gating

---

## Policy Configuration Schema

```python
@dataclass
class BoringModeConfig:
    """Configuration for 'boring mode' filtering."""
    min_signals: int = 2                    # Minimum contributing signals
    min_velocity_multiplier: float = 2.0     # Minimum velocity threshold
    require_alignment: bool = True           # Require alignment field
    cooldown_seconds: int = 3600             # Cooldown window (1 hour)
    allow_recurring_patterns: bool = True     # Allow recurring patterns
```

---

## Policy Evaluation Logic

### Step 1: Cooldown Check

```python
def check_cooldown(dm: DecisionMoment, config: BoringModeConfig) -> bool:
    """Check if enough time has passed since last DM for this symbol."""
    last_ts = policy._last_moment.get(dm.symbol)
    if not last_ts:
        return True  # No previous DM, allow
    
    elapsed = (dm.timestamp - last_ts).total_seconds()
    if elapsed < config.cooldown_seconds:
        return False  # BLOCKED: Still in cooldown
    
    return True  # Cooldown expired, allow
```

**Blocking Reason:** `"cooldown_active"`

---

### Step 2: Minimum Signals Check (Boring Mode Only)

```python
def check_min_signals(dm: DecisionMoment, config: BoringModeConfig) -> bool:
    """Check if enough signals are contributing."""
    if not config.boring_mode:
        return True  # Skip if boring mode disabled
    
    if len(dm.signals_contributing) < config.min_signals:
        return False  # BLOCKED: Not enough signals
    
    return True
```

**Blocking Reason:** `"insufficient_signals"`

---

### Step 3: Velocity Multiplier Check (Boring Mode Only)

```python
def check_velocity_multiplier(dm: DecisionMoment, config: BoringModeConfig) -> bool:
    """Check if any signal exceeds minimum velocity multiplier."""
    if not config.boring_mode:
        return True  # Skip if boring mode disabled
    
    multipliers = []
    for signal in dm.signals_contributing:
        if isinstance(signal.value, (int, float)) and isinstance(signal.baseline, (int, float)):
            if signal.baseline != 0:
                multiplier = abs(signal.value / signal.baseline)
                multipliers.append(multiplier)
    
    if not multipliers:
        return False  # BLOCKED: No numeric signals
    
    if max(multipliers) < config.min_velocity_multiplier:
        return False  # BLOCKED: Velocity too low
    
    return True
```

**Blocking Reason:** `"velocity_below_threshold"`

**Example:**
- Signal value: `3.5`, baseline: `1.0` → multiplier: `3.5` ✅ (passes if threshold = 2.0)
- Signal value: `1.5`, baseline: `1.0` → multiplier: `1.5` ❌ (fails if threshold = 2.0)

---

### Step 4: Alignment Requirement (Boring Mode Only)

```python
def check_alignment(dm: DecisionMoment, config: BoringModeConfig) -> bool:
    """Check if alignment field is specified (if required)."""
    if not config.boring_mode:
        return True  # Skip if boring mode disabled
    
    if not config.require_alignment:
        return True  # Skip if alignment not required
    
    if not dm.alignment:
        return False  # BLOCKED: Alignment missing
    
    if dm.alignment.lower() not in ["aligned", "divergent"]:
        return False  # BLOCKED: Invalid alignment value
    
    return True
```

**Blocking Reason:** `"alignment_missing"` or `"alignment_invalid"`

**Valid Alignment Values:**
- `"aligned"` → Signals agree in direction
- `"divergent"` → Signals conflict (still valid, but noted)
- `""` → Not specified (blocks if `require_alignment=True`)

---

### Step 5: Recurring Patterns Check (Boring Mode Only)

```python
def check_recurring_patterns(dm: DecisionMoment, config: BoringModeConfig) -> bool:
    """Check if recurring patterns are allowed."""
    if not config.boring_mode:
        return True  # Skip if boring mode disabled
    
    if config.allow_recurring_patterns:
        return True  # Allow all patterns
    
    if dm.novelty.lower() == "recurring":
        return False  # BLOCKED: Recurring pattern not allowed
    
    return True
```

**Blocking Reason:** `"recurring_pattern_not_allowed"`

**Novelty Values:**
- `"new"` → First time seeing this pattern
- `"recurring"` → Pattern seen before
- `""` → Not specified (always allowed)

---

## Complete Policy Evaluation

```python
def should_trigger(dm: DecisionMoment, policy: DecisionMomentPolicy) -> bool:
    """Complete policy evaluation."""
    
    # Step 1: Cooldown
    if not check_cooldown(dm, policy.config):
        return False, "cooldown_active"
    
    # Step 2-5: Boring mode checks (if enabled)
    if policy.boring_mode:
        if not check_min_signals(dm, policy.config):
            return False, "insufficient_signals"
        
        if not check_velocity_multiplier(dm, policy.config):
            return False, "velocity_below_threshold"
        
        if not check_alignment(dm, policy.config):
            return False, "alignment_missing"
        
        if not check_recurring_patterns(dm, policy.config):
            return False, "recurring_pattern_not_allowed"
    
    # All checks passed
    policy._last_moment[dm.symbol] = dm.timestamp  # Update cooldown
    return True, "allowed"
```

---

## Policy Modes

### Mode: Boring Mode OFF

```python
policy = DecisionMomentPolicy(boring_mode=False)
```

**Behavior:**
- ✅ Only cooldown check enforced
- ✅ All DMs pass (if cooldown expired)
- ✅ Use case: Development, testing, high-frequency monitoring

---

### Mode: Boring Mode ON (Default)

```python
policy = DecisionMomentPolicy(boring_mode=True)
```

**Behavior:**
- ✅ All 5 checks enforced
- ✅ Stricter filtering
- ✅ Use case: Production, attention protection

---

### Mode: Custom Configuration

```python
config = BoringModeConfig(
    min_signals=3,                    # Require 3+ signals
    min_velocity_multiplier=3.0,      # 3x threshold
    require_alignment=True,           # Must have alignment
    cooldown_seconds=7200,            # 2 hour cooldown
    allow_recurring_patterns=False    # Block recurring patterns
)
policy = DecisionMomentPolicy(boring_mode=True, config=config)
```

---

## Policy Examples

### Example 1: High-Frequency Mode

```python
config = BoringModeConfig(
    min_signals=1,                    # Single signal OK
    min_velocity_multiplier=1.5,       # Lower threshold
    require_alignment=False,           # Alignment optional
    cooldown_seconds=300,              # 5 minute cooldown
    allow_recurring_patterns=True      # Allow recurring
)
policy = DecisionMomentPolicy(boring_mode=True, config=config)
```

**Use Case:** Real-time monitoring, low latency requirements

---

### Example 2: Ultra-Strict Mode

```python
config = BoringModeConfig(
    min_signals=4,                    # Require 4+ signals
    min_velocity_multiplier=5.0,      # 5x threshold
    require_alignment=True,           # Must have alignment
    cooldown_seconds=14400,           # 4 hour cooldown
    allow_recurring_patterns=False    # Block recurring
)
policy = DecisionMomentPolicy(boring_mode=True, config=config)
```

**Use Case:** Only surface truly exceptional events

---

### Example 3: Balanced Mode (Default)

```python
config = BoringModeConfig(
    min_signals=2,                    # 2+ signals
    min_velocity_multiplier=2.0,      # 2x threshold
    require_alignment=True,           # Require alignment
    cooldown_seconds=3600,            # 1 hour cooldown
    allow_recurring_patterns=True     # Allow recurring
)
policy = DecisionMomentPolicy(boring_mode=True, config=config)
```

**Use Case:** Production default, balanced attention protection

---

## Policy Override System (Future)

```python
@dataclass
class PolicyOverride:
    """Human override for policy decisions."""
    symbol: str
    override_type: str  # "mute", "downgrade", "force", "adjust_threshold"
    value: Any
    expires_at: Optional[datetime]
    reason: str
```

**Override Types:**
- `"mute"` → Block all DMs for symbol
- `"downgrade"` → Lower conviction threshold
- `"force"` → Generate DM even if policy blocks
- `"adjust_threshold"` → Temporarily change `min_velocity_multiplier`

---

## Policy Metrics

### Metrics to Track

1. **Suppression Rate** → `suppressed_count / total_dm_count`
2. **Average Cooldown Hits** → How often cooldown blocks
3. **Signal Distribution** → Histogram of signal counts
4. **Velocity Multiplier Distribution** → Histogram of multipliers
5. **Alignment Distribution** → Count of aligned vs divergent

### Policy Tuning

**If too many DMs:**
- Increase `min_signals`
- Increase `min_velocity_multiplier`
- Increase `cooldown_seconds`
- Set `allow_recurring_patterns=False`

**If too few DMs:**
- Decrease `min_signals`
- Decrease `min_velocity_multiplier`
- Decrease `cooldown_seconds`
- Set `require_alignment=False`

---

*End of Policy DSL*
