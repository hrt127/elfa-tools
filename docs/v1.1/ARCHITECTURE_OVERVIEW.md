# Elfa Tools - Architecture Overview

## The Two-Path Model: From Lego Bricks to The Castle

---

## Conceptual Architecture

```text
                 ┌─────────────────────────────┐
                 │   Path A: Catalog Tools     │
                 │  ("Lego Bricks" – Immediate │
                 │   Utility, Narrow Modules)  │
                 └───────────────┬─────────────┘
                                 │
   ┌─────────────────────────────┼─────────────────────────────┐
   │                             │                             │
   ▼                             ▼                             ▼
elfa_client.py          narrative_enricher.py          perp_client.py
(on-chain template)      (velocity, accel, churn)       (funding, price, volume)
   │                             │                             │
   └───────────────┬─────────────┼─────────────┬───────────────┘
                   ▼             ▼             ▼
             delta_store.py   narrative_radar.py   narrative_heatmap.py
             (history,        (multi-ticker scan)  (community overlap)
              anomalies)
                   │
                   ▼
          ┌─────────────────────────────┐
          │ Path B: Narrative OS Loop   │
          │ (observe → enrich → decide  │
          │  → gate → explain →         │
          │  interrupt (or not))        │
          └───────────────┬─────────────┘
                          │
                          ▼
                 observe (API clients)
                          │
                          ▼
                 enrich (enricher, store)
                          │
                          ▼
                 decide (signal_composer)
                          │
                          ▼
                 gate (decision_moment policy)
                          │
                          ▼
                 explain (decision_moment)
                          │
                          ▼
          ┌─────────────────────────────┐
          │      Decision Moment        │
          │  (Atomic Unit: Why Now      │
          │   Matters, Explainable,     │
          │   Structured, Robust)       │
          └───────────────┬─────────────┘
                          │
                          ▼
                 interrupt (or not)
                 (alerts, scanner, check)
                          │
                          ▼
          ┌─────────────────────────────┐
          │ Outputs:                    │
          │ • Alerts (console, Discord) │
          │ • Digest (daily reports)    │
          │ • Heatmap (structural edges)│
          │ • Pre-trade checks          │
          │ • Entry scanner             │
          └─────────────────────────────┘
```

---

## Path A: Catalog Tools ("Lego Bricks")

**Philosophy:** Immediate utility, narrow modules that do one job well.

### Core Modules

#### 1. **elfa_client.py**

- **Purpose:** Fetch narrative data from Elfa API
- **Output:** `TickerNarrativeSnapshot`
- **Features:**
  - Rate limiting (60 req/60s)
  - Caching (5 min TTL)
  - Graceful error handling
  - Audit trails (`source_query`)

#### 2. **narrative_enricher.py**

- **Purpose:** Compute temporal metrics (velocity, acceleration, churn)
- **Input:** `TickerNarrativeSnapshot`
- **Output:** `EnrichedSnapshot`
- **Features:**
  - SQLite persistence
  - Velocity calculation (Δ mentions)
  - Acceleration calculation (Δ velocity, requires 3+ snapshots)
  - Account churn detection

#### 3. **perp_client.py**

- **Purpose:** Fetch perpetual futures market data
- **Output:** `PerpMarketData`
- **Features:**
  - Binance API integration
  - Funding rate, price, volume
  - Rate limiting & caching

#### 4. **delta_store.py**

- **Purpose:** Historical analysis and anomaly detection
- **Storage:** DuckDB
- **Features:**
  - Velocity calculation (time-based)
  - Anomaly detection (Z-score)
  - Historical queries
  - Watchlist summaries

#### 5. **narrative_radar.py**

- **Purpose:** Multi-ticker scanning and visualization
- **Output:** CLI table or markdown export
- **Features:**
  - Batch processing
  - Visual indicators (🚀, 📈, etc.)
  - Account churn details

#### 6. **narrative_heatmap.py**

- **Purpose:** Community overlap visualization
- **Output:** PNG images or markdown tables
- **Features:**
  - Jaccard similarity
  - Velocity correlation
  - Mindshare similarity

---

## Path B: The Narrative OS Loop (Canonical)

**Canonical Flow:** `observe → enrich → decide → gate → explain → interrupt (or not)`

**Philosophy:** Composable fusion, trust, explainability - where signals become decisions through a structured loop.

> **See also:** [NARRATIVE_OS_LOOP.md](./NARRATIVE_OS_LOOP.md) for detailed loop documentation

### The Narrative OS Loop Stages

#### 1. **observe** → `elfa_client.py`, `perp_client.py`, `onchain_client.py`
- **Purpose:** Fetch raw data from external sources
- **Output:** Raw snapshots (TickerNarrativeSnapshot, PerpMarketData, OnChainData)
- **Modules:** API clients

#### 2. **enrich** → `narrative_enricher.py`, `delta_store.py`
- **Purpose:** Add temporal context and historical analysis
- **Output:** Enriched snapshots with velocity, acceleration, anomalies
- **Modules:** NarrativeEnricher, DeltaStore

#### 3. **decide** → `signal_composer.py`
- **Purpose:** Fuse multiple signals into a composite decision
- **Input:** Enriched data from multiple sources
- **Output:** `CompositeSignal` with score, strength, confidence
- **Features:**
  - Weight normalization (adjusts when data missing)
  - Confidence scoring (based on agreement)
  - Signal strength classification
  - Explainable outputs (`explain()` method)

**Scoring Logic:**
- Narrative: Mindshare (0-0.4) + Velocity (-0.3 to 0.3) + Smart accounts (0-0.3)
- Market: Funding (-0.4 to 0.4) + Price momentum (-0.3 to 0.3) + Volume (0-0.3)
- On-chain: Exchange flow (-0.4 to 0.4) + Whale activity (-0.3 to 0.3) + Active addresses (0-0.3)

**Weight Normalization:**
- All sources: 40% narrative, 35% market, 25% on-chain
- Missing on-chain: ~53% narrative, ~47% market
- Only narrative: 100% narrative

#### 4. **gate** → `decision_moment.py` (DecisionMomentPolicy)
- **Purpose:** Determine if this moment should interrupt attention
- **Input:** Decision Moment candidate
- **Output:** `True` (interrupt) or `False` (suppress)
- **Checks:**
  - Cooldown (time since last moment)
  - Boring mode thresholds (min signals, velocity multiplier)
  - Alignment requirements
  - Recurring patterns (if disabled)

#### 5. **explain** → `decision_moment.py` (DecisionMoment.explain())
- **Purpose:** Generate human-readable explanation
- **Output:** Structured explanation of why now matters
- **Features:**
  - Contributing signals listed
  - Excluded signals documented
  - Interpretation summary
  - Uncertainty exposed
  - Provenance tracked

#### 6. **interrupt (or not)** → `alerts_engine.py`, Output Modules
- **Purpose:** Surface Decision Moment or suppress it
- **If Gated (True):** Fire alerts, surface opportunities, validate trades
- **If Suppressed (False):** No interruptions, continue monitoring
- **Modules:** AlertsEngine, entry_scanner, pre_trade_check, narrative_radar

---

## The Decision Moment: Where Paths Converge

**The Decision Moment is the atomic unit where all roads converge.**

### Structure

```python
DecisionMoment(
    id="BTC_20251213_1h",
    timestamp=datetime.utcnow(),
    subject_type="ticker",
    symbol="BTC",
    window="1h",
    
    # What triggered this
    trigger_description="Narrative acceleration detected",
    anomaly_type="acceleration",
    
    # Evidence
    signals_contributing=[...],  # What supports this
    signals_excluded=[...],      # What was considered but excluded
    
    # Context
    narrative_state="building",
    alignment="divergent",
    novelty="new",
    
    # Confidence
    conviction="medium",
    uncertainty="Medium — event-driven",
    
    # Interpretation
    interpretation_summary="Attention-worthy anomaly; timing uncertain",
    interpretation_exclusion="Not a trade recommendation",
    
    # Provenance
    provenance_sources=["GET /v2/data/top-mentions?ticker=BTC&timeWindow=1h"],
    generated_by="narrative_radar -> narrative_enricher",
    
    # Change tracking
    diff=DecisionMomentDiff(...)
)
```

### Key Properties

1. **Explainable:** Shows what changed and why
2. **Structured:** Consistent format across all moments
3. **Robust:** Handles missing data gracefully
4. **Composable:** Can be generated from any data source

---

## Outputs: Actionable Surfaces

### 1. **Alerts**

- **Source:** `alerts_engine.py`
- **Channels:** Console, Telegram, Discord
- **Trigger:** Rule conditions met
- **Format:** Structured messages with context

### 2. **Digests**

- **Source:** `narrative_digest.py`
- **Formats:** Obsidian, Telegram, Discord, Email, Blog, JSON
- **Content:** Daily summaries, top movers, insights

### 3. **Heatmaps**

- **Source:** `narrative_heatmap.py`
- **Output:** PNG images, markdown tables
- **Content:** Community overlap, velocity correlation

### 4. **Pre-Trade Checks**

- **Source:** `pre_trade_check.py`
- **Output:** APPROVED/BLOCKED with reasoning
- **Validation:** Narrative state, composite signals, anomalies

### 5. **Entry Scanner**

- **Source:** `entry_scanner.py`
- **Output:** Ranked opportunities by conviction
- **Detection:** Spikes, momentum, anomalies, smart money

---

## Data Flow: Path A → Path B → Decision Moment

### Example: Entry Scanner Workflow

```
1. Path A: Catalog Tools
   ├─> elfa_client.get_ticker_narrative_snapshot("BTC", "4h")
   │   └─> Returns: TickerNarrativeSnapshot
   │
   ├─> narrative_enricher.enrich_snapshot(snapshot)
   │   └─> Returns: EnrichedSnapshot (with velocity, acceleration)
   │
   ├─> delta_store.insert(enriched)
   │   └─> Stores to DuckDB
   │
   ├─> delta_store.calculate_velocity("BTC", "4h")
   │   └─> Returns: Historical velocity metrics
   │
   ├─> delta_store.detect_anomalies("BTC", "4h")
   │   └─> Returns: Z-score anomaly detection
   │
   └─> perp_client.get_perp_market_data("BTC")
       └─> Returns: PerpMarketData (funding, price, volume)

2. Path B: The Narrative OS Loop
   ├─> observe: Fetch data (elfa_client, perp_client)
   ├─> enrich: Add context (narrative_enricher, delta_store)
   ├─> decide: Fuse signals (signal_composer)
   │   └─> Returns: CompositeSignal (with confidence)
   ├─> gate: Filter noise (decision_moment policy)
   │   └─> Returns: True (interrupt) or False (suppress)
   ├─> explain: Generate reasoning (decision_moment.explain())
   │   └─> Returns: Structured explanation
   └─> interrupt (or not): Surface or suppress
       ├─> If gated: Fire alerts, surface opportunities
       └─> If suppressed: Continue monitoring, no interruption
```

---

## Design Principles Applied

### Path A (Catalog Tools)

- ✅ **Narrow:** Each module does one job
- ✅ **Immediate Utility:** Works standalone
- ✅ **Robust:** Never crashes, graceful errors
- ✅ **Explainable:** Audit trails, source queries

### Path B (Decision Engine)

- ✅ **Composable:** Modules snap together
- ✅ **Trust:** Confidence scores, explainable outputs
- ✅ **Explainable:** Evidence tracking, reasoning
- ✅ **Robust:** Handles missing data, normalizes weights

### Decision Moment

- ✅ **Atomic Unit:** Single concept, clear structure
- ✅ **Explainable:** Shows what changed and why
- ✅ **Structured:** Consistent format
- ✅ **Robust:** Handles edge cases

---

## Module Dependencies

```
Path A (Catalog Tools)
├─> elfa_client (standalone)
├─> narrative_enricher (depends on elfa_client)
├─> perp_client (standalone)
├─> delta_store (depends on narrative_enricher)
├─> narrative_radar (depends on elfa_client, narrative_enricher)
└─> narrative_heatmap (depends on elfa_client, narrative_enricher)

Path B (Decision Engine)
├─> signal_composer (depends on Path A modules)
├─> alerts_engine (depends on Path A modules)
└─> decision_moment (can use Path A or Path B outputs)

Outputs
├─> entry_scanner (uses Path A + Path B)
├─> pre_trade_check (uses Path A + Path B)
├─> narrative_digest (uses Path A)
└─> (alerts, heatmaps via Path A/B)
```

---

## The Narrative OS Loop in Practice

### Complete Loop Example

```
1. observe
   ├─> elfa_client.get_ticker_narrative_snapshot("BTC", "1h")
   ├─> perp_client.get_perp_market_data("BTC")
   └─> onchain_client.get_onchain_data("BTC")  # (if implemented)

2. enrich
   ├─> narrative_enricher.enrich_snapshot(snapshot)
   │   └─> Computes: velocity, acceleration, churn
   └─> delta_store.insert(enriched)
       └─> Stores for historical analysis

3. decide
   └─> signal_composer.compose(
           narrative_data=enriched,
           market_data=perp_data,
           onchain_data=onchain_data
       )
       └─> Returns: CompositeSignal with confidence

4. gate
   └─> decision_moment_policy.should_trigger(decision_moment)
       ├─> Checks: cooldown, boring mode, thresholds
       └─> Returns: True (interrupt) or False (suppress)

5. explain
   └─> decision_moment.explain()
       └─> Returns: Human-readable explanation

6. interrupt (or not)
   ├─> If gated: alerts_engine.check_all() → Fire alerts
   ├─> If gated: entry_scanner → Surface opportunity
   ├─> If gated: pre_trade_check → Validate trade
   └─> If suppressed: No interruption, continue monitoring
```

### Loop Characteristics

- **Iterative:** Loop runs continuously (or on-demand)
- **Stateful:** Each iteration builds on previous (via storage)
- **Gated:** Not every observation becomes an interruption
- **Explainable:** Every interruption has a clear explanation
- **Robust:** Loop continues even if stages fail

---

## Key Takeaways

- **Path A (Catalog Tools)** → Immediate utility, narrow modules (fetch, enrich, store, visualize).
- **Path B (The Narrative OS Loop)** → Canonical flow: `observe → enrich → decide → gate → explain → interrupt (or not)`
- **Decision Moment** → Atomic unit where all roads converge, exposing why now matters.
- **Outputs** → Actionable surfaces: alerts, digests, heatmaps, pre-trade checks.

---

*This architecture enables progressive commitment: start with Path A tools, grow into Path B workflows, converge on Decision Moments.*
