# Example: BTC Decision Moment

Complete flow through the Narrative OS Loop for a BTC narrative acceleration event.

---

## 1. OBSERVE

**Modules:** `elfa_client.py`, `perp_client.py`

**Command:**

```bash
python narrative_radar.py BTC --window 4h
```

**Raw Data:**

- Mentions: 143 (previous: 58)
- Keywords: ETF, inflows, accumulation
- Sentiment: +0.21
- Smart accounts: 9 (previous: 3)
- Funding: neutral
- Price: flat

**Output:** `TickerNarrativeSnapshot`

---

## 2. ENRICH

**Modules:** `narrative_enricher.py`, `delta_store.py`

**Computed Metrics:**

- Mention velocity: +2.4×
- Sentiment acceleration: +0.18
- Account churn: low
- Returning accounts: 62%
- Persistence: confirmed across 1h → 4h windows

**Output:** `EnrichedSnapshot`

---

## 3. DECIDE

**Module:** `signal_composer.py`

**Composite Signal:**

```json
{
  "narrative_strength": 0.73,
  "direction": "positive",
  "drivers": [
    "accelerating mentions",
    "returning smart accounts",
    "keyword persistence"
  ]
}
```

**Output:** `CompositeSignal`

---

## 4. GATE

**Module:** `decision_moment.py`

**Policy Checks:**

- Cooldown expired: ✅
- Velocity threshold met: ✅
- Not noise pattern: ✅
- Funding aligned: ✅
- Boring mode passed: ✅

**Result:** DecisionMoment approved

**Output:** `DecisionMoment` (policy_passed=True)

---

## 5. EXPLAIN

**Generated Explanation:**

```
BTC Narrative Shift Detected

What changed:
- Mentions accelerated 2.4× over 4h
- Sentiment moved positive
- Majority of activity from returning smart accounts

Why this matters:
- Pattern historically precedes volatility expansion
- Change persisted across multiple windows

What did not matter:
- No funding imbalance
- No retail-only participation spike

Confidence: Medium
Uncertainty: Macro catalysts unresolved
```

---

## 6. INTERRUPT

**Module:** `alerts_engine.py`

**Actions:**

- Alert sent via Telegram
- Stored in `delta_store`
- Added to daily digest

**End of system processing. Human judgment begins.**

