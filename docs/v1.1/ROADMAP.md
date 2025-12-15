# Elfa Tools Roadmap

## Vision

**Elfa Tools is a narrative operating system for decision-making under uncertainty.**

It transforms raw narrative signals into actionable insights by structuring information so you can decide with confidence. The tools are designed to be **modular, explainable, robust, and composable** - each component does one job well and works seamlessly with others.

All tools converge on the **Decision Moment**: a structured explanation of why now matters.

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete design philosophy.

---

## Current Status (v1.0.0)

### ✅ Completed

- **Core API Client** (`elfa_client.py`)
  - Authenticated REST API client with environment variable auth
  - Graceful error handling (never crashes)
  - Built-in caching with configurable TTL
  - Rate limit tracking and awareness
  - Audit trails with `source_query` field

- **Narrative Enricher** (`narrative_enricher.py`)
  - SQLite-backed history tracking
  - Velocity computation (change in mentions)
  - Acceleration computation (change in velocity)
  - Account churn tracking (new/lost accounts)
  - Temporal analysis capabilities

- **Narrative Radar** (`narrative_radar.py`)
  - CLI scanner with velocity, acceleration, account churn
  - Markdown export with audit trail
  - Multi-ticker support, caching options
  - Visual indicators (🚀📈↗️➡️↘️📉💥)

- **Co-Heatmaps** (`narrative_heatmap.py`)
  - Account overlap (Jaccard similarity)
  - Velocity correlation matrices
  - Mindshare similarity analysis
  - Account-ticker mention patterns
  - PNG + Markdown table exports

- **Daily Digest** (`narrative_digest.py`)
  - Multi-format outputs: Obsidian, Telegram, Discord, Email, Blog, JSON
  - Insights extraction (top movers, fastest accelerating, mindshare leaders)
  - Aggregated metrics + detailed breakdowns
  - Platform-optimized formatting

---

## Upcoming Features

### 🔄 Phase 1: Signal Generation & Storage

#### Composite Signal Generator

**Status:** ✅ Implemented  
**Priority:** High

Combine multiple data sources into unified signals:

- Narrative velocity/acceleration from Elfa API
- Funding rates (perpetual futures)
- Price action (OHLCV data)
- Configurable signal weights and thresholds
- Output: JSON signals with metadata and confidence scores

**Implementation:**
- ✅ `signal_composer.py` - Multi-source signal fusion
- ✅ Supports TickerNarrativeSnapshot and EnrichedSnapshot
- ✅ Modular signal components (narrative, funding, price)
- ✅ Explainable outputs with evidence and warnings
- ✅ Robust error handling (graceful degradation)

**Design:**

- Modular signal components (narrative, funding, price)
- Composable signal builder pattern
- Explainable outputs (show contributing factors)
- Robust error handling (graceful degradation if data unavailable)

#### Delta Store

**Status:** ✅ Implemented  
**Priority:** High

Persistent storage for historical analysis:

- SQLite/DuckDB backend for time-series data
- Efficient storage of narrative snapshots
- Query interface for historical analysis
- Support for backtesting and pattern detection

**Implementation:**
- ✅ `delta_store.py` - DuckDB-backed time-series store
- ✅ Supports both TickerNarrativeSnapshot and EnrichedSnapshot
- ✅ Velocity calculation and anomaly detection
- ✅ Watchlist summary and cleanup utilities
- ✅ Efficient indexing for time-range queries

**Design:**

- Schema versioning for data migrations
- Efficient indexing for time-range queries
- Delta compression for storage efficiency
- Export capabilities for external analysis

#### Perpetual Futures Client

**Status:** ✅ Implemented  
**Priority:** High

Market data client for perpetual futures:

- Funding rates from exchanges
- Price and volume metrics
- Open interest tracking

**Implementation:**
- ✅ `perp_client.py` - Binance perpetual futures client
- ✅ Funding rate, price, volume data
- ✅ Caching and rate limiting
- ✅ Extensible to other exchanges

#### On-Chain Client

**Status:** 🚧 Template Implemented  
**Priority:** Medium

On-chain metrics client:

- Exchange flows
- Whale activity tracking
- Active address metrics

**Implementation:**
- ✅ `onchain_client.py` - Template/skeleton implementation
- ⚠️ Requires provider integration (Glassnode, CryptoQuant, etc.)
- ✅ Structure ready for implementation

---

### 🔔 Phase 2: Alerts & Automation

#### Alerts Engine

**Status:** ✅ Implemented  
**Priority:** Medium

Configurable alerting system:

- Rule-based alert conditions (velocity thresholds, acceleration spikes, etc.)
- Persistence layer for alert state
- Multi-channel delivery (Discord, Email, Telegram)
- Alert deduplication and rate limiting
- Alert history and audit trail

**Implementation:**
- ✅ `alerts_engine.py` - Rule-based alert system
- ✅ SQLite persistence for alert history
- ✅ Pre-built rule factories (spike, velocity, anomaly, smart money, mindshare)
- ✅ Multi-channel notification support
- ✅ Cooldown management to prevent spam
- ✅ Supports TickerNarrativeSnapshot and EnrichedSnapshot

**Design:**

- YAML/JSON configuration for rules
- Pluggable notification backends
- Alert state management (acknowledged, snoozed, resolved)
- Explainable alerts (show why alert triggered)

#### Bot Adapter

**Status:** Planned  
**Priority:** Medium

Interactive bot interface:

- Telegram/Discord REPL for querying narrative data
- Scheduled alerts delivery
- Command interface for common queries
- Real-time monitoring capabilities

**Design:**

- Modular bot framework (easy to add new commands)
- Rate limiting and abuse prevention
- User authentication/authorization
- Composable with alerts engine

---

### 📊 Phase 3: Integration & Visualization

#### Dashboard Adapter

**Status:** Planned  
**Priority:** Low

Integration layer for external dashboards:

- Blend narrative data with:
  - Perpetual open interest (OI)
  - Funding rates
  - Whale flow data
  - Other on-chain metrics
- Export formats for common dashboard tools
- Real-time data streaming support

**Design:**

- Pluggable data source adapters
- Unified data model for multi-source aggregation
- Efficient data pipeline (caching, batching)
- API endpoints for dashboard consumption

---

## Future Considerations

### Potential Enhancements

- **Machine Learning Integration**
  - Pattern recognition in narrative signals
  - Predictive models for narrative trends
  - Anomaly detection

- **Advanced Analytics**
  - Sentiment analysis integration
  - Topic modeling and clustering
  - Network analysis of account relationships

- **Performance Optimizations**
  - Async/await support for concurrent API calls
  - Distributed caching (Redis support)
  - Batch processing for large-scale analysis

- **Extended Format Support**
  - Additional digest formats (Slack, Notion, etc.)
  - Custom template system for digests
  - Interactive HTML dashboards

---

## Design Principles

All new features must adhere to six core principles:

1. **Narrow** — Each tool does one job well
2. **Explainable** — Show source data, contributing factors, and audit trails
3. **Robust** — Fail gracefully, never crash, handle partial data
4. **Composable** — Tools work standalone and snap together naturally
5. **Signal Layer, Not Oracle** — Provides signals and context, not answers
6. **Transparent Constraints** — Rate limits, caching, and provenance are visible

Every feature must converge on the **Decision Moment**: a structured explanation of why now matters.

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete design philosophy, including quality standards and non-goals.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on contributing to the roadmap and implementation.

---

## Implementation Status Summary

### ✅ Completed (v1.1.0+)

- **Composite Signal Generator** (`signal_composer.py`)
- **Delta Store** (`delta_store.py`) 
- **Alerts Engine** (`alerts_engine.py`)
- **Perpetual Futures Client** (`perp_client.py`)
- **On-Chain Client Template** (`onchain_client.py`)

### 🚧 In Progress / Needs Integration

- On-chain data provider integration (Glassnode/CryptoQuant)
- Bot adapter for Telegram/Discord
- Dashboard adapter

### 📋 Planned

- Bot adapter (Telegram/Discord REPL)
- Dashboard adapter (blend with perp OI, funding, whale flows)
- YAML/JSON rule configuration for alerts
- Advanced analytics features

---

## Last Updated

2024-01-XX
