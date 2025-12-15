# Elfa Tools - Architecture Diagrams

**Generated:** 2024-12-13  
**Purpose:** Visual representation of system architecture, data flow, and module interactions

> **See also:** [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md) for the conceptual two-path model (Path A: Catalog Tools → Path B: Decision Engine → Decision Moment)

---

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Elfa Tools System                         │
│                   Narrative Intelligence Platform               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         External Data Sources            │
        ├─────────────────────────────────────────┤
        │  • Elfa API (api.elfa.ai)              │
        │  • Binance API (fapi.binance.com)       │
        │  • On-chain APIs (template)             │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         API Client Layer                │
        ├─────────────────────────────────────────┤
        │  • elfa_client.py                       │
        │  • perp_client.py                       │
        │  • onchain_client.py (template)         │
        │  Features:                              │
        │    - Rate limiting                      │
        │    - Caching (5 min TTL)               │
        │    - Error handling                    │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Data Enrichment Layer              │
        ├─────────────────────────────────────────┤
        │  • narrative_enricher.py                │
        │  Computes:                              │
        │    - Velocity (Δ mentions)              │
        │    - Acceleration (Δ velocity)         │
        │    - Account churn                     │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Storage Layer                      │
        ├─────────────────────────────────────────┤
        │  • SQLite (narrative_history.db)        │
        │  • DuckDB (narrative_chronicle.duckdb)  │
        │  • SQLite (alerts_history.db)           │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Analysis & Composition Layer       │
        ├─────────────────────────────────────────┤
        │  • signal_composer.py                   │
        │  • delta_store.py                       │
        │  • alerts_engine.py                     │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Application Layer                  │
        ├─────────────────────────────────────────┤
        │  • narrative_radar.py                    │
        │  • entry_scanner.py                     │
        │  • pre_trade_check.py                   │
        │  • narrative_digest.py                  │
        │  • narrative_heatmap.py                  │
        └─────────────────────────────────────────┘
```

---

## Data Flow: Narrative Radar

```text
User Command: python narrative_radar.py BTC ETH --window 1h
│
├─► narrative_radar.main()
   │
   ├─► For each ticker (BTC, ETH):
   │   │
   │   ├─► elfa_client.get_ticker_narrative_snapshot(ticker, "1h")
   │   │   │
   │   │   ├─► Check cache (miss on first call)
   │   │   ├─► Check rate limit (60 req/60s)
   │   │   ├─► GET https://api.elfa.ai/v2/data/top-mentions
   │   │   │     ?ticker=BTC&timeWindow=1h&page=0&pageSize=10
   │   │   ├─► Parse response → TickerNarrativeSnapshot
   │   │   └─► Cache result (TTL: 300s)
   │   │
   │   └─► narrative_enricher.enrich_snapshot(snapshot)
   │       │
   │       ├─► Query SQLite for last 2 snapshots
   │       ├─► Calculate:
   │       │   • delta_mentions = current - last
   │       │   • acceleration = current_velocity - prev_velocity
   │       │   • new_accounts = current - last (set diff)
   │       │   • lost_accounts = last - current (set diff)
   │       ├─► Store current snapshot to SQLite
   │       └─► Return EnrichedSnapshot
   │
   └─► Display results (CLI table or markdown export)
```

**API Calls:** 2 (one per ticker, if not cached)

---

## Data Flow: Entry Scanner

```text
User Command: python entry_scanner.py BTC ETH
│
├─► entry_scanner.scan_watchlist(["BTC", "ETH"])
   │
   ├─► For each ticker:
   │   │
   │   ├─► entry_scanner.scan_ticker("BTC")
   │   │   │
   │   │   ├─► elfa_client.get_ticker_narrative_snapshot("BTC", "4h")
   │   │   │   └─► API call (if not cached)
   │   │   │
   │   │   ├─► narrative_enricher.enrich_snapshot(snapshot)
   │   │   │   └─► SQLite read/write
   │   │   │
   │   │   ├─► delta_store.insert(enriched)
   │   │   │   └─► DuckDB insert
   │   │   │
   │   │   ├─► delta_store.calculate_velocity("BTC", "4h")
   │   │   │   └─► DuckDB query (last 8 hours)
   │   │   │       • Uses time delta, not snapshot count
   │   │   │
   │   │   ├─► delta_store.detect_anomalies("BTC", "4h")
   │   │   │   └─► DuckDB query (last 48 hours)
   │   │   │       • Z-score calculation
   │   │   │
   │   │   ├─► perp_client.get_perp_market_data("BTC")
   │   │   │   ├─► GET /fapi/v1/premiumIndex?symbol=BTCUSDT
   │   │   │   └─► GET /fapi/v1/ticker/24hr?symbol=BTCUSDT
   │   │   │
   │   │   └─► signal_composer.compose(...)
   │   │       ├─► Score narrative (mindshare + velocity + accounts)
   │   │       ├─► Score market (funding + price + volume)
   │   │       ├─► Score on-chain (if available)
   │   │       ├─► Normalize weights based on available data
   │   │       └─► Calculate composite score & confidence
   │   │
   │   └─► Analyze setups (spike, momentum, anomaly, smart_money)
   │       └─► Calculate conviction score
   │
   └─► Print results sorted by conviction
```

**API Calls:**

- Elfa: 1 per ticker (if not cached)
- Binance: 2 per ticker (if not cached)

---

## Data Flow: Pre-Trade Check

```text
User Command: python pre_trade_check.py BTC long
│
├─► pre_trade_check.check_trade("BTC", "long", "1h")
   │
   ├─► elfa_client.get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
   │   └─► API call (fresh data, no cache)
   │
   ├─► narrative_enricher.enrich_snapshot(snapshot)
   │   └─► SQLite read/write
   │
   ├─► delta_store operations
   │   ├─► calculate_velocity() → DuckDB query
   │   └─► detect_anomalies() → DuckDB query
   │
   ├─► perp_client.get_perp_market_data("BTC")
   │   └─► Binance API calls
   │
   ├─► signal_composer.compose(...)
   │   └─► Generate composite signal
   │
   └─► Validate trade
       ├─► Check narrative velocity (must be positive for long)
       ├─► Check acceleration (must be positive for long)
       ├─► Check composite signal (must be bullish for long)
       └─► Return: APPROVED/BLOCKED with reasoning
```

**API Calls:**

- Elfa: 1 (fresh data, no cache)
- Binance: 2 (if not cached)

---

## Module Interaction Matrix

```text
                    │ elfa │ narr │ delta │ signal │ alerts │ entry │ pre │ perp │ onchain │
                    │client│enrich│ store │composer│ engine │scanner│trade│client│ client  │
────────────────────┼──────┼──────┼───────┼────────┼────────┼───────┼─────┼──────┼─────────┤
elfa_client         │  •   │  ✓   │       │   ✓    │   ✓    │   ✓   │  ✓  │      │         │
narrative_enricher  │  ✓   │  •   │       │   ✓    │   ✓    │   ✓   │  ✓  │      │         │
delta_store         │      │  ✓   │  •    │        │        │   ✓   │  ✓  │      │         │
signal_composer     │      │  ✓   │       │   •    │        │   ✓   │  ✓  │  ✓   │    ✓    │
alerts_engine       │      │  ✓   │       │        │   •    │       │     │      │         │
entry_scanner       │  ✓   │  ✓   │  ✓    │   ✓    │        │   •   │     │  ✓   │         │
pre_trade_check     │  ✓   │  ✓   │  ✓    │   ✓    │        │       │  •  │  ✓   │         │
perp_client         │      │      │       │   ✓    │        │   ✓   │  ✓  │  •   │         │
onchain_client      │      │      │       │   ✓    │        │       │     │      │    •    │

Legend:
  • = Module itself
  ✓ = Uses this module
```

---

## Signal Composition Flow

```text
┌─────────────────┐
│  Narrative Data │
│  (Elfa API)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  Enrichment     │      │  Market Data     │
│  (Velocity,     │      │  (Binance API)   │
│   Acceleration) │      │                  │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └────────┬───────────────┘
                  ▼
         ┌─────────────────┐
         │ Signal Composer │
         │                 │
         │ 1. Score each   │
         │    component    │
         │ 2. Normalize     │
         │    weights       │
         │ 3. Calculate     │
         │    composite     │
         │ 4. Determine     │
         │    confidence    │
         └────────┬─────────┘
                  ▼
         ┌─────────────────┐
         │ Composite Signal │
         │                  │
         │ • Score: -1 to 1 │
         │ • Strength:      │
         │   STRONG_BULLISH │
         │   BULLISH        │
         │   NEUTRAL        │
         │   BEARISH        │
         │   STRONG_BEARISH │
         │   CONFLICTED     │
         │ • Confidence:    │
         │   0.0 to 1.0     │
         └──────────────────┘
```

**Weight Normalization:**

- If all 3 sources available: 40% narrative, 35% market, 25% on-chain
- If only narrative + market: 53% narrative, 47% market
- If only narrative: 100% narrative
- Weights automatically adjust based on available data

---

## Alert System Flow

```text
┌─────────────────┐
│  Alert Rules    │
│  (User-defined) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Alerts Engine  │
│                 │
│  For each rule: │
│  1. Check       │
│     cooldown    │
│     (from DB)   │
│  2. Evaluate    │
│     condition   │
│  3. Fire alert  │
│  4. Save        │
│     cooldown    │
│     (to DB)     │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Console    │ │  Telegram   │ │  Discord    │
│  Channel    │ │  Channel    │ │  Channel    │
└─────────────┘ └─────────────┘ └─────────────┘
         │              │              │
         └──────────────┴──────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  Alert History  │
            │  (SQLite DB)    │
            └─────────────────┘
```

**Cooldown Persistence:**

- Stored in `alert_cooldowns` table
- Persists across restarts
- Prevents spam alerts

---

## Storage Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Storage Layer                         │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   SQLite     │      │    DuckDB    │      │   SQLite     │
│              │      │              │      │              │
│ narrative_   │      │ narrative_   │      │ alerts_      │
│ history.db   │      │ chronicle.   │      │ history.db   │
│              │      │ duckdb       │      │              │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ Tables:      │      │ Tables:      │      │ Tables:      │
│ • snapshots  │      │ • narrative_ │      │ • alert_     │
│              │      │   snapshots  │      │   history    │
│ Purpose:     │      │              │      │ • alert_     │
│ • Store raw  │      │ Purpose:     │      │   cooldowns  │
│   snapshots  │      │ • Historical │      │              │
│ • Compute    │      │   analysis   │      │ Purpose:     │
│   velocity   │      │ • Velocity   │      │ • Alert logs │
│ • Track      │      │   calculation│      │ • Cooldown   │
│   churn      │      │ • Anomaly    │      │   state      │
│              │      │   detection  │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## Rate Limiting & Caching

```text
┌─────────────────────────────────────────────────────────┐
│              Rate Limiting & Caching Layer               │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Elfa Client  │      │ Perp Client  │      │ On-chain     │
│              │      │              │      │ Client       │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ Rate Limit:  │      │ Rate Limit:  │      │ Rate Limit:  │
│ 60 req/60s   │      │ 60 req/60s   │      │ 60 req/60s   │
│              │      │              │      │              │
│ Cache:       │      │ Cache:       │      │ Cache:       │
│ 5 min TTL    │      │ 5 min TTL    │      │ 10 min TTL   │
│              │      │              │      │              │
│ Key Format:  │      │ Key Format:  │      │ Key Format:  │
│ ticker:...   │      │ perp:...     │      │ onchain:...  │
└──────────────┘      └──────────────┘      └──────────────┘
```

**Cache Strategy:**

- In-memory dictionaries
- TTL-based expiration
- Cache key includes ticker + window
- No persistence (cleared on restart)

**Rate Limiting:**

- Client-side tracking
- Per-endpoint limits
- Handles 429 responses
- Automatic cleanup of old entries

---

## Error Handling Flow

```text
┌─────────────────┐
│  API Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Try Request    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────┐
│ 200  │  │  Error   │
│ OK   │  │ Response │
└──┬───┘  └────┬─────┘
   │           │
   │      ┌────┴────┐
   │      │         │
   │      ▼         ▼
   │  ┌──────┐  ┌──────┐
   │  │ 429  │  │ 401  │
   │  │ Rate │  │ Auth │
   │  │Limit │  │Error │
   │  └──┬───┘  └──┬───┘
   │     │         │
   │     └────┬────┘
   │          │
   │          ▼
   │  ┌──────────────┐
   │  │ Return None  │
   │  │ Print Warning│
   │  │ Never Crash  │
   │  └──────────────┘
   │
   ▼
┌──────────────┐
│ Return Data  │
│ or None      │
└──────────────┘
```

**Error Handling Principles:**

- Never raise exceptions
- Always return None on error
- Print warnings (not errors)
- Graceful degradation
- Continue execution

---

## Decision Moment Integration

```text
┌─────────────────────────────────────────────────────────┐
│              Decision Moment System                     │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Decision Moment Policy              │
        │      (decision_moment.py)                │
        ├─────────────────────────────────────────┤
        │  • Boring mode filtering                 │
        │  • Cooldown management                   │
        │  • Velocity threshold checks             │
        │  • Alignment requirements                │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Decision Moment                     │
        │      (Structured Output)                 │
        ├─────────────────────────────────────────┤
        │  • Trigger description                  │
        │  • Contributing signals                 │
        │  • Excluded signals                     │
        │  • Interpretation                      │
        │  • Uncertainty                         │
        │  • Provenance                          │
        └─────────────────────────────────────────┘
```

**Integration Points:**

- Can be generated from `EnrichedSnapshot`
- Can use `CompositeSignal` as input
- Can trigger `AlertsEngine` rules
- Can be stored in `DeltaStore`

---

## Component Dependencies

```text
                    ┌──────────────┐
                    │  elfa_client │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ narrative_   │  │ signal_      │  │ alerts_      │
│ enricher     │  │ composer     │  │ engine       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ delta_store  │  │ entry_       │  │ pre_trade_   │
│              │  │ scanner      │  │ check        │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Dependency Rules:**

- No circular dependencies
- Clear separation of concerns
- Each module can work standalone
- Shared data structures enable composition

---

---

## End of Architecture Diagrams

