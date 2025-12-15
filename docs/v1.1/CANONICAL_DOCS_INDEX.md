# Canonical Documentation Index

**Elfa Narrative OS — Complete System Reference**

---

## 📚 Documentation Structure

This index organizes all canonical documentation for the Elfa Narrative OS. Each document serves as the **definitive reference** for how the system works.

---

## Core Documents

### 1. [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md)

**What it covers:**
- System identity (what it is and isn't)
- The Narrative OS Loop (6 stages)
- Stage-by-stage breakdown (what happens, what talks to what)
- DecisionMoment schema
- Policy engine overview
- Examples (failed and successful DMs)
- Human override hooks
- File/responsibility map
- System invariants

**Read this first** to understand the overall system.

---

### 2. [DECISION_MOMENT_STATE_MACHINE.md](./DECISION_MOMENT_STATE_MACHINE.md)

**What it covers:**
- Complete state diagram (ASCII)
- State transitions (OBSERVE → ENRICH → DECIDE → GATE → EXPLAIN → INTERRUPT)
- State persistence (what persists, what doesn't)
- State machine invariants
- Example: Full state flow

**Read this** to understand how DecisionMoments flow through the system.

---

### 3. [POLICY_DSL.md](./POLICY_DSL.md)

**What it covers:**
- Policy configuration schema
- Policy evaluation logic (5 steps)
- Policy modes (boring mode on/off, custom)
- Policy examples (high-frequency, ultra-strict, balanced)
- Policy override system (future)
- Policy metrics and tuning

**Read this** to configure and tune Decision Moment gating.

---

### 4. [ALERT_TRUST_METRICS.md](./ALERT_TRUST_METRICS.md)

**What it covers:**
- Trust dimensions (precision, recall, latency, explanation quality, suppression accuracy)
- Trust score calculation
- Metrics dashboard schema
- Trust improvement strategies
- Trust monitoring queries
- Trust targets (canonical thresholds)

**Read this** to measure and improve Decision Moment quality.

---

### 5. [ARCHITECTURE_CANONICAL.md](./ARCHITECTURE_CANONICAL.md)

**What it covers:**
- System overview (ASCII diagram)
- Complete data flow (all 6 stages)
- Module dependency graph
- Storage architecture
- Rate limiting & caching
- Error handling flow

**Read this** to understand module interactions and data flow.

---

## Quick Reference

### "I want to understand..."

**...what the system does:**
→ [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (Section: "What This System Is")

**...how the loop works:**
→ [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (Section: "The Narrative OS Loop")

**...what each stage does:**
→ [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (Sections: "1️⃣ OBSERVE" through "6️⃣ INTERRUPT")

**...how DecisionMoments flow:**
→ [DECISION_MOMENT_STATE_MACHINE.md](./DECISION_MOMENT_STATE_MACHINE.md)

**...how to configure policy:**
→ [POLICY_DSL.md](./POLICY_DSL.md)

**...how to measure quality:**
→ [ALERT_TRUST_METRICS.md](./ALERT_TRUST_METRICS.md)

**...how modules connect:**
→ [ARCHITECTURE_CANONICAL.md](./ARCHITECTURE_CANONICAL.md)

---

## Document Relationships

```
CANONICAL_SYSTEM_DESCRIPTION.md
    │
    ├─► DECISION_MOMENT_STATE_MACHINE.md (details state flow)
    │
    ├─► POLICY_DSL.md (details policy engine)
    │
    ├─► ALERT_TRUST_METRICS.md (details quality measurement)
    │
    └─► ARCHITECTURE_CANONICAL.md (details module interactions)
```

---

## Reading Order

### For New Users

1. [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (complete read)
2. [ARCHITECTURE_CANONICAL.md](./ARCHITECTURE_CANONICAL.md) (data flow section)
3. [DECISION_MOMENT_STATE_MACHINE.md](./DECISION_MOMENT_STATE_MACHINE.md) (state diagram)

### For Developers

1. [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (overview)
2. [ARCHITECTURE_CANONICAL.md](./ARCHITECTURE_CANONICAL.md) (complete read)
3. [DECISION_MOMENT_STATE_MACHINE.md](./DECISION_MOMENT_STATE_MACHINE.md) (complete read)
4. [POLICY_DSL.md](./POLICY_DSL.md) (as needed)

### For Operators

1. [CANONICAL_SYSTEM_DESCRIPTION.md](./CANONICAL_SYSTEM_DESCRIPTION.md) (overview)
2. [POLICY_DSL.md](./POLICY_DSL.md) (complete read)
3. [ALERT_TRUST_METRICS.md](./ALERT_TRUST_METRICS.md) (complete read)

---

## Key Concepts

### The Narrative OS Loop

```
observe → enrich → decide → gate → explain → interrupt (or not)
```

**Invariant:** This loop never branches, never skips stages, never short-circuits.

### Decision Moment

A **DecisionMoment** is *permission to interrupt a human*.

Nothing else in the system is allowed to do that.

### Policy Engine

The **Policy Engine** answers:

> "Is this interruption worth human attention?"

It enforces:
- Cooldowns
- Minimum signals
- Velocity thresholds
- Alignment requirements
- Recurring pattern filters

### Trust Metrics

**Trust Score** = Composite of:
- Precision (false positive rate)
- Recall (false negative rate)
- Latency (time to surface)
- Explanation quality
- Suppression accuracy

**Target:** Trust Score ≥ 0.75

---

## System Invariants

1. **Never crashes** → All modules return `None` on error, never raise
2. **Never skips stages** → Loop always completes all 6 stages
3. **Never fires without explanation** → Every DM must have `explain()`
4. **Never fires without policy** → Every DM must pass `should_trigger()`
5. **Never alters history** → Overrides only affect future behavior

---

## Mental Model

> Elfa does not tell you what to do.  
> It tells you **when the world has changed enough that *you* should care**.

---

## Related Documentation

- [NARRATIVE_OS_LOOP.md](./NARRATIVE_OS_LOOP.md) — Conceptual overview
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md) — Two-path model
- [TEST_PLAN.md](./TEST_PLAN.md) — Testing strategy
- [CODE_ANALYSIS.md](./CODE_ANALYSIS.md) — Code review and issues

---

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| CANONICAL_SYSTEM_DESCRIPTION.md | ✅ Canonical | 2024-12-13 |
| DECISION_MOMENT_STATE_MACHINE.md | ✅ Canonical | 2024-12-13 |
| POLICY_DSL.md | ✅ Canonical | 2024-12-13 |
| ALERT_TRUST_METRICS.md | ✅ Canonical | 2024-12-13 |
| ARCHITECTURE_CANONICAL.md | ✅ Canonical | 2024-12-13 |

**Canonical** = This is the definitive reference. Changes require explicit approval.

---

*End of Canonical Documentation Index*
