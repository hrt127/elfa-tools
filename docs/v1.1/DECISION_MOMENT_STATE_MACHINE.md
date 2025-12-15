# Decision Moment State Machine

**Canonical Reference** — How DecisionMoments flow through the system

---

## State Diagram (ASCII)

```text
                    ┌─────────────────┐
                    │   OBSERVE       │
                    │  (Raw Data)     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ENRICH        │
                    │  (Time Deltas)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   DECIDE        │
                    │  (Composite)    │
                    └────────┬────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │         GATE (Policy Engine)          │
         └───────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  POLICY PASS     │      │  POLICY BLOCK    │
    │  (should_trigger  │      │  (should_trigger │
    │   = True)        │      │   = False)       │
    └────────┬─────────┘      └────────┬─────────┘
             │                          │
             │                          ▼
             │              ┌──────────────────┐
             │              │   SUPPRESSED      │
             │              │  (Silent Success) │
             │              │  - Logged        │
             │              │  - No alert      │
             │              │  - History saved  │
             │              └───────────────────┘
             │
             ▼
    ┌──────────────────┐
    │   EXPLAIN        │
    │  (Generate Text) │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │   INTERRUPT       │
    │  (Alert Channels) │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │   DELIVERED       │
    │  - Alert sent     │
    │  - History saved  │
    │  - Cooldown set   │
    └───────────────────┘
```

---

## State Transitions

### State: OBSERVE

**Entry:** External trigger (API call, scheduled scan)

**Actions:**
- `elfa_client.get_ticker_narrative_snapshot()` → `TickerNarrativeSnapshot`
- `perp_client.get_perp_market_data()` → `MarketData`
- `onchain_client.get_onchain_metrics()` → `OnChainData` (optional)

**Exit Conditions:**
- ✅ Success → Transition to ENRICH
- ❌ Failure → Return `None`, no transition

**Error Handling:**
- API failure → Return `None`
- Rate limit → Return `None`
- Invalid data → Return `None`
- **Never raises exceptions**

---

### State: ENRICH

**Entry:** `TickerNarrativeSnapshot` available

**Actions:**
- `narrative_enricher.enrich_snapshot()` → `EnrichedSnapshot`
- `delta_store.insert()` → Store to DuckDB
- `delta_store.calculate_velocity()` → Compute velocity
- `delta_store.detect_anomalies()` → Statistical analysis

**Exit Conditions:**
- ✅ Success → Transition to DECIDE
- ❌ Failure → Return `None`, no transition

**Error Handling:**
- Missing history → Partial enrichment (velocity = 0, acceleration = 0)
- Database error → Return `None`
- **Never raises exceptions**

---

### State: DECIDE

**Entry:** `EnrichedSnapshot` + optional market/on-chain data

**Actions:**
- `signal_composer.compose()` → `CompositeSignal`
- Weight normalization based on available data
- Confidence calculation

**Exit Conditions:**
- ✅ Success → Transition to GATE
- ❌ Failure → Return `None`, no transition

**Error Handling:**
- Missing data sources → Normalize weights
- All data missing → Return neutral signal
- **Never raises exceptions**

---

### State: GATE

**Entry:** `CompositeSignal` or `DecisionMoment` candidate

**Actions:**
- Create `DecisionMoment` from `CompositeSignal`
- `DecisionMomentPolicy.should_trigger(dm)` → `bool`

**Policy Checks (in order):**

1. **Cooldown Check**
   ```python
   if last_triggered and (now - last_triggered) < cooldown_seconds:
       return False  # BLOCKED
   ```

2. **Boring Mode: Minimum Signals**
   ```python
   if boring_mode and len(dm.signals_contributing) < min_signals:
       return False  # BLOCKED
   ```

3. **Boring Mode: Velocity Multiplier**
   ```python
   if boring_mode:
       multipliers = [abs(value / baseline) for signal in signals]
       if max(multipliers) < min_velocity_multiplier:
           return False  # BLOCKED
   ```

4. **Boring Mode: Alignment Requirement**
   ```python
   if boring_mode and require_alignment:
       if dm.alignment not in ["aligned", "divergent"]:
           return False  # BLOCKED
   ```

5. **Boring Mode: Recurring Patterns**
   ```python
   if boring_mode and not allow_recurring_patterns:
       if dm.novelty == "recurring":
           return False  # BLOCKED
   ```

**Exit Conditions:**
- ✅ `should_trigger() == True` → Transition to EXPLAIN
- ❌ `should_trigger() == False` → Transition to SUPPRESSED

**Error Handling:**
- Invalid DM → Return `False`
- Missing fields → Return `False`
- **Never raises exceptions**

---

### State: SUPPRESSED

**Entry:** `should_trigger() == False`

**Actions:**
- Log DM to history (for analysis)
- Do NOT send alert
- Do NOT update cooldown (cooldown only set on trigger)

**Exit Conditions:**
- ✅ Logged → End (no further transitions)

**This is a success state.**  
Silence protects attention.

---

### State: EXPLAIN

**Entry:** `should_trigger() == True`

**Actions:**
- `dm.explain()` → Generate human-readable text
- Validate explanation completeness

**Exit Conditions:**
- ✅ Explanation valid → Transition to INTERRUPT
- ❌ Explanation invalid → Transition to SUPPRESSED (safety fallback)

**Error Handling:**
- Explanation generation failure → Suppress DM
- **Never raises exceptions**

---

### State: INTERRUPT

**Entry:** Valid explanation generated

**Actions:**
- `alerts_engine.check_all()` → Evaluate alert rules
- Fire alerts through all channels
- Save to `alert_history` table
- Save cooldown to `alert_cooldowns` table
- Update `DecisionMomentPolicy._last_moment`

**Exit Conditions:**
- ✅ Alert sent → Transition to DELIVERED
- ❌ Alert failure → Still transition to DELIVERED (logged)

**Error Handling:**
- Channel failure → Log error, continue to other channels
- Database failure → Log error, still send alerts
- **Never raises exceptions**

---

### State: DELIVERED

**Entry:** Alert sent (or attempted)

**Actions:**
- Mark as complete
- Human judgment begins

**Exit Conditions:**
- ✅ End state (no further transitions)

---

## State Persistence

### What Persists

1. **Enriched Snapshots** → `narrative_history.db` (SQLite)
2. **Historical Data** → `narrative_chronicle.duckdb` (DuckDB)
3. **Alert History** → `alerts_history.db` (SQLite)
4. **Cooldown State** → `alert_cooldowns` table (SQLite)
5. **Policy State** → `DecisionMomentPolicy._last_moment` (in-memory, loaded from DB)

### What Does NOT Persist

- `DecisionMoment` objects (ephemeral, generated on-demand)
- `CompositeSignal` objects (ephemeral)
- Policy overrides (future: will persist)

---

## State Machine Invariants

1. **No backward transitions** → States only flow forward
2. **No skipping states** → All 6 stages must execute
3. **No exceptions** → All errors return `None` or `False`
4. **Cooldown is stateful** → Persists across restarts
5. **Suppression is logged** → All DMs recorded for analysis

---

## Example: Full State Flow

```python
# 1. OBSERVE
snapshot = elfa_client.get_ticker_narrative_snapshot("BTC", "1h")
# State: OBSERVE → ENRICH

# 2. ENRICH
enriched = narrative_enricher.enrich_snapshot(snapshot)
# State: ENRICH → DECIDE

# 3. DECIDE
signal = signal_composer.compose("BTC", narrative_data=enriched, ...)
# State: DECIDE → GATE

# 4. GATE
dm = create_decision_moment_from_signal(signal)
if policy.should_trigger(dm):
    # State: GATE → EXPLAIN
    explanation = dm.explain()
    # State: EXPLAIN → INTERRUPT
    alerts_engine.check_all("BTC", enriched)
    # State: INTERRUPT → DELIVERED
else:
    # State: GATE → SUPPRESSED
    log_suppressed_dm(dm)
```

---

*End of Decision Moment State Machine*
