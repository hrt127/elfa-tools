# The Narrative OS Loop (Canonical)

**The canonical flow for Path B: Decision Engine**

```
observe → enrich → decide → gate → explain → interrupt (or not)
```

---

## Overview

The Narrative OS Loop is the structured process by which raw observations become actionable Decision Moments. It ensures that every interruption is justified, explainable, and respects attention.

---

## The Six Stages

### 1. observe

**Purpose:** Gather raw data from external sources

**Modules:**
- `elfa_client.py` - Narrative data from Elfa API
- `perp_client.py` - Market data from Binance
- `onchain_client.py` - On-chain metrics (template)

**Output:** Raw snapshots
- `TickerNarrativeSnapshot`
- `PerpMarketData`
- `OnChainData`

**Characteristics:**
- Rate limited (60 req/60s)
- Cached (5 min TTL)
- Never crashes (returns None on error)

---

### 2. enrich

**Purpose:** Add temporal context and historical analysis

**Modules:**
- `narrative_enricher.py` - Velocity, acceleration, churn
- `delta_store.py` - Historical analysis, anomalies

**Input:** Raw snapshots from observe stage

**Output:** Enriched snapshots
- `EnrichedSnapshot` (with velocity, acceleration, churn)
- Historical context (velocity trends, anomalies)

**Computation:**
- Velocity: Δ mentions (current - previous)
- Acceleration: Δ velocity (requires 3+ snapshots)
- Churn: Account changes (new/lost accounts)
- Anomalies: Z-score detection

**Storage:**
- SQLite: Snapshot history
- DuckDB: Historical analysis

---

### 3. decide

**Purpose:** Fuse multiple signals into a composite decision

**Module:** `signal_composer.py`

**Input:** Enriched data from multiple sources
- Narrative (mentions, mindshare, velocity, smart accounts)
- Market (funding rate, price momentum, volume)
- On-chain (exchange flows, whale activity, addresses)

**Output:** `CompositeSignal`
- Composite score (-1 to 1)
- Signal strength (STRONG_BULLISH, BULLISH, NEUTRAL, BEARISH, STRONG_BEARISH, CONFLICTED)
- Confidence (0.0 to 1.0)
- Evidence (supporting metrics)
- Warnings (conflicts, extremes)

**Weight Normalization:**
- Automatically adjusts when data sources are missing
- All sources: 40% narrative, 35% market, 25% on-chain
- Missing on-chain: ~53% narrative, ~47% market
- Only narrative: 100% narrative

**Confidence Calculation:**
- High agreement + high magnitude = high confidence
- Mixed signals = low confidence
- Based on directional agreement and variance

---

### 4. gate

**Purpose:** Determine if this moment should interrupt attention

**Module:** `decision_moment.py` (DecisionMomentPolicy)

**Input:** Decision Moment candidate

**Checks:**
- **Cooldown:** Has enough time passed since last moment for this subject?
- **Boring Mode:** Does it meet minimum thresholds?
  - Minimum signals required
  - Velocity multiplier threshold
  - Alignment requirement
  - Recurring patterns (if disabled)

**Output:** `True` (interrupt) or `False` (suppress)

**Policy Configuration:**
```python
BoringModeConfig(
    min_signals=2,
    min_velocity_multiplier=2.0,
    require_alignment=True,
    cooldown_seconds=3600,
    allow_recurring_patterns=True
)
```

**State:**
- Tracks last moment per subject
- Enforces cooldown to prevent spam
- Respects attention (fewer, better interruptions)

---

### 5. explain

**Purpose:** Generate human-readable explanation of why this moment matters

**Module:** `decision_moment.py` (DecisionMoment.explain())

**Input:** Decision Moment

**Output:** Structured explanation
- Trigger description
- Contributing signals (with evidence)
- Excluded signals (what was considered but rejected)
- Interpretation summary
- Interpretation exclusion (what it is NOT)
- Uncertainty description
- Provenance (data sources)

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

Interpretation: Attention-worthy anomaly; timing uncertain
Not: Not a trade recommendation
Uncertainty: Medium — event-driven
```

---

### 6. interrupt (or not)

**Purpose:** Surface the Decision Moment or suppress it

**Modules:**
- `alerts_engine.py` - Rule-based alerts
- `entry_scanner.py` - Entry opportunities
- `pre_trade_check.py` - Trade validation
- `narrative_radar.py` - Multi-ticker scanning
- `narrative_digest.py` - Daily summaries
- `narrative_heatmap.py` - Community visualization

**If Gated (True):**
- Fire alerts through configured channels
- Surface entry opportunities
- Validate trades
- Generate reports
- **Interrupt attention** - User is notified

**If Suppressed (False):**
- No alerts fired
- No interruptions
- Continue monitoring
- **Respect attention** - User is not bothered

---

## Loop Properties

### Iterative
The loop runs continuously (or on-demand). Each iteration builds on previous state stored in databases.

### Stateful
- SQLite tracks snapshot history
- DuckDB enables historical analysis
- Cooldown state persists across restarts
- Cache reduces redundant API calls

### Gated
Not every observation becomes an interruption. The gate stage filters noise and ensures only meaningful moments surface.

### Explainable
Every interruption has a clear explanation. The explain stage provides structured reasoning.

### Robust
The loop continues even if stages fail:
- API failures → Returns None, continues
- Missing data → Normalizes weights, continues
- Database errors → Prints warning, continues
- **Never crashes** - Graceful degradation at every stage

---

## Loop Examples

### Example 1: Narrative Spike Detected

```
1. observe
   └─> elfa_client: BTC mentions = 150 (baseline: 50)

2. enrich
   ├─> narrative_enricher: velocity = +100, acceleration = +50
   └─> delta_store: anomaly detected (z-score = 3.2)

3. decide
   └─> signal_composer: composite_score = +0.65, confidence = 0.85
       └─> STRONG_BULLISH signal

4. gate
   └─> decision_moment_policy.should_trigger()
       ├─> Cooldown: OK (last moment was 2h ago)
       ├─> Signals: 3 contributing (meets min_signals=2)
       ├─> Velocity: 3.5x multiplier (exceeds 2.0 threshold)
       └─> Returns: True (INTERRUPT)

5. explain
   └─> decision_moment.explain()
       └─> "Narrative spike: +100 mentions, 3.5x velocity, 
            statistical anomaly (3.2σ), high confidence (85%)"

6. interrupt
   ├─> alerts_engine: Fire "SPIKE" alert
   ├─> entry_scanner: Surface as "STRONG BUY" opportunity
   └─> User notified via configured channels
```

### Example 2: Routine Update (Suppressed)

```
1. observe
   └─> elfa_client: BTC mentions = 52 (baseline: 50)

2. enrich
   ├─> narrative_enricher: velocity = +2, acceleration = 0
   └─> delta_store: No anomaly (z-score = 0.3)

3. decide
   └─> signal_composer: composite_score = +0.05, confidence = 0.40
       └─> NEUTRAL signal

4. gate
   └─> decision_moment_policy.should_trigger()
       ├─> Signals: 1 contributing (below min_signals=2)
       ├─> Velocity: 1.04x multiplier (below 2.0 threshold)
       └─> Returns: False (SUPPRESS)

5. explain
   └─> (Not generated - suppressed at gate)

6. interrupt
   └─> No alerts, no interruptions
       └─> User not bothered, loop continues
```

---

## Module Mapping

| Stage | Module(s) | Output |
|-------|-----------|--------|
| **observe** | `elfa_client.py`<br>`perp_client.py`<br>`onchain_client.py` | Raw snapshots |
| **enrich** | `narrative_enricher.py`<br>`delta_store.py` | Enriched snapshots |
| **decide** | `signal_composer.py` | CompositeSignal |
| **gate** | `decision_moment.py` (Policy) | Boolean (interrupt/suppress) |
| **explain** | `decision_moment.py` (DecisionMoment) | Explanation string |
| **interrupt** | `alerts_engine.py`<br>`entry_scanner.py`<br>`pre_trade_check.py`<br>Output modules | Alerts, reports, validations |

---

## Design Principles in the Loop

### Narrow
Each stage does one job:
- observe: Fetch data
- enrich: Add context
- decide: Fuse signals
- gate: Filter noise
- explain: Generate reasoning
- interrupt: Surface or suppress

### Explainable
Every stage exposes its reasoning:
- observe: `source_query` field
- enrich: Velocity/acceleration calculations visible
- decide: Evidence and warnings in CompositeSignal
- gate: Policy rules are configurable
- explain: Structured explanation method
- interrupt: Clear alert messages

### Robust
Every stage handles errors gracefully:
- observe: Returns None on API failure
- enrich: Handles missing previous snapshots
- decide: Normalizes weights when data missing
- gate: Returns False on invalid input
- explain: Handles missing fields
- interrupt: Continues even if channels fail

### Composable
Stages can be used independently or together:
- Can run observe + enrich standalone
- Can run decide + gate without interrupt
- Can run explain on any Decision Moment
- Stages compose naturally into the full loop

---

## Loop Configuration

### Boring Mode (Default: Enabled)

Filters out noise to surface only meaningful moments:

```python
policy = DecisionMomentPolicy(
    boring_mode=True,
    config=BoringModeConfig(
        min_signals=2,              # Require 2+ contributing signals
        min_velocity_multiplier=2.0, # Require 2x velocity increase
        require_alignment=True,      # Require alignment specified
        cooldown_seconds=3600,      # 1 hour between moments per subject
        allow_recurring_patterns=True # Allow recurring patterns
    )
)
```

### Relaxed Mode

For more frequent interruptions:

```python
policy = DecisionMomentPolicy(
    boring_mode=False  # No filtering, all moments pass gate
)
```

---

## Integration with Path A

The Narrative OS Loop (Path B) uses Path A (Catalog Tools) as building blocks:

```
Path A (Catalog Tools)          Path B (Narrative OS Loop)
──────────────────────          ──────────────────────────
elfa_client.py          ──┐
perp_client.py          ──┼─> observe
onchain_client.py       ──┘

narrative_enricher.py   ──┐
delta_store.py         ──┼─> enrich
                         └─> decide ──> signal_composer.py
                         └─> gate ────> decision_moment.py
                         └─> explain ─> decision_moment.py
                         └─> interrupt ─> alerts_engine.py
                                          entry_scanner.py
                                          pre_trade_check.py
```

---

## Key Insights

1. **The Loop is Iterative:** Runs continuously, building state over time
2. **The Gate is Critical:** Prevents spam, respects attention
3. **The Explain Stage is Essential:** Every interruption must justify itself
4. **The Loop is Robust:** Continues even when stages fail
5. **The Loop is Composable:** Stages can be used independently

---

## Decision Moment: The Loop's Output

The Decision Moment is the atomic unit produced by the loop:

```python
DecisionMoment(
    # From observe + enrich
    signals_contributing=[...],
    signals_excluded=[...],
    
    # From decide
    conviction="medium",
    uncertainty="Medium — event-driven",
    
    # From gate
    # (policy determines if this surfaces)
    
    # From explain
    interpretation_summary="Attention-worthy anomaly",
    interpretation_exclusion="Not a trade recommendation",
    
    # From interrupt
    # (determines if user is notified)
)
```

**The Decision Moment is where the loop converges.**

---

*The Narrative OS Loop: observe → enrich → decide → gate → explain → interrupt (or not)*
