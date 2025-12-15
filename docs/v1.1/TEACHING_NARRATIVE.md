# 📖 Teaching Narrative – "Bricks, Castle, Throne"

A story-style guide to understanding the Decision Moment Ecosystem Map.

---

## 🎯 The Kingdom of Elfa Tools

Imagine Elfa Tools as a kingdom being built. Every contributor is a builder, and every module has a place in the grand design. This narrative helps you see how your work fits into the larger ecosystem.

---

## 🧱 Path A – The Bricks

**These are the Catalog Tools.**

### What They Are

The bricks are the foundational modules that provide immediate utility:

- **`elfa_client.py`** – Fetches raw narrative data
- **`narrative_enricher.py`** – Adds velocity, acceleration, and temporal context
- **`delta_store.py`** – Stores historical data for analysis
- **`narrative_radar.py`** – Scans multiple tickers at once
- **`narrative_heatmap.py`** – Visualizes relationships and patterns
- **`perp_client.py`** – Fetches market data (funding rates, price)
- **`onchain_client.py`** – Fetches on-chain metrics (when implemented)

### Their Nature

Each brick is **narrow**: one job, done well.

- They are **standalone** – you can use them independently
- They are **reusable** – other tools build on top of them
- They are **simple** – clear inputs, clear outputs
- They are **robust** – never crash, always return safe defaults

### Why They Matter

Think of them as the **foundation stones**: strong, simple, reusable.

When you're building a brick:
- Focus on doing one thing exceptionally well
- Make it easy for others to use
- Ensure it never breaks downstream workflows
- Document what it does and why

**Example:** `elfa_client.py` doesn't try to analyze data or generate signals. It just fetches data reliably. That's its job, and it does it well.

---

## 🏰 Path B – The Castle

**This is the Decision Engine.**

### What It Is

The castle is composed of tools that fuse bricks into higher-level capabilities:

- **`signal_composer.py`** – Combines narrative + market + on-chain data into composite signals
- **`alerts_engine.py`** – Applies rules and triggers notifications when conditions are met
- **`decision_moment.py`** – Structures explanations of why now matters

### Their Nature

The castle is **composable**: it fuses bricks into walls, towers, and gates.

- It **combines** multiple data sources
- It adds **trust and explainability**: confidence scores, provenance trails, cooldown rules
- It **filters noise** – only meaningful signals pass through
- It **protects** the kingdom from chaos

### Why They Matter

The castle protects the kingdom from noise and chaos, ensuring only meaningful signals pass through.

When you're building castle components:
- Show how you combine multiple bricks
- Explain your reasoning (confidence scores, evidence)
- Handle missing data gracefully (robust degradation)
- Make it clear why your output matters

**Example:** `signal_composer.py` takes data from `elfa_client.py`, `perp_client.py`, and `onchain_client.py`, then fuses them into a single composite signal with confidence scores and warnings. It doesn't fetch data itself – it composes what others provide.

---

## 👑 The Throne – The Decision Moment

**At the center sits the Decision Moment: the atomic unit of value.**

### What It Is

The Decision Moment is a structured explanation of **"Why now matters."**

It is not:
- A prediction
- An oracle
- A black box
- An absolute claim

It is:
- A **structured story** that empowers human judgment
- An explanation of what changed and why it surfaced
- A collection of signals, reasoning, uncertainty, and provenance
- The convergence point for all tools

### Its Nature

The Decision Moment is:

- **Explainable** – Shows source data, contributing factors, and audit trails
- **Robust** – Handles partial data, never crashes, fails safely
- **Reproducible** – Same inputs produce same outputs
- **Transparent** – Exposes uncertainty instead of hiding it

### Why It Matters

Every brick and every castle wall points toward this throne.

When you're building tools:
- Ask: "Does this help explain why now matters?"
- If it doesn't justify a Decision Moment, it shouldn't interrupt attention
- Make your outputs converge on this concept
- Show the story, not just the data

**Example:** `pre_trade_check.py` doesn't just say "approved" or "blocked." It explains why – showing velocity, acceleration, composite signals, and warnings. That explanation is a Decision Moment.

---

## 🌟 The Outputs – The Kingdom's Voice

**From the throne, the Decision Moment speaks through various messengers.**

### The Messengers

These are the tools that deliver Decision Moments to users:

- **Alerts** – Console, Discord, Telegram notifications
- **Digests** – Daily reports (Obsidian, Telegram, Discord, Email, Blog, JSON)
- **Heatmaps** – Visual relationship maps
- **Pre-trade checks** – Risk validation before trades
- **Entry scanners** – Opportunity discovery
- **Position monitors** – Ongoing position tracking

### Their Nature

These outputs are the **kingdom's messengers**, carrying clarity to every corner.

- They **format** Decision Moments for different contexts
- They **deliver** them through appropriate channels
- They **preserve** the explainability and provenance
- They **respect attention** – only interrupt when it matters

### Why They Matter

The messengers ensure Decision Moments reach the right people at the right time in the right format.

When you're building output tools:
- Preserve the Decision Moment structure
- Format for the target platform
- Maintain explainability
- Respect user attention

**Example:** `narrative_digest.py` takes Decision Moments and formats them for Obsidian, Telegram, or Discord. The format changes, but the core explanation remains.

---

## ✨ The Teaching Mantra

**How to remember the ecosystem:**

1. **Bricks build the castle.**
   - Foundation tools provide raw capabilities
   - Each does one job well

2. **The castle protects the throne.**
   - Decision engines filter noise and add trust
   - They compose bricks into higher-level signals

3. **The throne explains why now matters.**
   - Decision Moments are the atomic unit of value
   - Everything converges here

4. **The messengers carry the story outward.**
   - Outputs deliver Decision Moments to users
   - They format and channel the explanation

---

## 🎓 For Contributors

### When Building a Brick

Ask yourself:
- ✅ Does this do one job well?
- ✅ Can others build on top of it?
- ✅ Does it never crash?
- ✅ Is it easy to understand and use?

**Example:** If you're adding a new data client, make it narrow (one data source), robust (never crashes), and composable (works with signal_composer).

### When Building Castle Components

Ask yourself:
- ✅ Does this combine multiple bricks?
- ✅ Does it add explainability (confidence, evidence)?
- ✅ Does it filter noise effectively?
- ✅ Does it handle missing data gracefully?

**Example:** If you're adding a new signal type, show how it combines existing data sources, provide confidence scores, and explain your reasoning.

### When Building Outputs

Ask yourself:
- ✅ Does this preserve the Decision Moment structure?
- ✅ Is it formatted appropriately for the target?
- ✅ Does it respect user attention?
- ✅ Does it maintain explainability?

**Example:** If you're adding a new output format, ensure it includes the same explanation structure (what changed, why it matters, what signals contributed).

---

## 🗺️ The Ecosystem Map

```
┌─────────────────────────────────────────────────────────┐
│                    THE KINGDOM                           │
│                                                           │
│  🧱 BRICKS (Foundation)                                  │
│  ├─ elfa_client.py                                       │
│  ├─ narrative_enricher.py                                │
│  ├─ delta_store.py                                       │
│  ├─ narrative_radar.py                                   │
│  ├─ narrative_heatmap.py                                 │
│  ├─ perp_client.py                                       │
│  └─ onchain_client.py                                    │
│                                                           │
│         ⬇️ (compose)                                      │
│                                                           │
│  🏰 CASTLE (Decision Engine)                             │
│  ├─ signal_composer.py                                   │
│  ├─ alerts_engine.py                                     │
│  └─ decision_moment.py                                   │
│                                                           │
│         ⬇️ (converge)                                     │
│                                                           │
│  👑 THRONE (Decision Moment)                            │
│  └─ "Why now matters"                                    │
│                                                           │
│         ⬇️ (deliver)                                      │
│                                                           │
│  🌟 MESSENGERS (Outputs)                                 │
│  ├─ Alerts (console, Discord, Telegram)                 │
│  ├─ Digests (Obsidian, Telegram, Discord, etc.)          │
│  ├─ Heatmaps                                             │
│  ├─ Pre-trade checks                                     │
│  ├─ Entry scanners                                       │
│  └─ Position monitors                                    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Key Insights

1. **Everything flows toward the Decision Moment.**
   - Bricks provide data
   - Castle components compose signals
   - The throne structures the explanation
   - Messengers deliver it

2. **Each layer has a clear purpose.**
   - Bricks: Fetch, enrich, store, visualize
   - Castle: Compose, filter, explain
   - Throne: Structure the "why now"
   - Messengers: Format and deliver

3. **Design principles apply at every level.**
   - **Narrow:** Each tool does one job
   - **Explainable:** Show source data and reasoning
   - **Robust:** Never crash, handle partial data
   - **Composable:** Tools work together seamlessly
   - **Signal Layer, Not Oracle:** Provide context, not answers
   - **Transparent Constraints:** Show rate limits, caching, provenance

4. **The Decision Moment is the convergence point.**
   - If something can't justify a Decision Moment, it shouldn't interrupt attention
   - Every tool should help explain "why now matters"
   - The explanation is the value, not just the data

---

## 🚀 Getting Started

### For New Contributors

1. **Start with a brick.**
   - Pick a simple, focused task
   - Make it narrow and robust
   - Ensure it composes well

2. **Understand the castle.**
   - See how your brick fits into signal composition
   - Understand how Decision Moments are structured
   - Learn how alerts and rules work

3. **Think about the throne.**
   - Ask: "Does this help explain why now matters?"
   - Ensure your outputs converge on Decision Moments
   - Make explanations clear and structured

4. **Consider the messengers.**
   - Think about how users will consume your output
   - Format appropriately for the target
   - Preserve explainability

---

## 📚 Related Documentation

- **[DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md)** – Complete design philosophy
- **[CATALOG.md](./CATALOG.md)** – Complete tool catalog
- **[ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)** – Technical architecture
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** – Contribution guidelines

---

## 🎯 Remember

**Bricks build the castle.**  
**The castle protects the throne.**  
**The throne explains why now matters.**  
**The messengers carry the story outward.**

This narrative makes the ecosystem easy to grasp: contributors can see how their module (brick) fits into the larger castle, and how everything converges on the throne – the Decision Moment.

---

*"In the kingdom of Elfa Tools, every builder knows their place, and every module serves the throne."*

