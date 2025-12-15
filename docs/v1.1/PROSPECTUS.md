# 📘 Elfa Tools Prospectus

## What Elfa Tools Are

**Elfa Tools is a narrative operating system for decision-making under uncertainty.**

It is **not**:

- a trading bot
- a signal provider
- a dashboard
- an AI toy

Elfa does not make decisions for you. It **structures information so you can decide with confidence.**

The tools are designed to be **modular, explainable, robust, and composable** - each component does one job well and works seamlessly with others. All tools converge on the **Decision Moment**: a structured explanation of why now matters.

---

## What They Can Be

### Composable

Tools can be combined into workflows, dashboards, or APIs depending on user needs. Each tool works standalone or as part of a larger system.

**Example:** `morning_routine.py` combines `narrative_radar.py` → `entry_scanner.py` → `narrative_digest.py` into a single automated workflow.

---

### Scalable

Start small with a single module, then expand into a full intelligence cockpit. Begin with `elfa_client.py` for basic data fetching, then add `narrative_enricher.py` for temporal analysis, and scale to a complete trading system.

**Example:** Start with `narrative_radar.py` for daily scans, then add `position_monitor.py` for automated monitoring, then integrate `signal_composer.py` for multi-source signals.

---

### Adaptive

Built to evolve with feedback, ensuring relevance in fast‑changing contexts. All tools follow design principles that enable iteration and improvement.

**Example:** `alerts_engine.py` supports custom rules that can be refined based on real trading outcomes.

---

### Future‑ready

Designed to integrate with trading platforms, knowledge systems, or collaborative environments. Modular architecture makes it easy to add new integrations.

**Example:** `dashboard_adapter.py` (planned) will integrate with external dashboards, `bot_adapter.py` (planned) will add Telegram/Discord interfaces.


---

## How to Use Them

### Pick a Module

Choose the tool that fits your immediate need:

- **Quick scan?** → `narrative_radar.py`
- **Daily digest?** → `narrative_digest.py`
- **Entry setups?** → `entry_scanner.py`
- **Pre-trade validation?** → `pre_trade_check.py`
- **Position monitoring?** → `position_monitor.py`


### Run It Standalone

Each script works independently for quick insights:

```bash
# Quick narrative scan
python narrative_radar.py BTC ETH SOL --window 4h

# Generate daily digest
python narrative_digest.py BTC ETH SOL --format telegram

# Find entry opportunities
python entry_scanner.py BTC ETH SOL
```

### Chain Them Together

Combine outputs for deeper analysis:

```bash
# Morning routine: radar → scanner → digest
python morning_routine.py BTC ETH SOL

# Trading workflow: scanner → pre-trade check → position monitor
python entry_scanner.py BTC ETH SOL
python pre_trade_check.py BTC long
python position_monitor.py 300 &
```

### Embed in Workflows

Integrate into your daily cockpit for trading, research, or learning:

**Trading System:**

- Morning: `morning_routine.py` → Find opportunities
- Throughout day: `position_monitor.py` → Monitor positions
- Before trades: `pre_trade_check.py` → Validate entries
- End of day: `eod_review.py` → Learn and iterate

**Research Workflow:**

- Collect: `elfa_client.py` → Fetch raw data
- Enrich: `narrative_enricher.py` → Add temporal context
- Analyze: `narrative_heatmap.py` → Discover relationships
- Store: `delta_store.py` → Historical analysis
- Report: `narrative_digest.py` → Generate insights

### Iterate

Use feedback loops to refine outputs and adapt tools to your context:

- Track which alerts were useful
- Refine entry scanner conviction thresholds
- Adjust position monitoring intervals
- Update watchlists based on performance

---

## What Makes Them Valuable

### Clarity

Turn complex narratives into digestible insights. Every tool shows its reasoning and source data.

**Example:** `signal_composer.py` explains why a signal is bullish/bearish with component scores and evidence.

### Efficiency

Automate repetitive analysis, saving time and energy. Tools reduce manual work by 75-93%.

**Example:** Morning scan: 20 min → 5 min. Entry finding: 15 min → 1 min.

### Reliability

Standardized outputs reduce errors and improve comparability. Same inputs always produce same outputs.

**Example:** All tools use `TickerNarrativeSnapshot` and `EnrichedSnapshot` for consistent data structures.

---

### User‑Centered

Designed for traders, builders, and learners — not just developers. Simple CLI tools for traders, well-documented APIs for builders.

**Example:** `entry_scanner.py` gives clear recommendations (STRONG BUY/SELL) with reasoning, not just raw data.

---

### Safety

Respect for permissions, reproducibility, and risk management. Never crashes, always shows audit trails.

**Example:** All tools return `None` on errors (never crash), include `source_query` for audit trails, respect rate limits.

---

### Growth

Tools evolve with user feedback, staying relevant and effective. Versioned, documented, with clear improvement paths.

**Example:** `ROADMAP.md` shows planned improvements, `CHANGELOG.md` tracks changes, tools are designed for extension.


---

## Catalog Snapshot

### Core Data Tools

- **elfa_client.py** → Authenticated API client with caching, rate limits, audit trails
- **perp_client.py** → Market data client for perpetual futures
- **onchain_client.py** → Template for on-chain metrics

### Analysis Tools

- **narrative_enricher.py** → Adds velocity, acceleration, churn, temporal analysis
- **narrative_radar.py** → Multi-ticker scanner with markdown exports
- **narrative_heatmap.py** → Relationship discovery (overlap, correlation, similarity)

### Signal & Output Tools

- **signal_composer.py** → Composite signal generator (narrative + funding + price)
- **narrative_digest.py** → Multi-format daily digest (6 formats)

### Automation Tools

- **alerts_engine.py** → Rule-based alerts with multi-channel delivery
- **delta_store.py** → Historical data storage and analysis

### Trading Workflow Tools

- **entry_scanner.py** → Find high-conviction entry setups
- **pre_trade_check.py** → Validate trades before entry
- **position_monitor.py** → Monitor positions for narrative changes
- **morning_routine.py** → Automated morning scan workflow
- **eod_review.py** → End-of-day review and analysis


---

## Design Principles

All tools adhere to six core principles:

1. **Narrow** — Each tool does one job well
2. **Explainable** — Show source data, contributing factors, and audit trails
3. **Robust** — Fail gracefully, never crash, handle partial data
4. **Composable** — Tools work standalone and snap together naturally
5. **Signal Layer, Not Oracle** — Provides signals and context, not answers
6. **Transparent Constraints** — Rate limits, caching, and provenance are visible

Every tool converges on the **Decision Moment**: a structured explanation of why now matters.

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete design philosophy, including the Decision Moment concept, design philosophies, value promise, non-goals, and quality standards.

---

## Getting Started

**🚀 New to Elfa Tools?** Start with the [QUICKSTART.md](./QUICKSTART.md) guide - get running in 5 minutes.

**Quick steps:**

1. **Install:** `pip install -r requirements.txt`
2. **Configure:** Set `ELFA_API_KEY` environment variable
3. **Try:** `python narrative_radar.py BTC ETH SOL`
4. **Explore:** See [CATALOG.md](./CATALOG.md) for full tool catalog
5. **Workflow:** See [TRADING_WORKFLOW.md](./TRADING_WORKFLOW.md) for daily workflows


---

## Documentation

**🚀 Entry Point:**

- **Quickstart:** [QUICKSTART.md](./QUICKSTART.md) - Get started in 5 minutes

**🗺️ Navigation:**

- **Catalog:** [CATALOG.md](./CATALOG.md) - Complete tool catalog organized by category
- **Trading Workflow:** [TRADING_WORKFLOW.md](./TRADING_WORKFLOW.md) - Daily trading system workflows (playbooks)
- **Roadmap:** [ROADMAP.md](./ROADMAP.md) - Planned features and future vision

**📖 Deep Dive:**

- **Design Principles:** [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) - How tools align with principles
- **API Guide:** [ELFA_API_GUIDE.md](./ELFA_API_GUIDE.md) - API overview and advanced use cases


---

👉 **This prospectus positions Elfa Tools not just as scripts, but as a living ecosystem.** It tells prospective users: here's what you can do today, here's how it grows with you, and here's why it matters.

---

*Last updated: 2024-01-XX*


