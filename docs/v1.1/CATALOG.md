# 📘 Elfa Tools Catalog

This catalog organizes the Elfa Tools stack by **category** and **use case**, so you can quickly see what each tool does and how they combine into workflows.

**Why Category-Based Structure?**
- **Separation of concerns:** Each category has clear responsibility
- **Scalability:** Easy to add new tools without clutter
- **Discoverability:** Find tools by function, not filename
- **Extensibility:** Clear mental model for contributors
- **Testing alignment:** Mirror categories in test suite

---

## 🗂️ Categories

### 🔌 Core Data Clients

**Purpose:** Fetch raw data from various sources with built-in safety features.

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `elfa_client.py` | Authenticated Elfa API client | Environment variable auth, caching (5min TTL), rate limit tracking, audit trails (`source_query`) |
| `perp_client.py` | Perpetual futures market data | Funding rates, price, volume from Binance (extensible to other exchanges) |
| `onchain_client.py` | On-chain metrics template | Template for Glassnode/CryptoQuant integration (exchange flows, whale activity) |

**Design:** All clients follow same pattern - never crash, return `None` on errors, include audit trails.

---

### 📊 Analysis Tools

**Purpose:** Transform raw data into actionable insights with temporal and relational analysis.

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `narrative_enricher.py` | Temporal analysis & enrichment | Velocity, acceleration, account churn, SQLite persistence |
| `narrative_radar.py` | Multi-ticker scanner | Batch processing, visual indicators (🚀📈↗️➡️↘️📉💥), markdown export |
| `narrative_heatmap.py` | Relationship discovery | Account overlap (Jaccard), velocity correlation, mindshare similarity, PNG + Markdown |

**Design:** All analysis tools work with `TickerNarrativeSnapshot` and `EnrichedSnapshot` for consistency.

---

### 📤 Output & Signal Tools

**Purpose:** Generate formatted outputs and composite signals for decision-making.

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `narrative_digest.py` | Multi-format daily digest | 6 formats: Obsidian, Telegram, Discord, Email, Blog, JSON |
| `signal_composer.py` | Composite signal generator | Fuses narrative + market + on-chain, confidence scoring, explainable outputs |

**Design:** Outputs are platform-optimized and explainable (show reasoning).

---

### 🤖 Automation Tools

**Purpose:** Automate monitoring, alerting, and workflow execution.

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `alerts_engine.py` | Rule-based alerting | Custom rules, multi-channel (Discord/Email/Telegram), SQLite persistence, cooldown management |
| `delta_store.py` | Historical data storage | DuckDB backend, velocity calculation, anomaly detection, watchlist summaries |
| `morning_routine.py` | Automated morning scan | Combines radar → scanner → digest into single workflow |
| `eod_review.py` | End-of-day analysis | Alert summaries, momentum leaders, daily digest generation |

**Design:** All automation tools are composable and can run standalone or in workflows.

---

### 📈 Trading Workflow Tools

**Purpose:** Complete trading system integration for entry, validation, and monitoring.

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `entry_scanner.py` | Find high-conviction setups | Detects spikes, momentum, anomalies, smart money; ranks by conviction (0-100%) |
| `pre_trade_check.py` | Validate trades before entry | Blocks bad trades, shows warnings/errors/positives, exit code (0=approved, 1=blocked) |
| `position_monitor.py` | Monitor open positions | Continuous monitoring, alerts when narrative moves against position, JSON-based config |

**Design:** All trading tools are explainable (show reasoning) and robust (never crash).

---

### 🔮 Planned Tools

**Purpose:** Future integrations and extensions.

| Tool | Status | Purpose |
|------|--------|---------|
| `bot_adapter.py` | Planned | Interactive bot interface for Telegram/Discord (REPL + scheduled alerts) |
| `dashboard_adapter.py` | Planned | Integration layer for external dashboards (blend with perp OI, funding, whale flows) |

---

## 🚀 Workflow Playbooks

### Daily Narrative Scan

**Use Case:** Morning routine to find opportunities from overnight activity.

**Workflow:**
1. Run `morning_routine.py` → Automated scan of watchlist
   - Or manually: `narrative_radar.py` → `entry_scanner.py` → `narrative_digest.py`
2. Review `entry_scanner.py` results → Find high-conviction setups
3. Use `narrative_heatmap.py` → Discover relationships between tickers
4. Export digest → Obsidian/Telegram for daily review

**Time:** 5 minutes (automated) vs 20 minutes (manual)

**Tools:** `morning_routine.py`, `entry_scanner.py`, `narrative_heatmap.py`, `narrative_digest.py`

---

### Signal Fusion & Alerts

**Use Case:** Combine multiple data sources into actionable signals with automated alerting.

**Workflow:**
1. Generate composite signals with `signal_composer.py`
   - Combines: narrative (Elfa) + market (perp) + on-chain data
2. Store snapshots in `delta_store.py` for historical tracking
3. Configure rules in `alerts_engine.py`
   - Alert on velocity spikes, anomalies, smart money activity
4. Deliver notifications via Discord/Email/Telegram

**Time:** Automated (runs continuously)

**Tools:** `signal_composer.py`, `delta_store.py`, `alerts_engine.py`

---

### Trading System Integration

**Use Case:** Complete trading workflow from opportunity discovery to position monitoring.

**Workflow:**
1. **Morning (7:00 AM):** `morning_routine.py`
   - Scan watchlist → Find entry setups → Generate journal
2. **Throughout Day:** `position_monitor.py` (background)
   - Monitor open positions → Alert on narrative changes
3. **Before Each Trade:** `pre_trade_check.py`
   - Validate trade → Block bad setups → Show reasoning
4. **End of Day (5:00 PM):** `eod_review.py`
   - Review alerts → Check momentum leaders → Learn and iterate

**Time:** 5 min morning + 30 sec per trade + 2 min EOD

**Tools:** `morning_routine.py`, `entry_scanner.py`, `pre_trade_check.py`, `position_monitor.py`, `eod_review.py`

---

### Market + Narrative Integration

**Use Case:** Combine narrative signals with market data for comprehensive analysis.

**Workflow:**
1. Pull funding and price data with `perp_client.py`
2. Combine with narrative signals in `signal_composer.py`
3. Store in `delta_store.py` for historical analysis
4. Generate reports with `narrative_digest.py`
5. (Future) Stream outputs into dashboards via `dashboard_adapter.py`

**Time:** 2-5 minutes per analysis

**Tools:** `perp_client.py`, `signal_composer.py`, `delta_store.py`, `narrative_digest.py`

---

### Research & Backtesting

**Use Case:** Historical analysis and pattern recognition for research.

**Workflow:**
1. Collect data: `elfa_client.py` → Fetch raw narrative snapshots
2. Enrich: `narrative_enricher.py` → Add velocity, acceleration, churn
3. Store: `delta_store.py` → Historical time-series storage
4. Analyze: `delta_store.py` → Velocity calculation, anomaly detection
5. Visualize: `narrative_heatmap.py` → Relationship discovery
6. Report: `narrative_digest.py` → Generate research reports

**Time:** Varies by scope

**Tools:** `elfa_client.py`, `narrative_enricher.py`, `delta_store.py`, `narrative_heatmap.py`, `narrative_digest.py`

---

## 📋 Navigation Guide

### By Category
- **Core Data Clients** → Start here for data fetching
- **Analysis Tools** → Transform data into insights
- **Output & Signal Tools** → Generate reports and signals
- **Automation Tools** → Automate workflows
- **Trading Workflow Tools** → Complete trading system

### By Use Case
- **Daily Scanning** → `morning_routine.py`, `entry_scanner.py`, `narrative_radar.py`
- **Trade Validation** → `pre_trade_check.py`
- **Position Monitoring** → `position_monitor.py`
- **Historical Analysis** → `delta_store.py`, `narrative_enricher.py`
- **Relationship Discovery** → `narrative_heatmap.py`
- **Multi-Source Signals** → `signal_composer.py`
- **Automated Alerts** → `alerts_engine.py`
- **Daily Reports** → `narrative_digest.py`, `eod_review.py`

### By Skill Level
- **Beginner:** `narrative_radar.py`, `narrative_digest.py`, `morning_routine.py`
- **Intermediate:** `entry_scanner.py`, `pre_trade_check.py`, `position_monitor.py`
- **Advanced:** `signal_composer.py`, `alerts_engine.py`, `delta_store.py`

### By Workflow
- **Trading System** → See "Trading System Integration" playbook above
- **Research** → See "Research & Backtesting" playbook above
- **Daily Monitoring** → See "Daily Narrative Scan" playbook above

---

## 🎨 Playful Discovery

**Explore and be inspired:**
- **[GALLERY.md](./GALLERY.md)** - Curated examples of Elfa Tools in action
- **[INSPIRE.md](./INSPIRE.md)** - Creative prompts for thinking differently
- **[ACHIEVEMENTS.md](./ACHIEVEMENTS.md)** - Track your progress and unlock badges

---


## 🔗 Related Documentation

**🚀 Entry Point:**
- **Quickstart:** [QUICKSTART.md](./QUICKSTART.md) - Get started in 5 minutes

**🗺️ Navigation:**
- **Prospectus:** [PROSPECTUS.md](./PROSPECTUS.md) - What Elfa Tools are and why they matter
- **Trading Workflow:** [TRADING_WORKFLOW.md](./TRADING_WORKFLOW.md) - Complete daily trading workflows (playbooks)
- **Roadmap:** [ROADMAP.md](./ROADMAP.md) - Planned features and future vision

**📖 Deep Dive:**
- **Design Principles:** [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) - How tools align with principles
- **API Guide:** [ELFA_API_GUIDE.md](./ELFA_API_GUIDE.md) - API overview and advanced use cases

---

## 💡 Quick Reference

### Most Used Tools

1. **`narrative_radar.py`** - Quick multi-ticker scan
2. **`entry_scanner.py`** - Find entry opportunities
3. **`pre_trade_check.py`** - Validate before trading
4. **`position_monitor.py`** - Monitor open positions
5. **`narrative_digest.py`** - Generate daily reports

### Workflow Scripts

- **`morning_routine.py`** - Complete morning scan (5 min)
- **`eod_review.py`** - End-of-day analysis (2 min)

### Library Modules

- **`elfa_client.py`** - Core API client (used by all tools)
- **`narrative_enricher.py`** - Temporal analysis (used by most tools)
- **`signal_composer.py`** - Signal fusion (used by trading tools)
- **`delta_store.py`** - Historical storage (used by analysis tools)

---

*Last updated: 2024-01-XX*

