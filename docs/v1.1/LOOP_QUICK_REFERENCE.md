# The Narrative OS Loop - Quick Reference

**Canonical Flow:** `observe → enrich → decide → gate → explain → interrupt (or not)`

---

## Stage → Code Mapping

| Stage | Module(s) | Key Function(s) | Output |
|-------|-----------|-----------------|--------|
| **observe** | `elfa_client.py`<br>`perp_client.py`<br>`onchain_client.py` | `get_ticker_narrative_snapshot()`<br>`get_perp_market_data()`<br>`get_onchain_data()` | `TickerNarrativeSnapshot`<br>`PerpMarketData`<br>`OnChainData` |
| **enrich** | `narrative_enricher.py`<br>`delta_store.py` | `enrich_snapshot()`<br>`calculate_velocity()`<br>`detect_anomalies()` | `EnrichedSnapshot`<br>Velocity metrics<br>Anomaly detection |
| **decide** | `signal_composer.py` | `compose()` | `CompositeSignal` |
| **gate** | `decision_moment.py` | `DecisionMomentPolicy.should_trigger()` | `True` (interrupt) or `False` (suppress) |
| **explain** | `decision_moment.py` | `DecisionMoment.explain()` | Explanation string |
| **interrupt** | `alerts_engine.py`<br>`entry_scanner.py`<br>`pre_trade_check.py` | `check_all()`<br>`scan_ticker()`<br>`check_trade()` | Alerts<br>Opportunities<br>Validations |

---

## Complete Loop Example

```python
# 1. observe
snapshot = get_ticker_narrative_snapshot("BTC", "1h")
market_data = get_perp_market_data("BTC")

# 2. enrich
enricher = NarrativeEnricher()
enriched = enricher.enrich_snapshot(snapshot)
store = DeltaStore()
store.insert(enriched)
anomaly = store.detect_anomalies("BTC", "1h")

# 3. decide
composer = SignalComposer()
signal = composer.compose(
    ticker="BTC",
    narrative_data=enriched,
    market_data=market_data,
    onchain_data=None
)

# 4. gate
policy = DecisionMomentPolicy(boring_mode=True)
dm = DecisionMoment(
    id="BTC_20251213_1h",
    timestamp=datetime.utcnow(),
    subject_type="ticker",
    symbol="BTC",
    window="1h",
    trigger_description="Narrative acceleration detected",
    anomaly_type="acceleration",
    signals_contributing=[...],
    # ... other fields
)
should_interrupt = policy.should_trigger(dm)

# 5. explain
if should_interrupt:
    explanation = dm.explain()
    print(explanation)

# 6. interrupt (or not)
if should_interrupt:
    # Fire alerts
    engine = AlertsEngine()
    engine.check_all("BTC", enriched)
    
    # Surface opportunity
    scanner = EntryScanner()
    opportunity = scanner.scan_ticker("BTC")
else:
    # Suppress - no interruption
    pass
```

---

## Loop Properties

- **Iterative:** Runs continuously, building state
- **Stateful:** SQLite/DuckDB track history
- **Gated:** Not every observation interrupts
- **Explainable:** Every interruption has reasoning
- **Robust:** Continues even when stages fail

---

*For detailed documentation, see [NARRATIVE_OS_LOOP.md](./NARRATIVE_OS_LOOP.md)*
