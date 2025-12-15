# Elfa Tools - Code Analysis & Review

**Generated:** 2024-12-13  
**Scope:** Complete codebase analysis covering logic, interactions, and API usage

---

## Executive Summary

Elfa Tools is a well-architected narrative intelligence system following strong design principles. The codebase demonstrates:

- ✅ **Modular design** with clear separation of concerns
- ✅ **Robust error handling** (never crashes, graceful degradation)
- ✅ **Explainable outputs** with audit trails and provenance
- ✅ **Composable architecture** enabling flexible workflows

**Key Findings:**

- Single external API dependency: Elfa API (`api.elfa.ai`)
- Secondary API: Binance (for perpetual futures data)
- On-chain data client is a template (not implemented)
- Rate limiting and caching implemented consistently
- SQLite (history) and DuckDB (delta store) for persistence
- Potential issue: Debug print statements in production code


---

## Architecture Overview

### Data Flow

```text
┌─────────────────┐
│  elfa_client    │ ──> GET /v2/data/top-mentions
│  (API Layer)    │     Returns: TickerNarrativeSnapshot
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ narrative_      │ ──> SQLite (narrative_history.db)
│ enricher        │     Computes: velocity, acceleration, churn
└────────┬────────┘     Returns: EnrichedSnapshot
         │
         ├─────────────────┬──────────────────┐
         ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ narrative_   │  │ delta_store  │  │ signal_      │
│ radar        │  │ (DuckDB)      │  │ composer     │
└──────────────┘  └──────────────┘  └──────┬───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │ Composite    │
                                    │ Signal       │
                                    └──────────────┘
```

### Core Modules

1. **elfa_client.py** - API client for Elfa narrative data
2. **narrative_enricher.py** - Temporal analysis (velocity, acceleration, churn)
3. **narrative_radar.py** - CLI scanner for multiple tickers
4. **signal_composer.py** - Multi-source signal fusion
5. **delta_store.py** - Historical analysis (DuckDB)
6. **alerts_engine.py** - Rule-based alerting system
7. **entry_scanner.py** - Entry opportunity detection
8. **pre_trade_check.py** - Trade validation
9. **perp_client.py** - Binance perpetual futures data
10. **onchain_client.py** - Template (not implemented)

---

## API Calls Analysis

### 1. Elfa API (`elfa_client.py`)

**Endpoint:** `GET https://api.elfa.ai/v2/data/top-mentions`

**Parameters:**

- `ticker`: Ticker symbol (e.g., "BTC")
- `timeWindow`: Time window ("1h", "4h", "24h")
- `page`: Page number (default: 0)
- `pageSize`: Results per page (default: 10)

**Headers:**

- `x-elfa-api-key`: API key from `ELFA_API_KEY` env var
- `Content-Type`: application/json

**Rate Limiting:**

- Client-side tracking: 60 requests per 60 seconds per endpoint
- Server-side: Handles 429 responses with `Retry-After` header
- **Issue:** Global rate limit tracker shared across all endpoints (may be too restrictive)

**Caching:**

- TTL: 300 seconds (5 minutes)
- Cache key: `ticker:{TICKER}:window:{WINDOW}`
- **Issue:** Cache is in-memory only (lost on restart)

**Response Handling:**

- Graceful degradation on all errors
- Flexible field mapping (handles multiple response formats)
- Returns `None` on failure (never raises exceptions)

**Data Extracted:**

- `total_mentions`: Integer count
- `mindshare_score`: Float (0-1)
- `top_smart_accounts`: List of account identifiers (max 3)
- `source_query`: Audit trail string

**Potential Issues:**
1. **Debug prints in production** (lines 137-138):
   ```python
   print("Elfa top-mentions status:", response.status_code)
   print("Body snippet:", response.text[:300])
   ```
   Should be removed or made conditional on debug flag.

2. **Fallback to first result** (line 181-182):
   If ticker not found, uses first result. This could return wrong ticker data.

3. **No request timeout handling** beyond 10s timeout - should handle slow responses better.

---

### 2. Binance API (`perp_client.py`)

**Endpoints:**
1. `GET https://fapi.binance.com/fapi/v1/premiumIndex`
   - Returns: Funding rate (8h, converted to daily)
   - Parameters: `symbol` (e.g., "BTCUSDT")

2. `GET https://fapi.binance.com/fapi/v1/ticker/24hr`
   - Returns: 24h price, volume, price change
   - Parameters: `symbol`

**Rate Limiting:**
- Same pattern as Elfa client: 60 req/60s
- **Issue:** Separate tracker per endpoint, but no coordination

**Caching:**
- TTL: 300 seconds (5 minutes)
- Cache key: `perp:{TICKER}`

**Data Extracted:**
- `funding_rate`: Daily funding rate (float)
- `price`: Current price (float)
- `price_change_24h`: 24h % change (float)
- `volume_24h`: 24h volume (float)
- `volume_ratio`: Always 1.0 (not calculated - needs historical data)

**Issues:**
1. **volume_ratio always 1.0** - Not implemented, requires historical data
2. **No error differentiation** - All errors return None, making debugging harder
3. **Symbol format hardcoded** - Assumes USDT pairs only

---

### 3. On-Chain Client (`onchain_client.py`)

**Status:** Template/Placeholder - Not Implemented

**Intended Providers:**
- Glassnode (template provided)
- CryptoQuant (template provided)

**Required Data:**
- Exchange net flow (BTC)
- Whale balance changes
- Active addresses
- Transaction counts

**Impact:** `signal_composer` gracefully degrades when on-chain data is None.

---

## Module Interactions

### Interaction Patterns

#### 1. Fetch → Enrich → Store Pattern

**Example: `narrative_radar.py`**

```python
snap = get_ticker_narrative_snapshot(ticker, window)  # elfa_client
enriched = enricher.enrich_snapshot(snap)             # narrative_enricher
# enricher automatically stores to SQLite
```

**Flow:**

1. `elfa_client.get_ticker_narrative_snapshot()` → API call
2. `narrative_enricher.enrich_snapshot()` → Computes velocity/acceleration
3. `narrative_enricher.store_snapshot()` → Persists to SQLite
4. Returns `EnrichedSnapshot` with temporal metrics

**Data Transformation:**

- `TickerNarrativeSnapshot` → `EnrichedSnapshot`
- Adds: `delta_mentions`, `acceleration`, `new_accounts`, `lost_accounts`


---

#### 2. Multi-Source Signal Composition

**Example: `entry_scanner.py`**

```python
snapshot = get_ticker_narrative_snapshot(ticker)     # Elfa API
enriched = enricher.enrich_snapshot(snapshot)         # Enrichment
market_data = get_perp_market_data(ticker)            # Binance API
signal = composer.compose(                            # Signal fusion
    narrative_data=enriched,
    market_data=market_data,
    onchain_data=None  # Not implemented
)
```

**Signal Composer Logic:**

- Narrative weight: 0.4 (40%)
- Market weight: 0.35 (35%)
- On-chain weight: 0.25 (25%)
- **Issue:** Weights don't adjust when data is missing (e.g., on-chain = None)

**Scoring Logic:**

- Narrative: Mindshare (0-0.4) + Velocity (-0.3 to 0.3) + Smart accounts (0-0.3)
- Market: Funding rate (-0.4 to 0.4) + Price momentum (-0.3 to 0.3) + Volume (0-0.3)
- On-chain: Exchange flow (-0.4 to 0.4) + Whale activity (-0.3 to 0.3) + Active addresses (0-0.3)

**Confidence Calculation:**

- Based on directional agreement between components
- Mixed signals = low confidence (0.3)
- High agreement + high magnitude = high confidence


---

#### 3. Historical Analysis Pattern

**Example: `delta_store.py`**

```python
store.insert(enriched)                                # Store to DuckDB
velocity_data = store.calculate_velocity(ticker)      # Historical analysis
anomaly = store.detect_anomalies(ticker)              # Statistical detection
```

**Velocity Calculation:**

- Compares current vs previous snapshot
- Computes: `mentions_delta`, `mentions_velocity`, `mindshare_velocity`
- **Issue:** Velocity calculation divides by `len(history)` which may not represent actual time delta

**Anomaly Detection:**

- Uses Z-score: `(current - mean) / stddev`
- Threshold: 2.0 standard deviations (configurable)
- Requires minimum 10 data points
- **Issue:** Uses all history except last point for mean/std, which could be stale


---

#### 4. Alert Rule Evaluation

**Example: `alerts_engine.py`**
```python
engine.add_rule(RuleFactory.spike_detector("BTC", threshold=60))
engine.check_all("BTC", enriched_snapshot)
```

**Rule Evaluation:**
1. Normalize data (handles multiple input types)
2. Check cooldown (prevents spam)
3. Evaluate condition (lambda function)
4. Fire alert through all channels
5. Persist to SQLite

**Cooldown Management:**
- Per-rule cooldown (default: 15 minutes)
- Stored in rule object (not persistent across restarts)
- **Issue:** Cooldown state lost on restart (could cause spam)

---

## Logic Review

### Strengths

1. **Robust Error Handling**

   - All functions return `None` on error (never raise)
   - Try-except blocks at multiple levels
   - Graceful degradation when data unavailable

2. **Explainable Design**

   - `source_query` field tracks API calls
   - `explain()` methods on signals
   - Clear reasoning in outputs

3. **Composable Architecture**

   - Modules work standalone
   - Shared data structures enable composition
   - No tight coupling

4. **Rate Limit Awareness**

   - Client-side tracking prevents hitting limits
   - Handles server-side 429 responses
   - Cache reduces API calls


### Issues & Concerns

#### 1. **Debug Print Statements**

**Location:** `elfa_client.py:137-138`

```python
print("Elfa top-mentions status:", response.status_code)
print("Body snippet:", response.text[:300])
```

**Impact:** Clutters output in production, potential security issue (exposes API responses)

**Recommendation:** Remove or make conditional on debug flag.


---

#### 2. **Fallback Logic Risk**

**Location:** `elfa_client.py:181-182`

```python
if ticker_data is None and results:
    ticker_data = results[0] if isinstance(results[0], dict) else None
```

**Issue:** If requested ticker not found, uses first result. Could return wrong ticker data.

**Recommendation:** Only use fallback if explicitly requested, or return None.


---

#### 3. **Velocity Calculation Logic**

**Location:** `delta_store.py:218`

```python
mentions_velocity = mentions_delta / len(history) if len(history) > 0 else 0
```

**Issue:** Divides by number of snapshots, not actual time delta. If snapshots are irregular, velocity is incorrect.

**Recommendation:** Use actual time delta between first and last snapshot.


---

#### 4. **Anomaly Detection Staleness**

**Location:** `delta_store.py:262`

```python
mentions = [h['mentions'] for h in history[:-1]]  # Excludes current
```

**Issue:** Uses all history except current for mean/std. If history is old, mean may be stale.

**Recommendation:** Use rolling window (e.g., last 24 hours) or exponential weighting.


---

#### 5. **Signal Composer Weight Adjustment**

**Location:** `signal_composer.py:138-142`

```python
composite_score = (
    narrative_score * self.narrative_weight +
    market_score * self.market_weight +
    onchain_score * self.onchain_weight
)
```

**Issue:** Weights don't adjust when data is missing. If on-chain data is None (score=0), it still gets 25% weight.

**Recommendation:** Normalize weights based on available data sources.


---

#### 6. **Cooldown State Persistence**

**Location:** `alerts_engine.py:44-46`

```python
if self.last_triggered:
    minutes_since = (datetime.now() - self.last_triggered).total_seconds() / 60
    if minutes_since < self.cooldown_minutes:
        return None
```

**Issue:** Cooldown state stored in memory. Lost on restart, could cause spam.

**Recommendation:** Persist cooldown state to database.


---

#### 7. **Acceleration Calculation Edge Case**

**Location:** `narrative_enricher.py:142-148`

```python
if prev_snap:
    prev_velocity = last_snap.total_mentions - prev_snap.total_mentions
    current_velocity = delta_mentions
    acceleration = current_velocity - prev_velocity
else:
    acceleration = delta_mentions  # First time = velocity
```

**Issue:** When only 2 snapshots exist, acceleration = velocity (not true acceleration).

**Recommendation:** Return None or 0 for acceleration until 3+ snapshots available.


---

#### 8. **Account Churn Logic**

**Location:** `narrative_enricher.py:150-154`

```python
last_accounts = set(last_snap.top_smart_accounts or [])
curr_accounts = set(snap.top_smart_accounts or [])
new_accounts = list(curr_accounts - last_accounts)
lost_accounts = list(last_accounts - curr_accounts)
```

**Issue:** Only compares top 3 accounts. If account drops from #4 to #5, not detected as "lost".

**Recommendation:** Track more accounts or use separate API for full account list.


---

#### 9. **Cache Invalidation**

**Location:** Multiple files (in-memory caches)

**Issue:** No cache invalidation strategy. Cache persists until TTL expires, even if data changes.

**Recommendation:** Add cache invalidation on write operations or manual clear.

---

#### 10. **Rate Limit Tracker Memory**

**Location:** `elfa_client.py:10`, `perp_client.py:23`

**Issue:** Global rate limit trackers grow unbounded (only cleaned per-request).

**Recommendation:** Periodic cleanup of old entries or use bounded data structure.

---

## Data Flow Examples

### Example 1: Narrative Radar Scan

```text
User: python narrative_radar.py BTC ETH --window 1h

1. narrative_radar.main()
   └─> For each ticker:
       ├─> elfa_client.get_ticker_narrative_snapshot("BTC", "1h")
       │   ├─> Check cache (miss)
       │   ├─> Check rate limit (OK)
       │   ├─> GET https://api.elfa.ai/v2/data/top-mentions?ticker=BTC&timeWindow=1h
       │   ├─> Parse response → TickerNarrativeSnapshot
       │   └─> Cache result (TTL: 300s)
       │
       └─> narrative_enricher.enrich_snapshot(snapshot)
           ├─> Get last 2 snapshots from SQLite
           ├─> Calculate: delta_mentions, acceleration, churn
           ├─> Store current snapshot to SQLite
           └─> Return EnrichedSnapshot

2. Display results (CLI or markdown export)
```

**API Calls:** 2 (one per ticker, if not cached)

---

### Example 2: Entry Scanner

```text
User: python entry_scanner.py BTC ETH

1. entry_scanner.scan_ticker("BTC")
   ├─> elfa_client.get_ticker_narrative_snapshot("BTC", "4h")
   │   └─> API call (if not cached)
   │
   ├─> narrative_enricher.enrich_snapshot(snapshot)
   │   └─> SQLite read/write
   │
   ├─> delta_store.insert(enriched)
   │   └─> DuckDB insert
   │
   ├─> delta_store.calculate_velocity("BTC", "4h")
   │   └─> DuckDB query (last 8 hours)
   │
   ├─> delta_store.detect_anomalies("BTC", "4h")
   │   └─> DuckDB query (last 48 hours) + statistical analysis
   │
   ├─> perp_client.get_perp_market_data("BTC")
   │   ├─> GET https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT
   │   └─> GET https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT
   │
   └─> signal_composer.compose(...)
       └─> Calculate composite signal

2. Analyze setups and print results
```

**API Calls:**

- Elfa: 1 (if not cached)
- Binance: 2 per ticker (if not cached)


---

### Example 3: Pre-Trade Check

```text
User: python pre_trade_check.py BTC long

1. pre_trade_check.check_trade("BTC", "long")
   ├─> elfa_client.get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
   │   └─> API call (cache disabled for fresh data)
   │
   ├─> narrative_enricher.enrich_snapshot(snapshot)
   │   └─> SQLite read/write
   │
   ├─> delta_store operations (velocity, anomalies)
   │   └─> DuckDB queries
   │
   ├─> perp_client.get_perp_market_data("BTC")
   │   └─> Binance API calls
   │
   └─> signal_composer.compose(...)
       └─> Generate composite signal

2. Validate trade based on narrative state
   └─> Return: APPROVED/BLOCKED with reasoning
```

**API Calls:**
- Elfa: 1 (fresh data, no cache)
- Binance: 2 (if not cached)

---

## API Call Summary

### External APIs

| API | Endpoint | Purpose | Rate Limit | Caching |
|-----|----------|---------|------------|---------|
| Elfa | `/v2/data/top-mentions` | Narrative data | 60/60s | 5 min |
| Binance | `/fapi/v1/premiumIndex` | Funding rate | 60/60s | 5 min |
| Binance | `/fapi/v1/ticker/24hr` | Price/volume | 60/60s | 5 min |

### Internal Storage

| Storage | Purpose | Technology |
|--------|---------|------------|
| narrative_history.db | Snapshot history | SQLite |
| narrative_chronicle.duckdb | Historical analysis | DuckDB |
| alerts_history.db | Alert logs | SQLite |

---

## Recommendations

### High Priority

1. **Remove debug prints** from `elfa_client.py`
2. **Fix fallback logic** - Don't use first result if ticker not found
3. **Normalize signal weights** when data sources are missing
4. **Persist cooldown state** for alerts to database

---

### Medium Priority

1. **Fix velocity calculation** to use time delta, not snapshot count
2. **Improve anomaly detection** with rolling windows
3. **Add cache invalidation** strategy
4. **Bound rate limit tracker** memory usage

---

### Low Priority

1. **Implement on-chain client** (currently template)
2. **Add request retry logic** with exponential backoff
3. **Implement volume_ratio** calculation in perp_client
4. **Add metrics/monitoring** for API call success rates


---

## Conclusion

The Elfa Tools codebase demonstrates strong architectural principles and robust error handling. The modular design enables flexible composition, and the explainable outputs provide transparency.

**Key Strengths:**

- Never crashes (graceful error handling)
- Clear data flow and transformations
- Composable modules
- Rate limiting and caching implemented

**Areas for Improvement:**

- Remove debug prints
- Fix edge cases in calculations
- Improve state persistence
- Normalize weights when data missing


Overall, the codebase is production-ready with minor fixes recommended above.

---

---

## End of Analysis

