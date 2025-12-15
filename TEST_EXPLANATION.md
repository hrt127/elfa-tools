# Test Suite Explanation

## What Do The Tests Accomplish?

The test suite validates that **Elfa Tools** works correctly and reliably. Here's what each category tests:

### 1. **Unit Tests** (`tests/test_*.py`)

Test individual components in isolation:

#### `test_elfa_client.py` (~25 tests)
- ✅ **API Integration**: Verifies the Elfa API client fetches data correctly
- ✅ **Caching**: Ensures data is cached for 5 minutes (reduces API calls)
- ✅ **Rate Limiting**: Prevents exceeding API limits (60 req/60s)
- ✅ **Error Handling**: Gracefully handles network errors, 404s, rate limits
- ✅ **Data Parsing**: Correctly extracts mentions, mindshare, smart accounts from API responses

**What it ensures**: The API client never crashes, respects rate limits, and returns valid data.

#### `test_narrative_enricher.py` (~15 tests)
- ✅ **Velocity Calculation**: Computes change in mentions between snapshots
- ✅ **Acceleration**: Calculates second derivative (change in velocity)
- ✅ **Account Churn**: Tracks new/lost smart accounts
- ✅ **Database Persistence**: Stores snapshots in SQLite for history
- ✅ **Edge Cases**: Handles first snapshot, missing data, negative deltas

**What it ensures**: Temporal analysis (velocity/acceleration) works correctly and data persists.

#### `test_narrative_radar.py` (~20 tests)
- ✅ **CLI Display**: Formats data with visual indicators (🚀📈↗️➡️↘️📉💥)
- ✅ **Markdown Export**: Generates audit trail reports
- ✅ **Multi-Ticker Support**: Handles multiple tickers in one scan
- ✅ **Error Handling**: Gracefully handles failed tickers

**What it ensures**: The CLI tool displays data correctly and exports reports properly.

#### `test_decision_moment.py` (~30 tests)
- ✅ **Decision Moment Creation**: Structures "why now matters" explanations
- ✅ **Policy Engine**: Filters boring vs. significant changes
- ✅ **Cooldown Management**: Prevents spam (won't surface same moment twice)
- ✅ **Serialization**: Converts to/from JSON for storage
- ✅ **Explanation Generation**: Creates human-readable explanations

**What it ensures**: Decision Moments are surfaced correctly and explainable.

#### `test_alerts_engine.py` (~30 tests)
- ✅ **Rule Triggering**: Alerts fire when conditions are met
- ✅ **Cooldown Persistence**: Prevents duplicate alerts (stored in SQLite)
- ✅ **Multi-Channel**: Supports console, Telegram, Discord notifications
- ✅ **Data Normalization**: Works with TickerNarrativeSnapshot, EnrichedSnapshot, or dicts
- ✅ **Rule Types**: Tests spike, velocity, anomaly, smart_money, mindshare rules

**What it ensures**: Alert system works reliably and doesn't spam users.

#### `test_delta_store.py` (~25 tests)
- ✅ **Snapshot Storage**: Stores data in DuckDB correctly
- ✅ **Velocity Calculation**: Time-based velocity (not just snapshot count)
- ✅ **Anomaly Detection**: Z-score based statistical anomaly detection
- ✅ **Historical Queries**: Retrieves data for time ranges
- ✅ **Watchlist Summary**: Multi-ticker analysis sorted by momentum

**What it ensures**: Historical data storage and analysis works correctly.

#### `test_signal_composer.py` (~20 tests)
- ✅ **Signal Fusion**: Combines narrative + market + on-chain data
- ✅ **Weight Normalization**: Adjusts weights when data sources unavailable
- ✅ **Confidence Scoring**: Calculates signal confidence (0-1)
- ✅ **Signal Classification**: STRONG_BULLISH, BULLISH, NEUTRAL, BEARISH, etc.
- ✅ **Graceful Degradation**: Works even if some data sources fail

**What it ensures**: Multi-source signal fusion works correctly.

#### `test_rule_config_loader.py` (~15 tests)
- ✅ **YAML Loading**: Loads alert rules from YAML config files
- ✅ **JSON Loading**: Loads alert rules from JSON config files
- ✅ **Rule Type Parsing**: Supports spike, velocity, anomaly, smart_money, mindshare
- ✅ **Error Handling**: Handles invalid configs gracefully

**What it ensures**: Configuration file support works correctly.

### 2. **Integration Tests** (`tests/integration/`)

Test complete workflows end-to-end:

#### `test_narrative_workflow.py` (~10 tests)
- ✅ **Fetch → Enrich**: Tests complete flow from API to enriched data
- ✅ **Account Churn Tracking**: Verifies new/lost accounts are detected
- ✅ **Decision Moment Creation**: Tests creating Decision Moments from enriched data
- ✅ **Boring Mode**: Verifies small changes are filtered out

**What it ensures**: The complete narrative analysis pipeline works.

#### `test_entry_scanner_workflow.py` (~8 tests)
- ✅ **Setup Detection**: Finds spike, momentum, anomaly, smart_money setups
- ✅ **Multi-Ticker Scanning**: Scans multiple tickers and ranks by conviction
- ✅ **Result Ranking**: Results sorted by conviction score
- ✅ **Failed Ticker Handling**: Gracefully handles tickers with no data

**What it ensures**: Entry scanner finds high-conviction opportunities correctly.

#### `test_pre_trade_check_workflow.py` (~6 tests)
- ✅ **Long Trade Validation**: Validates long trades based on narrative state
- ✅ **Short Trade Validation**: Validates short trades
- ✅ **Weak Signal Blocking**: Blocks trades when signals are too weak
- ✅ **Confidence Validation**: Ensures trades have sufficient confidence

**What it ensures**: Pre-trade validation works correctly.

---

## When Are We Getting Data Points?

### Data Collection Flow

```
User Action / Scheduled Task
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 1. OBSERVE (Fetch Raw Data)                            │
│                                                         │
│ • elfa_client.get_ticker_narrative_snapshot("BTC")     │
│   └─► API Call: GET /v2/data/top-mentions?ticker=BTC  │
│   └─► Returns: TickerNarrativeSnapshot                 │
│   └─► Cached: 5 minutes (300s)                         │
│   └─► Rate Limited: 60 requests per 60 seconds         │
│                                                         │
│ • perp_client.get_perp_market_data("BTC")              │
│   └─► API Call: Binance Futures API                   │
│   └─► Returns: Funding rate, price, volume            │
│                                                         │
│ • onchain_client.get_onchain_data("BTC")               │
│   └─► API Call: Glassnode API (if configured)         │
│   └─► Returns: Exchange flows, active addresses        │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 2. ENRICH (Add Temporal Context)                       │
│                                                         │
│ • narrative_enricher.enrich_snapshot(snapshot)          │
│   └─► Reads: Previous snapshot from SQLite             │
│   └─► Calculates: Velocity (Δ mentions)                │
│   └─► Calculates: Acceleration (Δ velocity)             │
│   └─► Tracks: Account churn (new/lost accounts)         │
│   └─► Stores: Current snapshot to SQLite              │
│                                                         │
│ • delta_store.insert(enriched)                          │
│   └─► Stores: Snapshot to DuckDB                       │
│   └─► Enables: Historical analysis                     │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 3. ANALYZE (Historical Context)                        │
│                                                         │
│ • delta_store.calculate_velocity("BTC", "4h")           │
│   └─► Queries: Last 8 hours of data                    │
│   └─► Calculates: Time-based velocity                  │
│                                                         │
│ • delta_store.detect_anomalies("BTC", "4h")            │
│   └─► Queries: Last 48 hours of data                   │
│   └─► Calculates: Z-score (statistical anomaly)        │
└─────────────────────────────────────────────────────────┘
```

### When Data Points Are Collected

#### **Manual/On-Demand Collection**

1. **CLI Commands**:
   ```bash
   # Fetch data for tickers right now
   python narrative_radar.py BTC ETH SOL --window 4h
   ```
   - **When**: When you run the command
   - **Data Points**: Fetches current snapshot for each ticker
   - **Caching**: Uses cache if data is < 5 minutes old

2. **Python Scripts**:
   ```python
   from elfa_client import get_ticker_narrative_snapshot
   
   # Fetch data programmatically
   snapshot = get_ticker_narrative_snapshot("BTC", "4h")
   ```
   - **When**: When your script calls the function
   - **Data Points**: One snapshot per call
   - **Caching**: Respects cache unless `use_cache=False`

#### **Automated/Scheduled Collection**

1. **Morning Routine** (`optional/morning_routine.py`):
   ```bash
   # Run daily at 9 AM
   python optional/morning_routine.py --watchlist watchlist.txt
   ```
   - **When**: Scheduled (cron job, systemd timer, etc.)
   - **Data Points**: Fetches data for all tickers in watchlist
   - **Frequency**: Once per day (configurable)

2. **Position Monitor** (`optional/position_monitor.py`):
   ```bash
   # Monitor positions continuously
   python optional/position_monitor.py --interval 300
   ```
   - **When**: Runs continuously, checks every N seconds
   - **Data Points**: Fetches data for tickers in your positions
   - **Frequency**: Every 5 minutes (300s) by default

3. **Alerts Engine** (`optional/alerts_engine.py`):
   ```python
   # Check alerts periodically
   engine.check_all("BTC", enriched_snapshot)
   ```
   - **When**: When you call `check_all()` (can be scheduled)
   - **Data Points**: Uses already-fetched enriched snapshot
   - **Frequency**: As often as you call it

### Data Point Frequency

| Component | Frequency | Cache TTL | Rate Limit |
|-----------|-----------|-----------|------------|
| **Elfa API** | On-demand | 5 minutes | 60 req/60s |
| **Binance API** | On-demand | 5 minutes | 1200 req/min |
| **Glassnode API** | On-demand | 10 minutes | 10 req/min |
| **SQLite History** | Every enrichment | Persistent | N/A |
| **DuckDB Store** | Every enrichment | Persistent | N/A |

### Example: Complete Data Collection Timeline

```
00:00 - Morning routine runs
        ├─► Fetches BTC, ETH, SOL (3 API calls to Elfa)
        ├─► Enriches each (3 SQLite writes)
        ├─► Stores in DuckDB (3 DuckDB inserts)
        └─► Generates daily digest

00:05 - Position monitor checks (if running)
        ├─► Fetches BTC (cached, no API call)
        ├─► Checks if narrative changed
        └─► Alerts if position at risk

00:10 - User runs narrative_radar manually
        ├─► Fetches BTC (cached, no API call)
        ├─► Fetches ETH (cached, no API call)
        └─► Fetches SOL (cached, no API call)

00:15 - Cache expires (5 minutes)
        └─► Next fetch will hit API

00:20 - User runs narrative_radar again
        ├─► Fetches BTC (API call - cache expired)
        ├─► Fetches ETH (API call - cache expired)
        └─► Fetches SOL (API call - cache expired)
```

### Key Points

1. **Data is fetched on-demand**, not continuously polled
2. **Caching reduces API calls** (5-10 minute TTL)
3. **Rate limiting prevents API abuse** (respects API limits)
4. **History is stored locally** (SQLite + DuckDB)
5. **Enrichment happens automatically** when you fetch data
6. **Historical analysis queries local database**, not API

### When to Fetch Data

- **Before making a trade**: Use `pre_trade_check.py`
- **Finding opportunities**: Use `entry_scanner.py`
- **Daily review**: Use `morning_routine.py`
- **Monitoring positions**: Use `position_monitor.py`
- **Quick check**: Use `narrative_radar.py`

---

## Summary

**Tests ensure**:
- ✅ Components work correctly in isolation
- ✅ Workflows work end-to-end
- ✅ Error handling is graceful
- ✅ Data persists correctly
- ✅ Calculations are accurate

**Data points are collected**:
- 📊 **On-demand**: When you run commands or scripts
- ⏰ **Scheduled**: Via cron jobs or systemd timers
- 🔄 **Continuously**: Via position monitor (if running)
- 💾 **Cached**: 5-10 minutes to reduce API calls
- 📈 **Stored**: In SQLite (history) and DuckDB (analysis)

The system is designed to be **efficient** (caching), **respectful** (rate limiting), and **reliable** (never crashes, graceful errors).

