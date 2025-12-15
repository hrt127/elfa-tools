# Example: Suppressed Decision Moment

Example of a Decision Moment that was correctly blocked by the policy engine.

---

## Scenario: SOL Narrative Spike

**Ticker:** SOL  
**Type:** Narrative Spike

---

## OBSERVE

**Raw Data:**
- Mentions: +3.1× increase
- Sentiment: +0.32
- Keywords: meme-driven, short-lived

---

## ENRICH

**Computed Metrics:**
- Velocity: high
- Persistence: ❌ single window only
- Account churn: ❌ 78% new accounts (high turnover)
- Cross-window confirmation: ❌ none

---

## DECIDE

**Composite Signal:**
- Narrative strength: 0.68
- Direction: positive

**Note:** Signal composer produces a candidate due to raw velocity. This is expected behavior.

---

## GATE (Rejected)

**Rejection Reasons:**
- ❌ No persistence across windows
- ❌ Account churn dominated by new entrants (not returning accounts)
- ❌ Similar spike occurred <12h ago (cooldown)
- ❌ Classified as reactive noise

**Policy Outcome:** DecisionMoment rejected, no alert emitted

---

## Result

- Snapshot stored for historical comparison
- No human interruption
- System working as intended
