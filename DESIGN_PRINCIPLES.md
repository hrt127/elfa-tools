# 🎯 Elfa Tools — Design Principles (v2)

## What Elfa Is

**Elfa Tools is a narrative operating system for decision-making under uncertainty.**

It is **not**:

- a trading bot
- a signal provider
- a dashboard
- an AI toy

Elfa does not make decisions for you.  
It **structures information so you can decide with confidence.**

---

## The Core Idea

Markets, research, and systems are dominated by **narratives**, not facts alone.  
Narratives are messy, contextual, and time-sensitive.

Elfa exists to:

- observe narrative signals
- structure them
- relate them
- surface them **only when they matter**

The goal is not prediction.  
The goal is **clear judgment under uncertainty**.

---

## The Atomic Unit: The Decision Moment

Elfa is built around a single concept:

> **A Decision Moment is a structured explanation of _why now matters_.**

A Decision Moment:

- is triggered by change, not noise
- explains _what changed_ and _why it surfaced_
- shows contributing signals and exclusions
- exposes uncertainty instead of hiding it
- invites human judgment instead of replacing it

Alerts, digests, dashboards, and workflows all converge on this unit.

If something cannot justify a Decision Moment, it should not interrupt attention.

---

## Core Principles

### 1. Narrow

Each tool does **one job** and does it well.  
No feature creep. No hidden responsibilities.

**Implementation:** Every tool has a single, well-defined purpose (see tool table below).

---

### 2. Explainable by Default

Every output:

- shows its source data
- exposes contributing factors
- includes audit trails
- can be reasoned about or disagreed with

Explainability is not an add-on.  
It is the default surface.

**Implementation:**
- All tools include `source_query` for audit trails
- `narrative_radar.py` → Shows velocity, acceleration, churn with indicators
- MVP outputs are explainable by default (see v1.1 features for advanced explainability)

---

### 3. Robust

Elfa must **never fail loudly**.

- Errors return safe defaults
- Partial data is handled gracefully
- Tools never crash downstream workflows
- Reruns are safe and reproducible

Stability > cleverness.

**Implementation:**
- All functions return `None` on errors (never raise exceptions)
- Graceful degradation (works with partial data)
- Comprehensive error handling (API timeouts, rate limits, invalid data)
- Error visibility (clear warnings, never silent failures)

---

### 4. Composable

Tools are designed to:

- work standalone
- snap together naturally
- scale from scripts → workflows → systems

Composition happens at the **Decision Moment**, not through tight coupling.

**Implementation:**
- Shared data structures (`TickerNarrativeSnapshot`, `EnrichedSnapshot`)
- Seamless integration (tools combine naturally)
- Modular design (each tool independent, easy to extend)
- MVP: `elfa_client.py` + `narrative_enricher.py` + `narrative_radar.py` compose naturally

---

### 5. Signal Layer, Not Oracle

Elfa provides **signals and context**, not answers.

- No black boxes
- No absolute claims
- No "trust me" outputs

Human judgment remains the final authority.

**Implementation:**
- All signals show confidence scores
- Composite signals show component breakdowns
- Warnings highlight uncertainty
- Tools provide evidence, not predictions

---

### 6. Transparent Constraints

Taste is enforced through architecture:

- rate-limit awareness
- caching with explicit TTLs
- persistence with SQLite/DuckDB
- visible provenance (`source_query`)

Constraints are features, not limitations.

**Implementation:**
- Built-in rate limit tracking (60 requests/60 seconds)
- Configurable caching (5-minute default TTL)
- SQLite/DuckDB persistence with audit trails
- Every snapshot includes `source_query` field

---

## Design Philosophies

### Mental Model Clarity
A new user should understand what Elfa is — and isn't — in under 60 seconds.

**How we achieve it:**
- Clear docstrings in every tool
- QUICKSTART.md gets you running in 5 minutes
- PROSPECTUS.md explains what Elfa is and why it matters
- CATALOG.md organizes tools by function

---

### Progressive Commitment
Start with one script.  
Grow into workflows only if value is proven.

**How we achieve it:**
- Each tool works standalone
- Start with `narrative_radar.py` (simplest)
- Progress to `entry_scanner.py` (moderate)
- Build to full workflows (advanced)

---

### Attention Is Scarce
Elfa optimizes for _fewer, better interruptions_ — not constant engagement.

**How we achieve it:**
- Alerts only trigger on meaningful changes
- Cooldown management prevents spam
- Decision Moments surface only when they matter
- Tools respect rate limits to avoid noise

---

### Trust Is Earned Structurally
Trust comes from:

- reproducibility
- explainability
- restraint

**How we achieve it:**
- Same inputs → same outputs (reproducible)
- Every output shows reasoning (explainable)
- Tools don't make claims they can't support (restraint)
- Audit trails for all data (transparent)

---

### Conceptual Completeness Over Feature Completeness
The system can be whole in design before it is complete in code.

**How we achieve it:**
- ROADMAP.md shows vision and future
- Core principles guide all development
- Tools are designed to be complete conceptually, even if not all features exist yet

---

## Value Promise

### Immediate

- A usable, opinionated set of tools
- Low barrier to entry
- Clear outputs you can act on today

**Delivered through:**
- QUICKSTART.md (5-minute setup)
- Working tools you can use immediately
- Clear visual indicators (🚀📈↗️➡️↘️📉💥) for velocity and acceleration

---

### Ultimate

- A personal narrative intelligence system
- Calm awareness instead of constant monitoring
- Confidence rooted in understanding, not signals

**Delivered through:**
- MVP: Velocity, acceleration, and account churn tracking
- v1.1: Complete trading workflows, historical analysis, explainable signals (see `optional/` directory)

---

## Non-Goals (Explicit)

Elfa will never aim to:

- predict markets
- automate conviction
- maximize engagement
- replace discretion

If those are the goals, this system is not for you.

---

## The Standard of Quality

A feature belongs in Elfa **only if** it:

1. Reduces cognitive load
2. Improves clarity at the decision moment
3. Can explain itself
4. Fails safely
5. Respects attention

If it does not meet all five, it does not ship.

**How MVP tools meet this standard:**

| Tool | Reduces Load | Improves Clarity | Explains Itself | Fails Safely | Respects Attention |
|------|-------------|-----------------|-----------------|--------------|-------------------|
| `narrative_radar.py` | ✅ Visual indicators | ✅ Shows all metrics | ✅ Velocity/accel/churn | ✅ Never crashes | ✅ Clear, focused output |
| `narrative_enricher.py` | ✅ Computes temporal context | ✅ Shows velocity/accel | ✅ Account churn tracking | ✅ Handles missing data | ✅ Transparent calculations |
| `elfa_client.py` | ✅ Caching reduces calls | ✅ `source_query` audit trail | ✅ Clear error handling | ✅ Never crashes | ✅ Rate limit awareness |

**v1.1 tools:** See `optional/` directory for advanced features that also meet this standard.

---

## In One Sentence

**Elfa helps you notice the right things, at the right time, for the right reasons — and then gets out of the way.**

---

## How Tools Implement Principles

### Tool-by-Tool Alignment

### MVP Core Tools

| Tool | Narrow | Explainable | Robust | Composable | Signal Layer | Transparent |
|------|--------|-------------|--------|------------|--------------|-------------|
| `elfa_client.py` | ✅ API client only | ✅ `source_query` | ✅ Never crashes | ✅ Used by all | ✅ Returns data | ✅ Rate limits visible |
| `narrative_enricher.py` | ✅ Temporal analysis only | ✅ Shows velocity/accel | ✅ Handles missing data | ✅ Composes with client | ✅ Computes signals | ✅ SQLite audit trail |
| `narrative_radar.py` | ✅ Multi-ticker scan | ✅ Shows all metrics | ✅ Graceful errors | ✅ Uses client+enricher | ✅ Visual indicators | ✅ Markdown export |
| `decision_moment.py` | ✅ Concept only | ✅ Structured explanation | ✅ Policy engine | ✅ Used by all | ✅ Decision Moments | ✅ Provenance tracking |

**Status: ✅ MVP tools fully aligned with all principles.**

**v1.1 tools:** See `optional/` directory for additional tools that also align with all principles.

---

## Decision Moments in Practice

### MVP Example: Narrative Radar Scan

**Decision Moment:** "Why does BTC matter now?"

**Structure:**
- **What changed:** Mentions increased by 45, velocity accelerated by +12
- **Why it surfaced:** Strong momentum detected (🚀 velocity, ⚡ acceleration)
- **Contributing factors:** Total mentions (1250), mindshare (0.85), account churn (+2 new)
- **Uncertainty:** Visual indicators show strength but not certainty
- **Human judgment:** You interpret the signals and decide

**Output:**
```text
BTC      1250        🚀 +45         ⚡ +12   0.85         +2 new, -1 lost
```

This is a Decision Moment: structured explanation of why BTC deserves attention now.

**v1.1 examples:** See `docs/v1.1/examples/` for advanced Decision Moment examples from trading workflows.

---

## Related Documentation

- **Quickstart:** [QUICKSTART.md](./QUICKSTART.md) - Get started in 5 minutes
- **Examples:** [docs/examples/](./docs/examples/) - Decision Moment examples
- **v1.1 Features:** [docs/v1.1/](./docs/v1.1/) - Advanced features and workflows

---

*Last updated: 2024-01-XX*
