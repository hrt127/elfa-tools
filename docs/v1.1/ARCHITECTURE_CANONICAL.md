# Elfa Narrative OS — Canonical Architecture Diagram

**ASCII Architecture** — How modules connect and data flows

---

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Elfa Narrative OS                             │
│              Decision-Making Under Uncertainty                   │
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
        │    THE NARRATIVE OS LOOP (Canonical)     │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   OBSERVE    │      │    ENRICH     │      │    DECIDE     │
│              │      │               │      │               │
│ elfa_client  │─────▶│ narrative_    │─────▶│ signal_       │
│ perp_client  │      │ enricher      │      │ composer      │
│ onchain_     │      │ delta_store   │      │               │
│ client       │      │               │      │               │
└──────────────┘      └───────────────┘      └───────────────┘
        │                     │                     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │              GATE                        │
        │                                          │
        │  decision_moment.py                      │
        │  ┌────────────────────────────────────┐ │
        │  │ DecisionMomentPolicy                │ │
        │  │  • Cooldown check                   │ │
        │  │  • Boring mode                      │ │
        │  │  • Velocity threshold              │ │
        │  │  • Alignment requirement            │ │
        │  └────────────────────────────────────┘ │
        └─────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐
    │   EXPLAIN        │      │   SUPPRESSED     │
    │                  │      │   (Silent)       │
    │ dm.explain()     │      │   (Logged)       │
    └────────┬─────────┘      └──────────────────┘
             │
             ▼
    ┌──────────────────┐
    │   INTERRUPT       │
    │                   │
    │ alerts_engine     │
    │  • Telegram       │
    │  • Discord        │
    │  • Console        │
    └───────────────────┘
```

---

## Data Flow: Complete Loop

```text
User/Trigger
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. OBSERVE                                                   │
│                                                              │
│  elfa_client.get_ticker_narrative_snapshot()                │
│    ├─► GET /v2/data/top-mentions?ticker=BTC&timeWindow=1h   │
│    ├─► Check cache (TTL: 300s)                              │
│    ├─► Check rate limit (60 req/60s)                         │
│    └─► Return TickerNarrativeSnapshot                        │
│                                                              │
│  perp_client.get_perp_market_data()                         │
│    ├─► GET /fapi/v1/premiumIndex?symbol=BTCUSDT            │
│    ├─► GET /fapi/v1/ticker/24hr?symbol=BTCUSDT             │
│    └─► Return MarketData dict                                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ENRICH                                                    │
│                                                              │
│  narrative_enricher.enrich_snapshot()                       │
│    ├─► Query SQLite: last 2 snapshots                       │
│    ├─► Calculate:                                            │
│    │   • delta_mentions = current - last                    │
│    │   • acceleration = current_velocity - prev_velocity    │
│    │   • new_accounts = set(current) - set(last)            │
│    │   • lost_accounts = set(last) - set(current)           │
│    ├─► Store snapshot to SQLite                             │
│    └─► Return EnrichedSnapshot                               │
│                                                              │
│  delta_store.insert()                                        │
│    └─► Insert to DuckDB (narrative_chronicle.duckdb)       │
│                                                              │
│  delta_store.calculate_velocity()                            │
│    └─► Query DuckDB: last 8 hours, compute time-based vel   │
│                                                              │
│  delta_store.detect_anomalies()                             │
│    └─► Query DuckDB: last 48 hours, compute Z-score          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. DECIDE                                                    │
│                                                              │
│  signal_composer.compose()                                   │
│    ├─► Score narrative (mindshare + velocity + accounts)    │
│    ├─► Score market (funding + price + volume)               │
│    ├─► Score on-chain (if available)                         │
│    ├─► Normalize weights based on available data             │
│    ├─► Calculate composite score                              │
│    ├─► Calculate confidence (agreement-based)                │
│    └─► Return CompositeSignal                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. GATE                                                      │
│                                                              │
│  Create DecisionMoment from CompositeSignal                  │
│                                                              │
│  DecisionMomentPolicy.should_trigger(dm)                    │
│    ├─► Check cooldown (from _last_moment dict)               │
│    ├─► Check min_signals (if boring_mode)                    │
│    ├─► Check min_velocity_multiplier (if boring_mode)        │
│    ├─► Check require_alignment (if boring_mode)              │
│    ├─► Check allow_recurring_patterns (if boring_mode)       │
│    └─► Return True/False                                     │
│                                                              │
│  If True:  → EXPLAIN                                         │
│  If False: → SUPPRESSED (logged, no alert)                   │
└─────────────────────────────────────────────────────────────┘
    │
    ├───────────────┬───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│ EXPLAIN │  │SUPPRESSED│  │  (End)       │
│         │  │          │  │              │
│ dm.     │  │ Logged   │  │              │
│ explain()│  │ to DB    │  │              │
└────┬────┘  └──────────┘  └──────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. INTERRUPT                                                  │
│                                                              │
│  alerts_engine.check_all()                                   │
│    ├─► Evaluate all AlertRules                              │
│    ├─► Check rule cooldowns (from alert_cooldowns table)    │
│    ├─► Fire alerts through channels:                         │
│    │   • console_channel()                                  │
│    │   • telegram_channel()                                 │
│    │   • discord_channel()                                  │
│    ├─► Save to alert_history table                          │
│    ├─► Save cooldown to alert_cooldowns table               │
│    └─► Update DecisionMomentPolicy._last_moment             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Human Judgment Begins
```

---

## Module Dependency Graph

```text
                    ┌──────────────┐
                    │ elfa_client  │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ narrative_   │  │ signal_     │  │ alerts_     │
│ enricher     │  │ composer     │  │ engine       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ delta_store  │  │ decision_    │  │ (End)        │
│              │  │ moment       │  │              │
└──────────────┘  └──────────────┘  └──────────────┘

Dependency Rules:
  • No circular dependencies
  • Clear separation of concerns
  • Each module can work standalone
  • Shared data structures enable composition
```

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

---

## Error Handling Flow

```text
┌─────────────────┐
│  API Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Try Request   │
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

Error Handling Principles:
  • Never raise exceptions
  • Always return None on error
  • Print warnings (not errors)
  • Graceful degradation
  • Continue execution
```

---

*End of Canonical Architecture Diagram*
