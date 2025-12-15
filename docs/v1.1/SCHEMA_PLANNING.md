# Schema Planning — Complete System Architecture

**Comprehensive reference** for all data structures, database schemas, and module relationships.

---

## Table of Contents

1. [Data Structures (Python)](#data-structures-python)
2. [Database Schemas](#database-schemas)
3. [Module Relationships](#module-relationships)
4. [Data Flow](#data-flow)
5. [Schema Relationships Diagram](#schema-relationships-diagram)

---

## Data Structures (Python)

### 1. TickerNarrativeSnapshot

**Module:** `elfa_client.py`  
**Purpose:** Raw snapshot from Elfa API

```python
@dataclass
class TickerNarrativeSnapshot:
    ticker: str                    # "BTC", "ETH"
    window: str                    # "1h", "4h", "24h"
    total_mentions: int            # Raw mention count
    mindshare_score: Optional[float]  # 0.0 to 1.0
    top_smart_accounts: List[str]  # Account addresses/IDs
    source_query: str              # API query for audit trail
```

**Relationships:**
- Input to: `narrative_enricher.enrich_snapshot()`
- Stored in: `narrative_history.db` (snapshots table)
- Cached in: `elfa_client._cache` (in-memory, TTL: 300s)

---

### 2. EnrichedSnapshot

**Module:** `narrative_enricher.py`  
**Purpose:** Snapshot with computed deltas (velocity, acceleration, churn)

```python
@dataclass
class EnrichedSnapshot:
    # Base fields (from TickerNarrativeSnapshot)
    ticker: str
    window: str
    timestamp: datetime
    total_mentions: int
    mindshare_score: Optional[float]
    top_smart_accounts: List[str]
    source_query: str
    
    # Computed fields
    delta_mentions: int = 0              # Change from last snapshot
    acceleration: Optional[int] = None   # Change in velocity (requires 3+ snapshots)
    new_accounts: List[str] = []         # Accounts that appeared
    lost_accounts: List[str] = []        # Accounts that disappeared
```

**Relationships:**
- Created from: `TickerNarrativeSnapshot` via `enrich_snapshot()`
- Input to: `signal_composer.compose()`, `delta_store.insert()`, `alerts_engine.check_all()`
- Stored in: `narrative_history.db` (snapshots table), `narrative_chronicle.duckdb` (narrative_snapshots table)

---

### 3. CompositeSignal

**Module:** `signal_composer.py`  
**Purpose:** Fused signal from multiple data sources

```python
@dataclass
class CompositeSignal:
    ticker: str
    timestamp: datetime
    
    # Component scores (-1 to 1)
    narrative_score: float    # From EnrichedSnapshot
    market_score: float       # From perp_client
    onchain_score: float      # From onchain_client
    
    # Composite output
    composite_score: float    # Weighted average (-1 to 1)
    signal_strength: SignalStrength  # Enum: STRONG_BULLISH, BULLISH, NEUTRAL, BEARISH, STRONG_BEARISH, CONFLICTED
    confidence: float         # 0.0 to 1.0 (agreement-based)
    
    # Evidence
    evidence: Dict            # Key metrics from all sources
    warnings: List[str]        # Conflicting signals, extreme conditions
```

**Relationships:**
- Created from: `EnrichedSnapshot` + market data + on-chain data
- Input to: `decision_moment.py` (for DecisionMoment creation)
- Ephemeral: Not persisted (generated on-demand)

---

### 4. DecisionMoment

**Module:** `decision_moment.py`  
**Purpose:** Structured explanation of why now matters

```python
@dataclass
class DecisionMoment:
    id: str                           # "BTC_20241213_1h"
    timestamp: datetime
    subject_type: str                 # "ticker", "theme"
    symbol: str                       # "BTC"
    window: str                       # "1h", "4h"
    
    trigger_description: str
    anomaly_type: str                 # "acceleration", "churn", "divergence"
    
    signals_contributing: List[SignalEvidence]
    signals_excluded: List[SignalEvidence]
    
    narrative_state: str              # "building", "fading"
    alignment: str                    # "aligned", "divergent", ""
    novelty: str                      # "new", "recurring", ""
    
    conviction: str                   # "low", "medium", "high"
    uncertainty: str                  # Human-readable
    
    interpretation_summary: str
    interpretation_exclusion: str     # What it is NOT
    
    provenance_sources: List[str]     # Data source queries
    generated_by: str                  # Tool/pipeline name
    
    diff: Optional[DecisionMomentDiff]
```

**Relationships:**
- Created from: `CompositeSignal` + policy evaluation
- Evaluated by: `DecisionMomentPolicy.should_trigger()`
- Input to: `alerts_engine.check_all()` (if policy_passed=True)
- Ephemeral: Not persisted (generated on-demand, logged if triggered)

---

### 5. SignalEvidence

**Module:** `decision_moment.py`  
**Purpose:** Evidence from a contributing signal

```python
@dataclass
class SignalEvidence:
    name: str                  # "Narrative Velocity"
    value: float | str         # 3.5 or "high"
    baseline: float | str      # 1.0 or "normal"
    note: str                  # "3.5x vs last hour"
```

**Relationships:**
- Used in: `DecisionMoment.signals_contributing`, `DecisionMoment.signals_excluded`

---

### 6. DecisionMomentDiff

**Module:** `decision_moment.py`  
**Purpose:** Tracks what changed since last Decision Moment

```python
@dataclass
class DecisionMomentDiff:
    since: datetime
    added: List[str]           # Signal names that appeared
    removed: List[str]         # Signal names that disappeared
    intensified: List[str]     # Signal names that strengthened
    weakened: List[str]        # Signal names that weakened
    interpretation_delta: str  # Summary of interpretation changes
```

**Relationships:**
- Used in: `DecisionMoment.diff`

---

### 7. BoringModeConfig

**Module:** `decision_moment.py`  
**Purpose:** Policy configuration

```python
@dataclass
class BoringModeConfig:
    min_signals: int = 2
    min_velocity_multiplier: float = 2.0
    require_alignment: bool = True
    cooldown_seconds: int = 3600
    allow_recurring_patterns: bool = True
```

**Relationships:**
- Used in: `DecisionMomentPolicy.config`

---

### 8. AlertRule

**Module:** `alerts_engine.py`  
**Purpose:** Alert rule definition

```python
@dataclass
class AlertRule:
    name: str
    ticker: str
    condition: Callable[[Dict], bool]  # Function that evaluates data
    message_template: str
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None
```

**Relationships:**
- Stored in: `AlertsEngine.rules` (in-memory)
- Cooldown persisted in: `alerts_history.db` (alert_cooldowns table)

---

## Database Schemas

### SQLite: narrative_history.db

**Module:** `narrative_enricher.py`  
**Purpose:** Store raw snapshots for velocity/acceleration calculation

```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    window TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    total_mentions INTEGER NOT NULL,
    mindshare_score REAL,
    top_accounts TEXT,              -- Comma-separated list
    source_query TEXT
);

-- Indexes (implicit, via queries)
-- Primary lookup: (ticker, window) ORDER BY timestamp DESC
```

**Data Flow:**
- Written by: `NarrativeEnricher.store_snapshot()`
- Read by: `NarrativeEnricher.get_last_snapshot()`, `get_last_two_snapshots()`
- Contains: Raw `TickerNarrativeSnapshot` data (before enrichment)

---

### DuckDB: narrative_chronicle.duckdb

**Module:** `delta_store.py`  
**Purpose:** Historical analysis and anomaly detection

```sql
CREATE TABLE narrative_snapshots (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    window VARCHAR NOT NULL,
    mentions INTEGER NOT NULL,
    mindshare DOUBLE,
    smart_accounts VARCHAR,          -- JSON array
    timestamp TIMESTAMP NOT NULL,
    source_query VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticker_timestamp 
    ON narrative_snapshots(ticker, timestamp DESC);

CREATE INDEX idx_window_timestamp 
    ON narrative_snapshots(window, timestamp DESC);
```

**Data Flow:**
- Written by: `DeltaStore.insert()` (accepts both `TickerNarrativeSnapshot` and `EnrichedSnapshot`)
- Read by: `DeltaStore.calculate_velocity()`, `detect_anomalies()`, `get_history()`
- Contains: Historical snapshots for time-series analysis

---

### SQLite: alerts_history.db

**Module:** `alerts_engine.py`  
**Purpose:** Alert history and cooldown state

```sql
-- Alert history
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0
);

CREATE INDEX idx_ticker_timestamp 
    ON alert_history(ticker, timestamp DESC);

-- Cooldown state (persists across restarts)
CREATE TABLE alert_cooldowns (
    rule_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    last_triggered TEXT NOT NULL,
    PRIMARY KEY (rule_name, ticker)
);
```

**Data Flow:**
- Written by: `AlertsEngine._save_alert()`, `_save_cooldown_state()`
- Read by: `AlertsEngine.get_history()`, `_get_cooldown_state()`, `_load_cooldown_state()`
- Contains: Alert logs and persistent cooldown state

---

## Module Relationships

### Data Structure Flow

```
External APIs
    │
    ▼
elfa_client.py
    │
    ├─► TickerNarrativeSnapshot
    │       │
    │       ├─► narrative_enricher.py
    │       │       │
    │       │       ├─► EnrichedSnapshot
    │       │       │       │
    │       │       │       ├─► signal_composer.py
    │       │       │       │       │
    │       │       │       │       └─► CompositeSignal
    │       │       │       │               │
    │       │       │       │               └─► decision_moment.py
    │       │       │       │                       │
    │       │       │       │                       └─► DecisionMoment
    │       │       │       │                               │
    │       │       │       │                               └─► alerts_engine.py
    │       │       │       │                                       │
    │       │       │       │                                       └─► Alert (fired)
    │       │       │       │
    │       │       │       └─► delta_store.py (DuckDB)
    │       │       │
    │       │       └─► narrative_history.db (SQLite)
    │       │
    │       └─► delta_store.py (DuckDB)
```

### Module Dependencies

```
elfa_client.py
    └─► (no dependencies)

narrative_enricher.py
    └─► elfa_client.TickerNarrativeSnapshot

delta_store.py
    └─► elfa_client.TickerNarrativeSnapshot
    └─► narrative_enricher.EnrichedSnapshot

signal_composer.py
    └─► elfa_client.TickerNarrativeSnapshot
    └─► narrative_enricher.EnrichedSnapshot
    └─► perp_client (market data dict)
    └─► onchain_client (on-chain data dict)

decision_moment.py
    └─► signal_composer.CompositeSignal (indirect)

alerts_engine.py
    └─► elfa_client.TickerNarrativeSnapshot
    └─► narrative_enricher.EnrichedSnapshot
    └─► decision_moment.DecisionMoment (indirect)
```

---

## Data Flow

### Complete Loop Flow

```
1. OBSERVE
   elfa_client.get_ticker_narrative_snapshot()
   └─► TickerNarrativeSnapshot
       │
       ├─► Cache: _cache[KEY] = (snapshot, expiry_time)
       └─► narrative_enricher.enrich_snapshot()

2. ENRICH
   narrative_enricher.enrich_snapshot()
   ├─► Read: narrative_history.db (last 2 snapshots)
   ├─► Compute: delta_mentions, acceleration, churn
   ├─► Write: narrative_history.db (current snapshot)
   └─► Return: EnrichedSnapshot
       │
       └─► delta_store.insert()
           └─► Write: narrative_chronicle.duckdb

3. DECIDE
   signal_composer.compose()
   ├─► Input: EnrichedSnapshot + market_data + onchain_data
   ├─► Score: narrative, market, on-chain
   ├─► Normalize: weights based on available data
   └─► Return: CompositeSignal

4. GATE
   decision_moment.py
   ├─► Create: DecisionMoment from CompositeSignal
   ├─► Evaluate: DecisionMomentPolicy.should_trigger()
   │   ├─► Check: cooldown (from _last_moment dict)
   │   ├─► Check: min_signals, velocity_multiplier, alignment, recurring
   │   └─► Return: True/False
   └─► If True: proceed to EXPLAIN

5. EXPLAIN
   DecisionMoment.explain()
   └─► Return: str (human-readable)

6. INTERRUPT
   alerts_engine.check_all()
   ├─► Evaluate: AlertRule.condition()
   ├─► Check: cooldown (from alert_cooldowns table)
   ├─► Fire: alert via channels
   ├─► Write: alert_history table
   └─► Write: alert_cooldowns table
```

---

## Schema Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
│  (Elfa API, Binance API, On-chain APIs)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   elfa_client.py               │
        │                                │
        │   TickerNarrativeSnapshot      │
        │   ├─ ticker                    │
        │   ├─ window                    │
        │   ├─ total_mentions            │
        │   ├─ mindshare_score           │
        │   ├─ top_smart_accounts        │
        │   └─ source_query              │
        │                                │
        │   Cache: _cache[KEY]           │
        └───────────┬────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │   narrative_enricher.py        │
        │                                │
        │   EnrichedSnapshot             │
        │   ├─ (all TickerNarrative...)  │
        │   ├─ delta_mentions            │
        │   ├─ acceleration              │
        │   ├─ new_accounts              │
        │   └─ lost_accounts             │
        │                                │
        │   SQLite: narrative_history.db │
        │   └─ snapshots table           │
        └───────────┬────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                        │
        ▼                        ▼
┌───────────────┐      ┌──────────────────┐
│ delta_store.py│      │ signal_composer.py│
│               │      │                   │
│ DuckDB:       │      │ CompositeSignal   │
│ narrative_    │      │ ├─ narrative_score│
│ chronicle.    │      │ ├─ market_score   │
│ duckdb        │      │ ├─ onchain_score  │
│               │      │ ├─ composite_score│
│ narrative_    │      │ ├─ signal_strength │
│ snapshots     │      │ ├─ confidence     │
│ table         │      │ └─ evidence       │
└───────────────┘      └─────────┬────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ decision_moment.py       │
                    │                          │
                    │ DecisionMoment           │
                    │ ├─ signals_contributing  │
                    │ ├─ signals_excluded      │
                    │ ├─ interpretation_*     │
                    │ └─ diff                  │
                    │                          │
                    │ DecisionMomentPolicy     │
                    │ ├─ should_trigger()      │
                    │ └─ _last_moment (dict)   │
                    └──────────┬───────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │ alerts_engine.py         │
                    │                          │
                    │ AlertRule                 │
                    │ ├─ condition             │
                    │ ├─ message_template      │
                    │ └─ last_triggered         │
                    │                          │
                    │ SQLite: alerts_history.db│
                    │ ├─ alert_history table   │
                    │ └─ alert_cooldowns table │
                    └──────────────────────────┘
```

---

## Key Relationships Summary

### 1. Snapshot Chain

```
TickerNarrativeSnapshot (raw)
    ↓ enrich_snapshot()
EnrichedSnapshot (with deltas)
    ↓ insert()
DuckDB narrative_snapshots (historical)
```

### 2. Signal Chain

```
EnrichedSnapshot
    ↓ compose()
CompositeSignal
    ↓ create DecisionMoment
DecisionMoment
    ↓ should_trigger()
bool (policy decision)
    ↓ if True
Alert (fired)
```

### 3. Storage Chain

```
TickerNarrativeSnapshot
    ↓ store_snapshot()
SQLite snapshots (for velocity calc)
    ↓ insert()
DuckDB narrative_snapshots (for analysis)
```

### 4. Cooldown Chain

```
DecisionMomentPolicy._last_moment (in-memory)
    ↓ on trigger
alerts_engine._save_cooldown_state()
    ↓
SQLite alert_cooldowns (persistent)
    ↓ on restart
alerts_engine._load_cooldown_state()
    ↓
AlertRule.last_triggered (in-memory)
```

---

## Data Type Mappings

### Python → SQLite

| Python Type | SQLite Type | Example |
|-------------|-------------|---------|
| `str` | `TEXT` | `"BTC"` |
| `int` | `INTEGER` | `1420` |
| `float` | `REAL` | `0.15` |
| `List[str]` | `TEXT` (comma-separated) | `"addr1,addr2,addr3"` |
| `datetime` | `TEXT` (ISO format) | `"2024-12-13T10:00:00"` |
| `Optional[T]` | `TEXT/INTEGER/REAL` (nullable) | `NULL` |

### Python → DuckDB

| Python Type | DuckDB Type | Example |
|-------------|-------------|---------|
| `str` | `VARCHAR` | `"BTC"` |
| `int` | `INTEGER` | `1420` |
| `float` | `DOUBLE` | `0.15` |
| `List[str]` | `VARCHAR` (JSON array) | `'["addr1","addr2"]'` |
| `datetime` | `TIMESTAMP` | `TIMESTAMP '2024-12-13 10:00:00'` |

---

## Index Strategy

### SQLite (narrative_history.db)

**Primary Lookup Pattern:**
```sql
SELECT * FROM snapshots 
WHERE ticker = ? AND window = ? 
ORDER BY timestamp DESC 
LIMIT 2;
```

**No explicit indexes** (SQLite auto-indexes on WHERE clauses for small datasets)

### DuckDB (narrative_chronicle.duckdb)

**Indexes:**
- `idx_ticker_timestamp` on `(ticker, timestamp DESC)` — for velocity calculation
- `idx_window_timestamp` on `(window, timestamp DESC)` — for window-based queries

**Query Patterns:**
- Velocity: `WHERE ticker = ? AND window = ? AND timestamp >= ?`
- Anomalies: `WHERE ticker = ? AND window = ? AND timestamp >= ?` (48h lookback)

### SQLite (alerts_history.db)

**Indexes:**
- `idx_ticker_timestamp` on `(ticker, timestamp DESC)` — for alert history queries

**Query Patterns:**
- History: `WHERE ticker = ? ORDER BY timestamp DESC LIMIT ?`
- Cooldown: `WHERE rule_name = ? AND ticker = ?` (PRIMARY KEY lookup)

---

## Cache Strategy

### In-Memory Caches

**elfa_client.py:**
```python
_cache: Dict[str, Tuple[TickerNarrativeSnapshot, float]]
# Key: "ticker:BTC:window:1h"
# Value: (snapshot, expiry_timestamp)
# TTL: 300 seconds (5 minutes)
```

**DecisionMomentPolicy:**
```python
_last_moment: Dict[str, datetime]
# Key: symbol (e.g., "BTC")
# Value: last DecisionMoment timestamp
# Purpose: Cooldown tracking (in-memory, also persisted)
```

**Rate Limit Tracker:**
```python
_rate_limit_tracker: Dict[str, List[float]]
# Key: endpoint (e.g., "/v2/data/top-mentions")
# Value: list of request timestamps
# Purpose: Rate limit enforcement (60 req/60s)
```

---

*End of Schema Planning*
