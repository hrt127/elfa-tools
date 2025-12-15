# 📘 Elfa Narrative OS — Canonical System Description

**Version:** 1.0  
**Last Updated:** 2024-12-13  
**Status:** Canonical Reference

---

## What This System Is

Elfa is a **Narrative Operating System for decision-making under uncertainty**.

It is not:
- ❌ a trading bot
- ❌ a signal oracle
- ❌ a dashboard
- ❌ a prediction machine

It is a **decision pressure system**:
it observes reality, compresses narrative change, applies policy, and *only interrupts humans when something structurally meaningful has changed*.

---

## The Narrative OS Loop (Canonical)

### Unchanging Flow

```
observe
→ enrich
→ decide
→ gate
→ explain
→ interrupt (or not)
```

This loop **never branches**, never skips stages, never short-circuits.

Every module exists to serve **exactly one stage**.

---

## Stage-by-Stage: What Happens, What Talks to What

---

## 1️⃣ OBSERVE — Raw Reality Capture

**Purpose:**  
Capture *what is being said / priced / funded*, without interpretation.

**Inputs:**
- External APIs
- Market data
- On-chain signals
- Narrative surfaces (mentions, themes, velocity)

**Modules:**
- `elfa_client.py` → narrative mentions, themes
- `perp_client.py` → funding, OI, basis
- `onchain_client.py` → optional structural metrics

**Output:**

```python
TickerNarrativeSnapshot(
  ticker="BTC",
  total_mentions=1420,
  mindshare_score=0.15,
  top_smart_accounts=["0x123...", "0x456..."],
  source_query="GET /v2/data/top-mentions?ticker=BTC&timeWindow=1h",
  timestamp=datetime(2024, 12, 13, 10, 0, 0)
)
```

**Rules:**
- ✅ No scoring
- ✅ No opinions
- ✅ No thresholds
- ✅ No alerts
- ✅ If it fails → returns `None`
- ✅ Never raises exceptions

**What Talks to What:**
```
External APIs → elfa_client.py → TickerNarrativeSnapshot
External APIs → perp_client.py → MarketData dict
External APIs → onchain_client.py → OnChainData dict
```

---

## 2️⃣ ENRICH — Time & Memory

**Purpose:**  
Turn raw facts into *change over time*.

**Modules:**
- `narrative_enricher.py` → velocity, acceleration, churn
- `delta_store.py` → historical context, anomaly detection

**What happens:**
- Compare current snapshot vs historical baseline
- Compute:
  - **velocity** (Δ mentions / Δ time)
  - **acceleration** (Δ velocity / Δ time)
  - **churn** (account set differences)
  - **regime deviation** (statistical anomalies)

**Output:**

```python
EnrichedSnapshot(
  ticker="BTC",
  delta_mentions=+85,
  acceleration=+12,
  new_accounts=["0x789..."],
  lost_accounts=["0xabc..."],
  total_mentions=1420,
  mindshare_score=0.15,
  top_smart_accounts=["0x123...", "0x456...", "0x789..."],
  timestamp=datetime(2024, 12, 13, 10, 0, 0),
  source_query="GET /v2/data/top-mentions?ticker=BTC&timeWindow=1h"
)
```

**Rules:**
- ✅ Enrichment can degrade gracefully
- ✅ Partial data is allowed
- ✅ Still no decisions
- ✅ Never raises exceptions

**What Talks to What:**
```
TickerNarrativeSnapshot → narrative_enricher.py → EnrichedSnapshot
EnrichedSnapshot → delta_store.py → Historical context
SQLite (narrative_history.db) → narrative_enricher.py → Previous snapshots
DuckDB (narrative_chronicle.duckdb) → delta_store.py → Velocity/anomaly data
```

---

## 3️⃣ DECIDE — Signal Synthesis (Not Alerts)

**Purpose:**  
Convert enriched context into **candidate pressure**.

This is *not* a trade signal.  
It is a **decision candidate**.

**Module:**
- `signal_composer.py`

**What happens:**
- Combine narrative + market + funding + on-chain
- Produce a **CompositeSignal**
- Calculate confidence based on agreement

**Output:**

```python
CompositeSignal(
  ticker="BTC",
  timestamp=datetime(2024, 12, 13, 10, 0, 0),
  narrative_score=0.82,
  market_score=0.71,
  onchain_score=0.45,
  composite_score=0.68,
  signal_strength=SignalStrength.BULLISH,
  confidence=0.64,
  evidence={
    'Mentions': 1420,
    'Mindshare': '0.15',
    'Smart accounts': 3,
    'Velocity': 85,
    'Funding rate': '0.008%',
    'Price Δ 24h': '+2.5%',
    'Volume ratio': '1.4x'
  },
  warnings=[]
)
```

**Rules:**
- ✅ Multiple signals may exist
- ✅ Weak signals are allowed
- ✅ Nothing fires yet
- ✅ Weight normalization when data sources missing
- ✅ Never raises exceptions

**What Talks to What:**
```
EnrichedSnapshot → signal_composer.py → CompositeSignal
MarketData dict → signal_composer.py → CompositeSignal
OnChainData dict → signal_composer.py → CompositeSignal
```

**Weight Normalization:**
- If all 3 sources: 40% narrative, 35% market, 25% on-chain
- If only narrative + market: ~53% narrative, ~47% market
- If only narrative: 100% narrative
- Weights automatically adjust based on available data

---

## 4️⃣ GATE — Decision Moment Policy Engine

**This is the heart of the system.**

**Module:**
- `decision_moment.py` → `DecisionMomentPolicy`

### What a DecisionMoment Is

A **DecisionMoment** is *permission to interrupt a human*.

Nothing else in the system is allowed to do that.

### DecisionMoment Schema (Canonical)

```python
DecisionMoment(
  id: str,                    # "BTC_20241213_1h"
  timestamp: datetime,
  subject_type: str,          # "ticker", "theme"
  symbol: str,                # "BTC"
  window: str,                # "1h", "4h"
  
  trigger_description: str,    # "Narrative acceleration detected"
  anomaly_type: str,          # "acceleration", "churn", "divergence"
  
  signals_contributing: List[SignalEvidence],
  signals_excluded: List[SignalEvidence],
  
  narrative_state: str,       # "building", "fading"
  alignment: str,             # "aligned", "divergent", ""
  novelty: str,               # "new", "recurring", ""
  
  conviction: str,            # "low", "medium", "high"
  uncertainty: str,           # Human-readable
  
  interpretation_summary: str,
  interpretation_exclusion: str,  # What it is NOT
  
  provenance_sources: List[str],
  generated_by: str,
  
  diff: Optional[DecisionMomentDiff]
)
```

### SignalEvidence Schema

```python
SignalEvidence(
  name: str,                  # "Narrative Velocity"
  value: float | str,         # 3.5
  baseline: float | str,      # 1.0
  note: str                   # "3.5x vs last hour"
)
```

### DecisionMomentDiff Schema

```python
DecisionMomentDiff(
  since: datetime,
  added: List[str],           # Signal names that appeared
  removed: List[str],         # Signal names that disappeared
  intensified: List[str],     # Signal names that strengthened
  weakened: List[str],        # Signal names that weakened
  interpretation_delta: str   # Summary of interpretation changes
)
```

### Policy Layer (Boring Mode Included)

Policies answer:

> "Is this interruption worth human attention?"

**Policy Checks:**
1. **Cooldown** → Has enough time passed since last DM for this symbol?
2. **Minimum Signals** → Are there enough contributing signals?
3. **Velocity Multiplier** → Does any signal exceed minimum threshold?
4. **Alignment** → Is signal alignment specified (if required)?
5. **Recurring Patterns** → Are recurring patterns allowed?

**Boring Mode Effects:**
- Raises thresholds (`min_velocity_multiplier` default: 2.0x)
- Requires multi-factor confirmation (`min_signals` default: 2)
- Extends cooldowns (`cooldown_seconds` default: 3600)
- Biases toward silence

**Policy Decision:**

```python
PolicyDecision(
  allow: bool,               # True if DM should trigger
  reason: str                # Why it was allowed/blocked
)
```

**What Talks to What:**
```
CompositeSignal → decision_moment.py → DecisionMoment (candidate)
DecisionMoment (candidate) → DecisionMomentPolicy.should_trigger() → bool
DecisionMomentPolicy → _last_moment dict → Cooldown tracking
```

---

## 5️⃣ EXPLAIN — Trust Surface

**Module:**
- `DecisionMoment.explain()`

Every DM must render:

```
WHY THIS FIRED
WHAT CHANGED
WHY NOW
WHAT DATA WAS USED
WHAT WAS IGNORED
WHAT THIS IS NOT
```

If explanation fails → DM is invalid.

**Example Output:**

```
Decision Moment: BTC (1h)
Trigger: Narrative acceleration detected
Anomaly Type: acceleration

Contributing Signals:
  • Narrative Velocity: 3.5 (baseline: 1.0)
    3.5x vs last hour
  • Smart Accounts Active: 5 (baseline: 2)
    3 new whales

Excluded Signals:
  • Retail chatter: No retail spike

Interpretation: Attention-worthy anomaly; timing uncertain
Not: Not a trade recommendation
Uncertainty: Medium — event-driven
```

**What Talks to What:**
```
DecisionMoment → explain() → str (human-readable)
```

---

## 6️⃣ INTERRUPT (OR NOT)

**Module:**
- `alerts_engine.py`

Only DecisionMoments with:
- `policy_passed = True` (from `DecisionMomentPolicy.should_trigger()`)
- `confidence >= threshold` (if threshold configured)

may interrupt.

**Delivery channels are irrelevant** — Telegram, Discord, logs, dashboards.

The **DecisionMoment is the product**, not the alert.

**What Talks to What:**
```
DecisionMoment (policy_passed=True) → alerts_engine.py → Alert channels
alerts_engine.py → alert_history.db → Alert persistence
alerts_engine.py → alert_cooldowns table → Cooldown persistence
```

**Alert Rule Structure:**

```python
AlertRule(
  name: str,
  ticker: str,
  condition: Callable[[Dict], bool],
  message_template: str,
  cooldown_minutes: int,
  last_triggered: Optional[datetime]
)
```

**Cooldown Persistence:**
- Stored in `alert_cooldowns` table (SQLite)
- Persists across restarts
- Prevents spam alerts
- Loaded when rule is added

---

## Designed Failed DecisionMoment (BTC Example)

**Scenario:**  
BTC mentions spike +12%, but:
- Velocity is within historical noise
- No theme rotation
- Funding unchanged
- Similar spike occurred yesterday

**Result:**

```python
DecisionMoment(
  id="BTC_20241213_1h",
  trigger_description="Mention spike detected",
  signals_contributing=[
    SignalEvidence(
      name="Mention Count",
      value=1420,
      baseline=1268,
      note="+12% increase"
    )
  ],
  # ... other fields ...
)

# Policy evaluation:
DecisionMomentPolicy.should_trigger(dm) → False
# Blocked by: "delta_below_materiality_threshold"
# OR: "velocity_multiplier < 2.0"
# OR: "cooldown_active"
```

**Why this matters:**  
Silence is a *success state*, not a bug.

---

## One Real BTC DecisionMoment (End-to-End)

### Observation

```python
TickerNarrativeSnapshot(
  ticker="BTC",
  total_mentions=1420,  # ↑ from 580
  mindshare_score=0.15,
  top_smart_accounts=["0x123...", "0x456...", "0x789..."]  # ↑ from 1
)
```

### Enrichment

```python
EnrichedSnapshot(
  ticker="BTC",
  delta_mentions=+840,  # 1420 - 580
  acceleration=+125,     # True acceleration (3+ snapshots)
  new_accounts=["0x456...", "0x789..."],
  lost_accounts=[],
  # Highest velocity in 120 days
)
```

### Decision

```python
CompositeSignal(
  ticker="BTC",
  composite_score=0.81,
  signal_strength=SignalStrength.STRONG_BULLISH,
  confidence=0.81,
  # Multi-surface alignment
)
```

### Gate

```python
DecisionMoment(
  id="BTC_20241213_1h",
  signals_contributing=[
    SignalEvidence(name="Narrative Velocity", value=840, baseline=580, note="+3.8σ"),
    SignalEvidence(name="Smart Accounts", value=3, baseline=1, note="2 new whales"),
    SignalEvidence(name="Theme Rotation", value="ETF", baseline="macro", note="47% shift")
  ],
  # ...
)

# Policy evaluation:
DecisionMomentPolicy.should_trigger(dm) → True
# Passes: materiality, boring mode, cooldown expired
```

### Explain

```
BTC narrative regime shifted from macro-driven to ETF-driven.
This is the largest thematic rotation in 120 days.
Market positioning confirms narrative pressure.
This is not a price prediction.
```

### Interrupt

- Alert sent via configured channels
- Human decides what to do

---

## Human Override Hooks (Explicit)

Humans can:

1. **Mute a ticker** → Skip all DMs for symbol
2. **Downgrade severity** → Lower conviction threshold
3. **Mark false positive** → Log for policy tuning
4. **Force DM for review** → Generate DM even if policy blocks
5. **Change policy mode** → Toggle boring mode, adjust thresholds

**Overrides are:**
- ✅ **Logged** (never silent)
- ✅ **Non-destructive** (do not alter history)
- ✅ **Future-only** (only affect future gating)

**Implementation:**
- Override state stored in `policy_overrides` table (SQLite)
- Checked before policy evaluation
- Logged to `override_log` table

---

## Canonical File & Responsibility Map

```
observe/
  elfa_client.py          → TickerNarrativeSnapshot
  perp_client.py          → MarketData dict
  onchain_client.py       → OnChainData dict

enrich/
  narrative_enricher.py   → EnrichedSnapshot
  delta_store.py          → Historical context, anomalies

decide/
  signal_composer.py      → CompositeSignal

gate/
  decision_moment.py      → DecisionMoment, DecisionMomentPolicy

explain/
  decision_moment.py      → DecisionMoment.explain()

interrupt/
  alerts_engine.py        → Alert delivery, history

storage/
  narrative_history.db    → SQLite (snapshots, velocity)
  narrative_chronicle.duckdb → DuckDB (historical analysis)
  alerts_history.db       → SQLite (alert history, cooldowns)
```

---

## Mental Model (One Sentence)

> Elfa does not tell you what to do.  
> It tells you **when the world has changed enough that *you* should care**.

---

## System Invariants

1. **Never crashes** → All modules return `None` on error, never raise
2. **Never skips stages** → Loop always completes all 6 stages
3. **Never fires without explanation** → Every DM must have `explain()`
4. **Never fires without policy** → Every DM must pass `should_trigger()`
5. **Never alters history** → Overrides only affect future behavior

---

*End of Canonical System Description*
