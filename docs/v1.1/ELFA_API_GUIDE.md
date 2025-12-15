# Elfa API Guide & Advanced Use Cases

## 📡 Elfa API Overview

### Base URL

```text
https://api.elfa.ai
```


### Authentication

- **Method:** API Key via header
- **Header:** `x-elfa-api-key: YOUR_API_KEY`
- **Environment Variable:** `ELFA_API_KEY`

### Rate Limits

**Default Limits (as implemented in `elfa_client.py`):**

- **60 requests per 60 seconds** per endpoint
- Rate limit tracking is built into the client
- Automatic retry-after handling (429 responses)
- Client-side caching (5-minute TTL) to minimize API calls

**Rate Limit Behavior:**

- Client automatically tracks requests per endpoint
- Returns `None` gracefully when rate limited (never crashes)
- `Retry-After` header respected when provided by API
- Cache reduces API calls for repeated queries

**Best Practices:**

- Use caching for repeated queries (`use_cache=True` by default)
- Batch operations when possible
- Monitor with `get_rate_limit_stats()` function
- Use `--no-cache` flag sparingly in CLI tools

### Available Endpoints

#### `/v2/data/top-mentions`

**Purpose:** Get narrative data for tickers (mentions, mindshare, smart accounts)

**Parameters:**

- `ticker`: Ticker symbol (e.g., "BTC", "ETH", "AAPL")
- `timeWindow`: Aggregation window ("1h", "4h", "24h", etc.)
- `page`: Pagination (default: 0)
- `pageSize`: Results per page (default: 10)

**Response Fields:**

- `total_mentions`: Number of mentions in time window
- `mindshare_score`: Mindshare score (0-1 scale)
- `top_smart_accounts`: List of smart accounts mentioning ticker
- `results`: Array of ticker narrative data

**Data Structure:**

```python
TickerNarrativeSnapshot(
    ticker: str,
    window: str,
    total_mentions: int,
    mindshare_score: Optional[float],
    top_smart_accounts: List[str],
    source_query: str  # Audit trail
)
```

### Caching Strategy

**Default Cache TTL:** 5 minutes (300 seconds)

**Cache Benefits:**

- Reduces API calls by ~80% for repeated queries
- Faster response times for cached data
- Respects rate limits automatically
- Can be disabled per-request with `use_cache=False`

**Cache Management:**

```python
from elfa_client import clear_cache, get_cache_stats

# Check cache status
stats = get_cache_stats()
# {'total_entries': 10, 'valid_entries': 8, 'expired_entries': 2, 'cache_ttl_seconds': 300}

# Clear cache if needed
clear_cache()
```

---

## 🎯 Unique Use Cases by Tool

### 1. `elfa_client.py` - Raw Narrative Data

**Primary Use:** Fetch raw narrative snapshots from Elfa API

**Unique Capabilities:**

- **Audit Trails:** Every snapshot includes `source_query` for transparency
- **Graceful Degradation:** Never crashes, always returns `None` on errors
- **Smart Caching:** Automatic cache management with configurable TTL
- **Rate Limit Awareness:** Built-in tracking prevents hitting limits

**Use Cases:**

- Real-time narrative monitoring for single tickers
- Building custom analysis pipelines
- Integration with external systems
- Data collection for research/backtesting

**Example:**

```python
from elfa_client import get_ticker_narrative_snapshot

# Get current narrative state
snapshot = get_ticker_narrative_snapshot("BTC", window="4h")
if snapshot:
    print(f"BTC: {snapshot.total_mentions} mentions, "
          f"mindshare: {snapshot.mindshare_score}")
    print(f"Source: {snapshot.source_query}")  # Audit trail
```

---

### 2. `narrative_enricher.py` - Temporal Analysis

**Primary Use:** Track narrative changes over time (velocity, acceleration, churn)

**Unique Capabilities:**

- **Velocity Tracking:** Rate of change in mentions
- **Acceleration Detection:** Second derivative (change in velocity)
- **Account Churn Analysis:** New/lost smart accounts
- **SQLite Persistence:** Historical data for trend analysis

**Use Cases:**

- **Momentum Detection:** Identify accelerating narratives before they peak
- **Smart Money Tracking:** Monitor which accounts are entering/exiting narratives
- **Trend Reversal Signals:** Detect when acceleration turns negative
- **Historical Pattern Analysis:** Build datasets for ML models

**Example:**

```python
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher

enricher = NarrativeEnricher()
snapshot = get_ticker_narrative_snapshot("ETH", window="1h")
enriched = enricher.enrich_snapshot(snapshot)

# Detect momentum
if enriched.acceleration > 10:
    print(f"🚀 ETH narrative accelerating: {enriched.acceleration} mentions/snapshot")

# Track smart money
if enriched.new_accounts:
    print(f"💡 New smart accounts: {enriched.new_accounts}")
```

---

### 3. `narrative_radar.py` - Multi-Ticker Scanning

**Primary Use:** Scan multiple tickers simultaneously for narrative activity

**Unique Capabilities:**

- **Batch Processing:** Scan entire watchlists efficiently
- **Visual Indicators:** Emoji-based status (🚀📈↗️➡️↘️📉💥)
- **Export Formats:** Markdown reports with audit trails
- **Caching Integration:** Respects cache to minimize API calls

**Use Cases:**

- **Watchlist Monitoring:** Daily scans of your portfolio
- **Discovery:** Find tickers with unusual narrative activity
- **Comparative Analysis:** Compare narrative strength across assets
- **Automated Reporting:** Generate daily narrative reports

**Example:**

```bash
# Scan crypto watchlist
python narrative_radar.py BTC ETH SOL AVAX --window 4h --export daily_scan.md

# Output shows:
# BTC      1250    🚀 +45    ⚡ +12    0.85    +2 new, -1 lost
# ETH      980     📈 +23    🔺 +8     0.72    stable
```

---

### 4. `narrative_heatmap.py` - Relationship Analysis

**Primary Use:** Discover relationships between tickers through account overlap

**Unique Capabilities:**

- **Jaccard Similarity:** Account overlap between tickers
- **Velocity Correlation:** Which tickers move together narratively
- **Mindshare Clustering:** Group tickers by narrative similarity
- **Visual Exports:** PNG heatmaps + Markdown tables

**Use Cases:**

- **Sector Discovery:** Find tickers that share narrative communities
- **Correlation Analysis:** Identify narrative co-movements
- **Portfolio Diversification:** Avoid over-concentration in similar narratives
- **Market Structure Mapping:** Visualize narrative relationships

**Example:**

```python
# Discover which tickers share smart accounts
python narrative_heatmap.py BTC ETH SOL --window 24h --output ./heatmaps

# Reveals:
# - BTC and ETH have 60% account overlap (high correlation)
# - SOL has low overlap with BTC/ETH (different narrative community)
# - Velocity correlation matrix shows narrative co-movements
```

---

### 5. `narrative_digest.py` - Multi-Format Reporting

**Primary Use:** Generate platform-optimized narrative reports

**Unique Capabilities:**

- **6 Output Formats:** Obsidian, Telegram, Discord, Email, Blog, JSON
- **Insight Extraction:** Top movers, fastest accelerating, mindshare leaders
- **Platform Optimization:** Format-specific styling and structure
- **Historical Context:** Compare current vs previous periods

**Use Cases:**

- **Daily Briefings:** Automated morning narrative reports
- **Team Sharing:** Discord/Telegram updates for trading teams
- **Research Documentation:** Obsidian notes for knowledge management
- **Content Creation:** Blog-ready markdown for publishing

**Example:**

```bash
# Generate daily digest for Telegram
python narrative_digest.py BTC ETH SOL --window 24h --format telegram

# Output:
# 📊 NARRATIVE DIGEST - 24H
# 
# 🚀 Top Movers:
# • BTC: +45 mentions (velocity: +12.5)
# • ETH: +23 mentions (velocity: +8.2)
# 
# 💡 Smart Money Activity:
# • 3 new accounts on BTC
# • 2 accounts exited ETH
```

---

### 6. `signal_composer.py` - Multi-Source Signal Fusion

**Primary Use:** Combine narrative + market + on-chain data into unified signals

**Unique Capabilities:**

- **Weighted Fusion:** Configurable weights for each data source
- **Confidence Scoring:** Agreement-based confidence metrics
- **Conflict Detection:** Warns when signals disagree
- **Explainable Outputs:** Shows contributing factors

**Use Cases:**

- **Trade Signal Generation:** High-confidence composite signals
- **Risk Assessment:** Identify conflicting signals (low confidence)
- **Multi-Factor Analysis:** Narrative + funding + on-chain alignment
- **Backtesting:** Historical signal performance analysis

**Example:**

```python
from signal_composer import SignalComposer
from elfa_client import get_ticker_narrative_snapshot
from perp_client import get_perp_market_data

composer = SignalComposer(
    narrative_weight=0.4,
    market_weight=0.35,
    onchain_weight=0.25
)

narrative = get_ticker_narrative_snapshot("BTC", window="4h")
market = get_perp_market_data("BTC")
# onchain = get_onchain_data("BTC")  # When implemented

signal = composer.compose(
    ticker="BTC",
    narrative_data=narrative,
    market_data={
        'funding_rate': market.funding_rate if market else 0,
        'price_change_24h': market.price_change_24h if market else 0,
        'volume_ratio': market.volume_ratio if market else 1.0
    }
)

print(signal.explain())
# 🚀 BTC Composite Signal
# Overall: +0.65 (85% confidence)
# Components:
# • Narrative: +0.42
# • Market: +0.28
# • On-chain: +0.15
```

---

### 7. `alerts_engine.py` - Rule-Based Alerting

**Primary Use:** Get notified when narrative conditions are met

**Unique Capabilities:**

- **Flexible Rules:** Custom condition functions
- **Multi-Channel:** Discord, Telegram, Email, Console
- **Cooldown Management:** Prevents alert spam
- **SQLite Persistence:** Alert history and audit trail

**Use Cases:**

- **Spike Detection:** Alert on unusual mention activity
- **Smart Money Alerts:** Notify when multiple smart accounts mention ticker
- **Anomaly Detection:** Statistical outliers in narrative data
- **Velocity Thresholds:** Alert on acceleration/deceleration

**Example:**

```python
from alerts_engine import AlertsEngine, RuleFactory
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher

engine = AlertsEngine()
engine.add_channel(print)  # Or telegram_channel, discord_channel, etc.

# Add pre-built rules
engine.add_rule(RuleFactory.spike_detector("BTC", threshold=60))
engine.add_rule(RuleFactory.smart_money_alert("ETH", min_accounts=3))
engine.add_rule(RuleFactory.anomaly_alert("SOL"))

# Check data and fire alerts
enricher = NarrativeEnricher()
snapshot = get_ticker_narrative_snapshot("BTC", window="1h")
enriched = enricher.enrich_snapshot(snapshot)

engine.check_all("BTC", enriched)
# 🔥 SPIKE: BTC
# 75 mentions (threshold: 60)
# Mindshare: 0.12
```

---

### 8. `delta_store.py` - Historical Analysis

**Primary Use:** Store and analyze historical narrative data

**Unique Capabilities:**

- **DuckDB Backend:** Fast time-series queries
- **Velocity Calculation:** Historical rate of change
- **Anomaly Detection:** Statistical outlier identification
- **Watchlist Summaries:** Multi-ticker momentum rankings

**Use Cases:**

- **Backtesting:** Test narrative-based strategies
- **Pattern Recognition:** Identify recurring narrative patterns
- **Trend Analysis:** Long-term narrative trajectory analysis
- **Anomaly Research:** Study unusual narrative events

**Example:**

```python
from delta_store import DeltaStore
from elfa_client import get_ticker_narrative_snapshot

store = DeltaStore()

# Store snapshots over time
snapshot = get_ticker_narrative_snapshot("BTC", window="4h")
store.insert(snapshot)

# Calculate historical velocity
velocity = store.calculate_velocity("BTC", window="4h")
# {'mentions_velocity': 12.5, 'acceleration': 'up', ...}

# Detect anomalies
anomaly = store.detect_anomalies("BTC", window="4h", std_threshold=2.0)
if anomaly:
    print(f"🚨 Anomaly: {anomaly['z_score']:+.1f}σ from mean")
```

---

## 🔗 Advanced Combined Use Cases

### Use Case 1: Narrative-Market Divergence Detection

**Problem:** Identify when narrative and market signals diverge (potential reversal signals)

**Solution:** Combine `signal_composer` + `alerts_engine` + `delta_store`

```python
from signal_composer import SignalComposer
from alerts_engine import AlertsEngine, AlertRule
from delta_store import DeltaStore
from elfa_client import get_ticker_narrative_snapshot
from perp_client import get_perp_market_data

composer = SignalComposer()
engine = AlertsEngine()
store = DeltaStore()

# Custom rule: Alert on narrative-market divergence
def divergence_rule(data):
    narrative_score = data.get('narrative_score', 0)
    market_score = data.get('market_score', 0)
    # Alert if narrative bullish but market bearish (or vice versa)
    return abs(narrative_score - market_score) > 0.5

engine.add_rule(AlertRule(
    name="divergence",
    ticker="BTC",
    condition=divergence_rule,
    message_template="⚠️ DIVERGENCE: Narrative {narrative_score:+.2f} vs Market {market_score:+.2f}",
    cooldown_minutes=60
))

# Monitor and alert
narrative = get_ticker_narrative_snapshot("BTC")
market = get_perp_market_data("BTC")
signal = composer.compose("BTC", narrative_data=narrative, market_data=market)

# Store for historical analysis
if narrative:
    store.insert(narrative)

# Check for divergence
engine.check_all("BTC", {
    'narrative_score': signal.narrative_score,
    'market_score': signal.market_score
})
```

**Expected Value:** Early warning of potential reversals when narrative and price diverge.

---

### Use Case 2: Smart Money Flow Tracking

**Problem:** Track which smart accounts are accumulating/distributing across multiple tickers

**Solution:** Combine `narrative_enricher` + `narrative_heatmap` + `delta_store`

```python
from narrative_enricher import NarrativeEnricher
from narrative_heatmap import generate_heatmap  # Hypothetical
from delta_store import DeltaStore
from elfa_client import get_ticker_narrative_snapshot

enricher = NarrativeEnricher()
store = DeltaStore()
tickers = ["BTC", "ETH", "SOL", "AVAX"]

# Track account churn across portfolio
smart_money_flows = {}
for ticker in tickers:
    snapshot = get_ticker_narrative_snapshot(ticker, window="4h")
    if snapshot:
        enriched = enricher.enrich_snapshot(snapshot)
        store.insert(enriched)
        
        # Track which accounts are new (accumulating)
        for account in enriched.new_accounts:
            if account not in smart_money_flows:
                smart_money_flows[account] = {'accumulating': [], 'distributing': []}
            smart_money_flows[account]['accumulating'].append(ticker)
        
        # Track which accounts exited (distributing)
        for account in enriched.lost_accounts:
            if account not in smart_money_flows:
                smart_money_flows[account] = {'accumulating': [], 'distributing': []}
            smart_money_flows[account]['distributing'].append(ticker)

# Identify accounts with strong directional bias
for account, flows in smart_money_flows.items():
    if len(flows['accumulating']) >= 2:
        print(f"💡 {account} accumulating: {flows['accumulating']}")
    if len(flows['distributing']) >= 2:
        print(f"📤 {account} distributing: {flows['distributing']}")

# Use heatmap to find tickers with overlapping smart accounts
# (reveals which tickers smart money treats as correlated)
```

**Expected Value:** Identify smart money rotation patterns and narrative sector correlations.

---

### Use Case 3: Narrative Velocity Momentum Trading

**Problem:** Trade on narrative acceleration before it peaks

**Solution:** Combine `narrative_enricher` + `delta_store` + `signal_composer` + `alerts_engine`

```python
from narrative_enricher import NarrativeEnricher
from delta_store import DeltaStore
from signal_composer import SignalComposer
from alerts_engine import AlertsEngine, RuleFactory

enricher = NarrativeEnricher()
store = DeltaStore()
composer = SignalComposer()
engine = AlertsEngine()

# Custom rule: Alert on acceleration threshold
def acceleration_rule(data):
    velocity = data.get('mentions_velocity', 0)
    acceleration = data.get('acceleration', 0)
    # Alert when velocity is high AND accelerating
    return velocity > 15 and acceleration > 5

engine.add_rule(AlertRule(
    name="momentum",
    ticker="BTC",
    condition=acceleration_rule,
    message_template="🚀 MOMENTUM: Velocity {mentions_velocity:+.1f}, Accel {acceleration:+.1f}",
    cooldown_minutes=30
))

# Monitor and store
snapshot = get_ticker_narrative_snapshot("BTC", window="1h")
enriched = enricher.enrich_snapshot(snapshot)
store.insert(enriched)

# Get historical context
history = store.get_history("BTC", window="1h", hours_back=8)
if len(history) >= 3:
    # Calculate trend
    recent_velocity = [h.get('mentions_velocity', 0) for h in history[-3:]]
    trend = "accelerating" if recent_velocity[-1] > recent_velocity[0] else "decelerating"
    
    # Only alert if accelerating (early signal)
    if trend == "accelerating":
        engine.check_all("BTC", {
            'mentions_velocity': enriched.delta_mentions,
            'acceleration': enriched.acceleration
        })
```

**Expected Value:** Early entry signals before narrative peaks, maximizing capture of momentum moves.

---

### Use Case 4: Multi-Asset Narrative Correlation Dashboard

**Problem:** Monitor narrative relationships across entire portfolio

**Solution:** Combine `narrative_radar` + `narrative_heatmap` + `delta_store` + `narrative_digest`

```python
from narrative_radar import scan_tickers  # Hypothetical
from narrative_heatmap import generate_heatmap
from delta_store import DeltaStore
from narrative_digest import generate_digest

tickers = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK"]
store = DeltaStore()

# 1. Scan all tickers
radar_results = scan_tickers(tickers, window="4h")

# 2. Store in delta store for historical analysis
for result in radar_results:
    store.insert(result)

# 3. Generate heatmap to see relationships
heatmap_data = generate_heatmap(tickers, window="24h")

# 4. Get watchlist summary (momentum-ranked)
summary = store.get_watchlist_summary(tickers, window="4h")

# 5. Generate digest with insights
digest = generate_digest(
    tickers,
    window="24h",
    format="obsidian",  # For knowledge management
    insights={
        'top_movers': summary[:3],  # Top 3 by momentum
        'correlations': heatmap_data['account_overlap'],
        'anomalies': [store.detect_anomalies(t) for t in tickers]
    }
)

# Output: Comprehensive narrative dashboard
# - Current state (radar)
# - Relationships (heatmap)
# - Historical context (delta store)
# - Formatted insights (digest)
```

**Expected Value:** Holistic view of narrative landscape across portfolio, identifying opportunities and risks.

---

### Use Case 5: Narrative-Funded Signal Backtesting

**Problem:** Test if narrative signals combined with funding rates predict price movements

**Solution:** Combine `delta_store` + `signal_composer` + `perp_client` (historical data)

```python
from delta_store import DeltaStore
from signal_composer import SignalComposer
from perp_client import get_perp_market_data
from datetime import datetime, timedelta

store = DeltaStore()
composer = SignalComposer()

# Get historical narrative data
history = store.get_history("BTC", window="4h", hours_back=720)  # 30 days

# Backtest: For each historical point, generate signal and compare to actual price
results = []
for i, snapshot in enumerate(history[1:], 1):
    # Get narrative data
    narrative_data = {
        'mentions': snapshot['mentions'],
        'mindshare': snapshot['mindshare'],
        'mentions_velocity': snapshot['mentions'] - history[i-1]['mentions']
    }
    
    # Get market data (would need historical perp data)
    market_data = get_perp_market_data("BTC")  # Current - would need historical
    
    # Generate signal
    signal = composer.compose("BTC", narrative_data=narrative_data, market_data=market_data)
    
    # Compare to actual price movement (would need historical price data)
    # Store results for analysis
    results.append({
        'timestamp': snapshot['timestamp'],
        'signal': signal.composite_score,
        'confidence': signal.confidence,
        # 'actual_price_change': ...  # Would need historical price data
    })

# Analyze: Do high-confidence signals correlate with price movements?
# Calculate hit rate, Sharpe ratio, etc.
```

**Expected Value:** Quantify predictive power of narrative signals, optimize signal weights.

---

## 💡 Key Insights: Why These Combinations Work

### 1. Temporal + Spatial = Context

- `narrative_enricher` (temporal) + `narrative_heatmap` (spatial) = Full narrative context
- Velocity tells you *when*, heatmap tells you *where* (which tickers)

### 2. Raw + Enriched = Intelligence

- `elfa_client` (raw) + `narrative_enricher` (enriched) = Actionable insights
- Raw data is a snapshot, enriched data shows direction

### 3. Single + Multi = Scale

- Individual tools (single ticker) + batch tools (multi-ticker) = Portfolio-level analysis
- Scale from monitoring one asset to entire watchlists

### 4. Real-time + Historical = Pattern Recognition

- Current tools (real-time) + `delta_store` (historical) = Pattern detection
- Identify recurring narrative patterns for predictive signals

### 5. Narrative + Market + On-chain = Signal Fusion

- `signal_composer` combines all data sources = Higher confidence signals
- Single-source signals are noisy, multi-source signals are robust

---

## 🎯 Expected Value Summary

### Individual Tools

- **Raw Data Access:** Direct API integration with caching/rate limiting
- **Temporal Analysis:** Velocity, acceleration, churn tracking
- **Batch Processing:** Multi-ticker scanning and comparison
- **Relationship Discovery:** Account overlap and correlation analysis
- **Format Flexibility:** Platform-optimized reporting
- **Signal Generation:** Multi-source fusion with confidence scoring
- **Automated Alerts:** Rule-based notification system
- **Historical Analysis:** Pattern recognition and backtesting

### Combined Tools

- **Divergence Detection:** Early warning of reversals
- **Smart Money Tracking:** Account-level flow analysis
- **Momentum Trading:** Acceleration-based entry signals
- **Portfolio Dashboard:** Holistic narrative monitoring
- **Strategy Backtesting:** Quantify signal predictive power

### Unique Advantages

1. **Narrow:** Each tool does one job well
2. **Explainable:** Every signal shows its source (audit trails)
3. **Robust:** Never crashes, graceful degradation
4. **Composable:** Tools work together seamlessly
5. **Signal Layer, Not Oracle:** Provides signals and context, not answers
6. **Transparent Constraints:** Rate limits, caching, and provenance are visible
7. **Efficient:** Built-in caching reduces API costs
8. **Flexible:** Works with any data source (narrative, market, on-chain)

All tools converge on **Decision Moments**—structured explanations of why now matters. See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete design philosophy.

---

## 📚 Additional Resources

- **Elfa API Docs:** [docs.elfa.ai](https://docs.elfa.ai)
- **Project README:** [README.md](./README.md)
- **Roadmap:** [ROADMAP.md](./ROADMAP.md)
- **Contributing:** [CONTRIBUTING.md](./CONTRIBUTING.md)

---

*Last updated: 2024-01-XX*

