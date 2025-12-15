# Human Override Hooks

Override mechanisms allow humans to adjust system behavior without modifying code.

---

## Override Types

### 1. Ignore Once

Suppress a single Decision Moment instance.

**Use when:**
- You are already aware of the event
- Timing is not relevant

---

### 2. Suppress Class

Temporarily disable a Decision Moment type.

**Example:**
```yaml
suppress:
  - NarrativeAcceleration
duration: 24h
```

**Use when:**
- Market regime changes
- Known external events dominate

---

### 3. Raise Threshold

Activate or strengthen Boring Mode.

**Effect:**
- Requires larger deltas
- Longer persistence windows
- Higher cross-confirmation requirements

---

### 4. Force Explain Only

Generate explanations without sending alerts.

**Use when:**
- Research mode
- Learning phase
- Post-mortem analysis

---

## Override Rules

**Non-overrideable:**
- Cannot fabricate signals
- Cannot bypass explainability
- Cannot disable audit trails

**Principle:** Overrides tune sensitivity. They never alter truth.

---

## Implementation

Overrides are stored in `policy_overrides` table (SQLite) and checked before policy evaluation.
