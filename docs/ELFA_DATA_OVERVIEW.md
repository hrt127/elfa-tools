# Elfa Data Overview & Phase B Analysis

**Generated:** 2025-12-15  
**Purpose:** Comprehensive analysis of available Elfa data, current usage, and Phase B innovation opportunities

---

## 📊 Available Elfa Data (What Can Be Queried)

Based on [Elfa API Documentation](https://docs.elfa.ai) and [FAQ](https://elfa-ai.gitbook.io/faq/):

### Free Plan Features (Available to Query)

1. **Trending Tokens**
   - Real-time trending tokens by mentions
   - Time-windowed leaderboards
   - Mindshare rankings

2. **Smart Stats**
   - Smart account activity
   - Account-level insights
   - Top smart accounts per ticker

3. **Top Mentions**
   - Total mentions per ticker
   - Time-windowed aggregation (1h, 4h, 24h, etc.)
   - Mention velocity and trends

4. **Multi-Keyword Mentions Search**
   - Search across multiple keywords/tickers
   - Cross-ticker mention analysis
   - Keyword co-occurrence

5. **Event Summary from Keyword Mentions**
   - Event detection from mentions
   - Keyword-triggered summaries
   - Contextual event extraction

6. **Token News Mentions**
   - News account mentions
   - Verified news outlet activity
   - News-driven narrative signals

7. **Trending Contract Addresses on Twitter**
   - Contract address mentions on X/Twitter
   - Address-level narrative tracking
   - Smart contract attention signals

8. **Trending Contract Addresses on Telegram**
   - Contract address mentions on Telegram
   - Telegram-specific narrative signals
   - Cross-platform address tracking

### Additional Available Data (Beyond Free Plan)

Based on API structure and Elfa's data sources:

- **Sentiment Scores** - Bullish/bearish sentiment per token
- **Account Classifications** - Smart Accounts, CT Accounts, News Accounts
- **Mindshare Percentages** - Percentage of total crypto discussion
- **Historical Time-Series** - Historical mention data (with API access)
- **Account Overlap** - Which accounts mention multiple tickers
- **Source Attribution** - X, Telegram, and other sources
- **Real-Time Streams** - WebSocket API (coming soon)

---

## 🔍 What We're Currently Querying

### Current Implementation (`elfa_client.py`)

**Endpoint:** `GET /v2/data/top-mentions`

**Query Parameters:**
- `ticker`: Single ticker symbol (e.g., "BTC", "ETH")
- `timeWindow`: Aggregation window ("1h", "4h", "24h")
- `page`: Pagination (default: 0)
- `pageSize`: Results per page (default: 10)

**Data Retrieved:**
```python
TickerNarrativeSnapshot(
    ticker: str,                    # Ticker symbol
    window: str,                    # Time window
    total_mentions: int,            # Total mentions in window
    mindshare_score: Optional[float], # Mindshare (0-1 scale)
    top_smart_accounts: List[str],  # Top 3 smart accounts
    source_query: str               # Audit trail
)
```

**What We Extract:**
- ✅ Total mentions count
- ✅ Mindshare score
- ✅ Top smart accounts (first 3)
- ✅ Source query for audit trail

**What We DON'T Query (But Could):**
- ❌ Multi-ticker batch queries
- ❌ Sentiment scores
- ❌ Account classifications (CT, News, Smart)
- ❌ Contract address mentions
- ❌ Event summaries
- ❌ News mentions specifically
- ❌ Cross-platform data (Twitter vs Telegram)
- ❌ Historical time-series (beyond our own storage)
- ❌ Trending tokens leaderboard
- ❌ Multi-keyword searches

---

## 🛠️ How We're Set Up to Query

### Architecture

```
elfa_client.py
├── Authentication: x-elfa-api-key header
├── Base URL: https://api.elfa.ai
├── Endpoint: /v2/data/top-mentions
├── Rate Limiting: 60 req/60s (client-side tracking)
├── Caching: 5-minute TTL (in-memory)
└── Error Handling: Graceful (returns None, never crashes)
```

### Query Flow

```
User Request
    ↓
get_ticker_narrative_snapshot(ticker, window)
    ↓
Check Cache → Return if cached
    ↓
Check Rate Limits → Block if limited
    ↓
GET /v2/data/top-mentions?ticker={ticker}&timeWindow={window}
    ↓
Parse Response → Extract ticker data from results array
    ↓
Cache Result → Store for 5 minutes
    ↓
Return TickerNarrativeSnapshot
```

### Current Limitations

1. **Single Ticker Only** - One ticker per API call
2. **No Batch Queries** - Can't query multiple tickers in one request
3. **Limited Data Extraction** - Only extracting 3 fields (mentions, mindshare, accounts)
4. **No Sentiment** - Not extracting sentiment scores
5. **No Account Types** - Not distinguishing Smart/CT/News accounts
6. **No Contract Addresses** - Not querying contract address mentions
7. **No Events** - Not using event summary endpoints
8. **No Leaderboards** - Not querying trending tokens endpoint

---

## 📈 Comparison: Free Plan vs What We Use

| Feature | Free Plan Available | We Query | We Use | Gap |
|---------|-------------------|----------|--------|-----|
| **Top Mentions** | ✅ | ✅ | ✅ | None |
| **Smart Stats** | ✅ | ⚠️ Partial | ✅ | Only top 3 accounts |
| **Trending Tokens** | ✅ | ❌ | ❌ | **Not using** |
| **Multi-Keyword Search** | ✅ | ❌ | ❌ | **Not using** |
| **Event Summary** | ✅ | ❌ | ❌ | **Not using** |
| **Token News Mentions** | ✅ | ❌ | ❌ | **Not using** |
| **Contract Addresses (Twitter)** | ✅ | ❌ | ❌ | **Not using** |
| **Contract Addresses (Telegram)** | ✅ | ❌ | ❌ | **Not using** |
| **Sentiment Scores** | ✅ | ❌ | ❌ | **Not using** |
| **Account Classifications** | ✅ | ⚠️ Partial | ⚠️ Partial | Not distinguishing types |

**Summary:** We're using **~12.5%** of available free plan features.

---

## 🚀 What Else Is Available (Beyond Current Usage)

### 1. Trending Tokens Leaderboard
**Endpoint:** Likely `/v2/data/trending` or similar  
**Value:** Discover new opportunities without knowing tickers upfront  
**Use Case:** Daily discovery scan, find emerging narratives

### 2. Multi-Keyword Mentions
**Endpoint:** Likely `/v2/data/mentions?keywords=[]` or similar  
**Value:** Cross-ticker analysis, sector tracking  
**Use Case:** Track entire sectors (e.g., all L2s, all DeFi tokens)

### 3. Event Summary from Keywords
**Endpoint:** Likely `/v2/data/events` or similar  
**Value:** Contextual event detection  
**Use Case:** Understand WHY something is trending

### 4. Contract Address Mentions
**Endpoints:** Likely `/v2/data/contracts/twitter` and `/v2/data/contracts/telegram`  
**Value:** Track smart contract attention before token launch  
**Use Case:** Early detection of new contracts gaining attention

### 5. News Mentions
**Endpoint:** Likely `/v2/data/news` or similar  
**Value:** Distinguish organic vs news-driven narratives  
**Use Case:** Filter out news-driven noise, focus on organic attention

### 6. Sentiment Scores
**Endpoint:** Likely in `/v2/data/top-mentions` response (not extracted)  
**Value:** Directional context beyond volume  
**Use Case:** Distinguish bullish vs bearish narrative spikes

### 7. Account Type Classifications
**Endpoint:** Likely in response data (not extracted)  
**Value:** Weight signals by account quality  
**Use Case:** Prioritize Smart Account activity over CT Account activity

### 8. Cross-Platform Analysis
**Value:** Compare Twitter vs Telegram narratives  
**Use Case:** Identify platform-specific narratives (e.g., Telegram alpha groups)

---

## 🎯 Phase B Goals Analysis

### Current Phase B Status

Based on roadmap and implementation:

**Phase 1: Signal Generation & Storage** ✅ **COMPLETE**
- ✅ Composite Signal Generator (`signal_composer.py`)
- ✅ Delta Store (`delta_store.py`)
- ✅ Perpetual Futures Client (`perp_client.py`)
- ✅ On-Chain Client Template (`onchain_client.py`)

**Phase 2: Alerts & Automation** ✅ **COMPLETE**
- ✅ Alerts Engine (`alerts_engine.py`)
- 🚧 Bot Adapter (Planned)

**Phase 3: Integration & Visualization** 📋 **PLANNED**
- 📋 Dashboard Adapter
- 📋 Advanced Visualizations

### What Phase B Should Achieve

**Goal:** Transform narrative intelligence into actionable trading signals through:
1. **Multi-source signal fusion** (narrative + market + on-chain)
2. **Automated alerting** (rule-based notifications)
3. **Historical analysis** (pattern recognition, backtesting)
4. **Decision Moments** (structured explanations of why now matters)

---

## 💡 Are We Doing Enough? Innovation Analysis

### ✅ What We're Doing Well

1. **Temporal Analysis (Velocity/Acceleration)**
   - Unique: Most tools only show current state
   - Value: Early momentum detection
   - Innovation: **High** - Not commonly done

2. **Account Churn Tracking**
   - Unique: Track which smart accounts enter/exit
   - Value: Smart money flow detection
   - Innovation: **High** - Novel approach

3. **Multi-Source Signal Fusion**
   - Unique: Narrative + Market + On-chain
   - Value: Higher confidence signals
   - Innovation: **Medium** - Concept exists, execution is clean

4. **Explainable Signals**
   - Unique: Every signal shows source and reasoning
   - Value: Trust and transparency
   - Innovation: **High** - Rare in trading tools

5. **Decision Moment Framework**
   - Unique: Structured "why now matters" explanations
   - Value: Reduces noise, focuses attention
   - Innovation: **Very High** - Novel concept

### ⚠️ What We're Missing (Innovation Opportunities)

#### 1. **Contract Address Alpha** 🔥 **HIGH ALPHA OPPORTUNITY**

**What:** Track contract addresses before token launch  
**Why:** Early detection of new projects gaining attention  
**How:**
```python
# New endpoint: /v2/data/contracts/trending
contracts = get_trending_contracts(platform="twitter", window="1h")
# Returns: [{"address": "0x...", "mentions": 45, "accounts": [...]}]
```

**Innovation Level:** 🔥 **Very High** - Unseen alpha source  
**Implementation Effort:** Low (new endpoint wrapper)  
**Value:** Early entry opportunities

#### 2. **Cross-Platform Narrative Divergence** 🔥 **HIGH ALPHA OPPORTUNITY**

**What:** Compare Twitter vs Telegram narratives  
**Why:** Identify platform-specific alpha (Telegram groups often ahead)  
**How:**
```python
twitter_data = get_ticker_narrative_snapshot("BTC", source="twitter")
telegram_data = get_ticker_narrative_snapshot("BTC", source="telegram")
divergence = calculate_divergence(twitter_data, telegram_data)
# Alert if Telegram mentions spike before Twitter
```

**Innovation Level:** 🔥 **Very High** - Novel signal  
**Implementation Effort:** Medium (requires source filtering)  
**Value:** Early signal detection

#### 3. **Event-Driven Narrative Spikes** 🔥 **MEDIUM-HIGH ALPHA**

**What:** Use event summaries to understand WHY narratives spike  
**Why:** Distinguish organic momentum vs news-driven spikes  
**How:**
```python
events = get_event_summary(keywords=["BTC", "ETF"], window="24h")
# Returns: [{"event": "ETF approval", "mentions": 1200, "accounts": [...]}]
# Filter: Only act on organic spikes (no major events)
```

**Innovation Level:** 🔥 **High** - Context-aware signals  
**Implementation Effort:** Medium (new endpoint + filtering logic)  
**Value:** Better signal quality (avoid news-driven false signals)

#### 4. **Sentiment-Weighted Signals** ⚡ **MEDIUM ALPHA**

**What:** Weight signals by sentiment (bullish vs bearish)  
**Why:** Distinguish positive vs negative narrative spikes  
**How:**
```python
snapshot = get_ticker_narrative_snapshot("BTC")
sentiment = snapshot.sentiment_score  # -1 to +1
# Only act on bullish narrative spikes
if sentiment > 0.3 and snapshot.delta_mentions > 20:
    signal = "BULLISH_SPIKE"
```

**Innovation Level:** ⚡ **Medium** - Common but underutilized  
**Implementation Effort:** Low (extract existing field)  
**Value:** Better signal direction

#### 5. **Account-Type Weighted Signals** ⚡ **MEDIUM ALPHA**

**What:** Weight signals by account type (Smart > CT > News)  
**Why:** Smart accounts are more predictive than CT accounts  
**How:**
```python
smart_accounts = [acc for acc in snapshot.accounts if acc.type == "smart"]
ct_accounts = [acc for acc in snapshot.accounts if acc.type == "ct"]
# Weight: 3x for smart accounts, 1x for CT accounts
weighted_mentions = len(smart_accounts) * 3 + len(ct_accounts) * 1
```

**Innovation Level:** ⚡ **Medium** - Logical but not common  
**Implementation Effort:** Medium (requires account type extraction)  
**Value:** Higher quality signals

#### 6. **Multi-Keyword Sector Tracking** ⚡ **MEDIUM ALPHA**

**What:** Track entire sectors (all L2s, all DeFi) via multi-keyword  
**Why:** Sector rotation signals, macro narrative shifts  
**How:**
```python
l2_tickers = ["ARB", "OP", "MATIC", "STRK"]
sector_data = get_multi_keyword_mentions(l2_tickers, window="24h")
# Returns: Aggregate sector narrative strength
sector_momentum = calculate_sector_velocity(sector_data)
```

**Innovation Level:** ⚡ **Medium** - Useful but not novel  
**Implementation Effort:** Medium (new endpoint + aggregation)  
**Value:** Macro-level signals

#### 7. **Trending Tokens Discovery** ⚡ **LOW-MEDIUM ALPHA**

**What:** Query trending tokens leaderboard for discovery  
**Why:** Find new opportunities without knowing tickers  
**How:**
```python
trending = get_trending_tokens(window="1h", limit=20)
# Returns: [{"ticker": "NEWTOKEN", "mentions": 500, "mindshare": 0.15}]
# Filter: Only tokens with smart account activity
alpha_tokens = [t for t in trending if len(t.smart_accounts) >= 3]
```

**Innovation Level:** ⚡ **Low-Medium** - Common but useful  
**Implementation Effort:** Low (new endpoint wrapper)  
**Value:** Discovery automation

---

## 🎯 Recommendations: Phase B Enhancement

### Priority 1: High-Impact, Low-Effort 🔥

1. **Extract Sentiment Scores** (if available in response)
   - Effort: Low (just extract existing field)
   - Impact: Medium (better signal direction)
   - Innovation: Medium

2. **Contract Address Tracking**
   - Effort: Low-Medium (new endpoint)
   - Impact: Very High (early alpha)
   - Innovation: Very High

3. **Trending Tokens Discovery**
   - Effort: Low (new endpoint)
   - Impact: Medium (automated discovery)
   - Innovation: Low-Medium

### Priority 2: High-Impact, Medium-Effort 🔥

4. **Cross-Platform Divergence**
   - Effort: Medium (source filtering + comparison)
   - Impact: Very High (early signals)
   - Innovation: Very High

5. **Event-Driven Filtering**
   - Effort: Medium (new endpoint + logic)
   - Impact: High (better signal quality)
   - Innovation: High

6. **Account-Type Weighting**
   - Effort: Medium (extract + weight)
   - Impact: Medium (better signals)
   - Innovation: Medium

### Priority 3: Medium-Impact, Medium-Effort ⚡

7. **Multi-Keyword Sector Tracking**
   - Effort: Medium (new endpoint + aggregation)
   - Impact: Medium (macro signals)
   - Innovation: Medium

---

## 💎 Unseen Alpha Opportunities

### 1. **Contract Address → Token Launch Prediction** 🔥🔥🔥

**Concept:** Track contract addresses gaining attention BEFORE token launch  
**Why:** Early entry before public launch  
**How:**
- Query trending contract addresses
- Track mention velocity
- Alert when new contract spikes (potential launch)
- Cross-reference with DEX data

**Innovation:** 🔥🔥🔥 **Extremely High** - Unseen in most tools  
**Effort:** Medium-High  
**Value:** Early alpha detection

### 2. **Telegram → Twitter Narrative Lag** 🔥🔥

**Concept:** Telegram groups often discuss tokens before Twitter  
**Why:** Early signal detection  
**How:**
- Compare Telegram vs Twitter mention velocity
- Alert when Telegram spikes first
- Weight Telegram signals higher for early detection

**Innovation:** 🔥🔥 **Very High** - Novel approach  
**Effort:** Medium  
**Value:** Early entry signals

### 3. **Smart Account Cluster Analysis** 🔥🔥

**Concept:** Track which smart accounts mention multiple tokens together  
**Why:** Identify smart money rotation patterns  
**How:**
- Query multiple tickers
- Find accounts mentioning 2+ tickers
- Detect rotation patterns (exiting one, entering another)

**Innovation:** 🔥🔥 **Very High** - Advanced pattern  
**Effort:** Medium-High  
**Value:** Smart money flow tracking

### 4. **News vs Organic Narrative Divergence** 🔥

**Concept:** Distinguish news-driven vs organic narrative spikes  
**Why:** News spikes are less predictive than organic momentum  
**How:**
- Query news mentions separately
- Compare news-driven vs organic mentions
- Only act on organic spikes (no major news events)

**Innovation:** 🔥 **High** - Context-aware  
**Effort:** Medium  
**Value:** Better signal quality

---

## 📊 Summary: Are We Doing Enough?

### Current State: **Good Foundation, Missing Alpha**

**Strengths:**
- ✅ Solid temporal analysis (velocity/acceleration)
- ✅ Account churn tracking
- ✅ Multi-source signal fusion
- ✅ Explainable outputs
- ✅ Decision Moment framework

**Gaps:**
- ❌ Only using ~12.5% of available free plan features
- ❌ Missing contract address tracking (high alpha)
- ❌ Missing cross-platform analysis (high alpha)
- ❌ Missing sentiment extraction (medium alpha)
- ❌ Missing event-driven filtering (medium alpha)

### Phase B Enhancement Recommendations

**To maximize innovation and alpha:**

1. **Immediate (Low Effort, High Impact):**
   - Extract sentiment scores
   - Add contract address tracking
   - Add trending tokens discovery

2. **Short-term (Medium Effort, Very High Impact):**
   - Cross-platform divergence analysis
   - Event-driven filtering
   - Account-type weighting

3. **Long-term (Higher Effort, Very High Innovation):**
   - Smart account cluster analysis
   - Contract → Token launch prediction
   - Multi-keyword sector tracking

### Innovation Score

**Current:** 7/10 - Good foundation, solid execution  
**Potential:** 9/10 - With enhancements, could be industry-leading  
**Gap:** Missing high-alpha opportunities (contract addresses, cross-platform)

---

## 🎯 Conclusion

**We're doing well on execution and architecture, but we're leaving alpha on the table.**

The Elfa API provides rich data we're not fully utilizing. The biggest opportunities are:

1. **Contract address tracking** (early alpha detection)
2. **Cross-platform analysis** (early signal detection)
3. **Event-driven filtering** (better signal quality)

These are **unseen alpha opportunities** that could differentiate our tools significantly.

**Recommendation:** Prioritize contract address tracking and cross-platform divergence as Phase B enhancements. These offer the highest innovation-to-effort ratio and provide genuine alpha opportunities not commonly found in other tools.

---

*Last Updated: 2025-12-15*  
*Based on Elfa API Documentation and current codebase analysis*

