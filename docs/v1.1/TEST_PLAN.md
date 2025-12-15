# Elfa Tools - Comprehensive Test Plan

**Generated:** 2024-12-13  
**Purpose:** Complete testing strategy for all modules

---

## Test Strategy Overview

### Testing Levels

1. **Unit Tests** - Individual functions and classes
2. **Integration Tests** - Module interactions
3. **API Mock Tests** - External API interactions
4. **Edge Case Tests** - Boundary conditions and error scenarios
5. **Performance Tests** - Rate limiting and caching

### Test Principles

- **Never crash** - All tests should verify graceful error handling
- **Explainable** - Test outputs should be clear
- **Robust** - Tests should handle missing data gracefully
- **Composable** - Tests should work standalone and together

---

## Module Test Plans

### 1. elfa_client.py

#### Unit Tests

**Test: `get_ticker_narrative_snapshot` - Success Case**

```python
def test_get_ticker_narrative_snapshot_success():
    """Test successful API call and response parsing."""
    # Mock API response
    # Verify TickerNarrativeSnapshot structure
    # Verify cache storage
    # Verify source_query field
```

**Test: `get_ticker_narrative_snapshot` - Cache Hit**

```python
def test_get_ticker_narrative_snapshot_cache_hit():
    """Test cache retrieval without API call."""
    # Populate cache
    # Call function with use_cache=True
    # Verify no API call made
    # Verify cached data returned
```

**Test: `get_ticker_narrative_snapshot` - Rate Limit**

```python
def test_get_ticker_narrative_snapshot_rate_limit():
    """Test rate limit handling."""
    # Simulate 60 requests in 60 seconds
    # Verify 61st request returns None
    # Verify warning message
```

**Test: `get_ticker_narrative_snapshot` - Ticker Not Found**

```python
def test_get_ticker_narrative_snapshot_ticker_not_found():
    """Test handling when ticker not in response."""
    # Mock API response without requested ticker
    # Verify returns None (not first result)
    # Verify warning message
```

**Test: `get_ticker_narrative_snapshot` - API Error Handling**

```python
def test_get_ticker_narrative_snapshot_api_errors():
    """Test various API error scenarios."""
    # Test 401 (authentication)
    # Test 404 (not found)
    # Test 429 (rate limit)
    # Test 500 (server error)
    # Test timeout
    # Test connection error
    # Verify all return None gracefully
```

**Test: `_is_rate_limited` - Rate Limit Tracking**

```python
def test_rate_limit_tracking():
    """Test rate limit tracker logic."""
    # Add 60 requests
    # Verify 61st is rate limited
    # Wait 61 seconds
    # Verify rate limit cleared
```

**Test: `_get_cached_result` - Cache Expiration**

```python
def test_cache_expiration():
    """Test cache TTL expiration."""
    # Cache result with TTL
    # Wait for expiration
    # Verify cache miss
```

#### Edge Cases

- Empty API response
- Malformed JSON
- Missing fields in response
- Very long ticker names
- Special characters in ticker names
- Concurrent requests

---

### 2. narrative_enricher.py

#### Unit Tests

**Test: `enrich_snapshot` - First Snapshot**

```python
def test_enrich_snapshot_first_snapshot():
    """Test enrichment with no previous data."""
    # Create first snapshot
    # Verify delta_mentions = total_mentions
    # Verify acceleration = 0 (not velocity)
    # Verify no account churn
```

**Test: `enrich_snapshot` - Second Snapshot**

```python
def test_enrich_snapshot_second_snapshot():
    """Test enrichment with one previous snapshot."""
    # Create two snapshots
    # Verify delta_mentions calculated
    # Verify acceleration = 0 (only 2 snapshots)
    # Verify account churn calculated
```

**Test: `enrich_snapshot` - Third Snapshot (True Acceleration)**
```python
def test_enrich_snapshot_third_snapshot():
    """Test enrichment with two previous snapshots."""
    # Create three snapshots
    # Verify acceleration calculated correctly
    # Verify velocity and acceleration both present
```

**Test: `enrich_snapshot` - Account Churn**
```python
def test_enrich_snapshot_account_churn():
    """Test account churn detection."""
    # Snapshot 1: accounts [A, B, C]
    # Snapshot 2: accounts [B, C, D]
    # Verify new_accounts = [D]
    # Verify lost_accounts = [A]
```

**Test: `store_snapshot` - Persistence**
```python
def test_store_snapshot_persistence():
    """Test snapshot storage to SQLite."""
    # Store snapshot
    # Query database
    # Verify data persisted correctly
```

**Test: `get_last_snapshot` - Retrieval**
```python
def test_get_last_snapshot():
    """Test retrieving last snapshot."""
    # Store multiple snapshots
    # Get last snapshot
    # Verify correct snapshot returned
```

#### Edge Cases

- Empty account lists
- None values for mindshare
- Very large mention counts
- Negative deltas
- Missing timestamps
- Database connection failures

---

### 3. signal_composer.py

#### Unit Tests

**Test: `compose` - All Data Sources Available**
```python
def test_compose_all_sources():
    """Test composition with all data sources."""
    # Provide narrative, market, on-chain data
    # Verify composite score calculated
    # Verify weights: 40% narrative, 35% market, 25% on-chain
    # Verify confidence calculation
```

**Test: `compose` - Missing On-Chain Data**
```python
def test_compose_missing_onchain():
    """Test weight normalization when on-chain missing."""
    # Provide narrative and market data only
    # Verify weights normalized: ~53% narrative, ~47% market
    # Verify on-chain score = 0
    # Verify composite still calculated
```

**Test: `compose` - Only Narrative Data**
```python
def test_compose_only_narrative():
    """Test composition with only narrative data."""
    # Provide narrative data only
    # Verify weight = 100% narrative
    # Verify composite = narrative score
```

**Test: `compose` - Conflicting Signals**
```python
def test_compose_conflicting_signals():
    """Test confidence calculation with conflicting signals."""
    # Narrative: +0.5 (bullish)
    # Market: -0.5 (bearish)
    # Verify signal_strength = CONFLICTED
    # Verify confidence < 0.5
```

**Test: `_score_narrative` - Scoring Logic**
```python
def test_score_narrative():
    """Test narrative scoring components."""
    # Test mindshare component (0-0.4)
    # Test velocity component (-0.3 to 0.3)
    # Test smart accounts component (0-0.3)
    # Verify score clamped to [-1, 1]
```

**Test: `_score_market` - Market Scoring**
```python
def test_score_market():
    """Test market scoring logic."""
    # Test funding rate component
    # Test price momentum component
    # Test volume component
    # Verify score clamped to [-1, 1]
```

**Test: `_calculate_confidence` - Confidence Calculation**
```python
def test_calculate_confidence():
    """Test confidence calculation logic."""
    # Test high agreement (all positive)
    # Test mixed signals (low confidence)
    # Test high magnitude + low std dev (high confidence)
```

#### Edge Cases

- All data sources None
- Extreme score values
- Zero scores
- Missing fields in data dicts
- Invalid data types

---

### 4. delta_store.py

#### Unit Tests

**Test: `insert` - Snapshot Storage**
```python
def test_insert_snapshot():
    """Test inserting snapshot to DuckDB."""
    # Insert EnrichedSnapshot
    # Query database
    # Verify data stored correctly
```

**Test: `calculate_velocity` - Velocity Calculation**
```python
def test_calculate_velocity():
    """Test velocity calculation with time delta."""
    # Create snapshots with known timestamps
    # Calculate velocity
    # Verify uses time delta, not snapshot count
    # Verify mentions_velocity in mentions/hour
```

**Test: `calculate_velocity` - Insufficient Data**
```python
def test_calculate_velocity_insufficient_data():
    """Test velocity with < 2 snapshots."""
    # Create single snapshot
    # Verify returns None
```

**Test: `detect_anomalies` - Anomaly Detection**
```python
def test_detect_anomalies():
    """Test statistical anomaly detection."""
    # Create history with known mean/std
    # Add outlier
    # Verify z-score calculated correctly
    # Verify anomaly detected if |z| >= threshold
```

**Test: `detect_anomalies` - Insufficient Data**
```python
def test_detect_anomalies_insufficient_data():
    """Test anomaly detection with < 10 snapshots."""
    # Create < 10 snapshots
    # Verify returns None
```

**Test: `get_history` - Historical Retrieval**
```python
def test_get_history():
    """Test retrieving historical snapshots."""
    # Store multiple snapshots over time
    # Query with hours_back parameter
    # Verify correct snapshots returned
    # Verify ordered by timestamp ASC
```

#### Edge Cases

- Empty database
- Very old timestamps
- Concurrent inserts
- Database connection failures
- Invalid timestamp formats

---

### 5. alerts_engine.py

#### Unit Tests

**Test: `check_all` - Rule Triggering**
```python
def test_check_all_rule_triggering():
    """Test rule evaluation and alert firing."""
    # Add rule with condition
    # Provide data that matches condition
    # Verify alert fired
    # Verify message formatted correctly
```

**Test: `check_all` - Cooldown Persistence**
```python
def test_check_all_cooldown_persistence():
    """Test cooldown state persistence across restarts."""
    # Trigger alert
    # Verify cooldown saved to database
    # Create new engine instance
    # Verify cooldown loaded from database
    # Verify alert not fired during cooldown
```

**Test: `check_all` - Cooldown Expiration**
```python
def test_check_all_cooldown_expiration():
    """Test cooldown expiration."""
    # Trigger alert
    # Wait for cooldown to expire
    # Verify alert can fire again
```

**Test: `add_rule` - Cooldown Loading**
```python
def test_add_rule_cooldown_loading():
    """Test loading cooldown state when adding rule."""
    # Save cooldown state to database
    # Add rule
    # Verify cooldown state loaded
```

**Test: `_normalize_data` - Data Normalization**
```python
def test_normalize_data():
    """Test data normalization from various formats."""
    # Test TickerNarrativeSnapshot
    # Test EnrichedSnapshot
    # Test Dict
    # Verify all normalized to same format
```

**Test: `get_history` - Alert History**
```python
def test_get_history():
    """Test retrieving alert history."""
    # Fire multiple alerts
    # Query history
    # Verify correct alerts returned
    # Verify ordered by timestamp DESC
```

#### Edge Cases

- Multiple rules for same ticker
- Rules with no cooldown
- Very long cooldown periods
- Database write failures
- Invalid rule conditions

---

### 6. entry_scanner.py

#### Integration Tests

**Test: `scan_ticker` - Complete Flow**
```python
def test_scan_ticker_complete_flow():
    """Test complete entry scanner flow."""
    # Mock API responses
    # Run scan_ticker
    # Verify all components called:
    #   - elfa_client
    #   - narrative_enricher
    #   - delta_store
    #   - perp_client
    #   - signal_composer
    # Verify result structure
    # Verify conviction calculation
```

**Test: `scan_ticker` - Setup Detection**
```python
def test_scan_ticker_setup_detection():
    """Test detection of various entry setups."""
    # Test spike setup (high delta + acceleration)
    # Test momentum setup (high velocity)
    # Test anomaly setup (high z-score)
    # Test smart money setup (new accounts)
    # Verify correct setups identified
```

**Test: `scan_watchlist` - Multiple Tickers**
```python
def test_scan_watchlist():
    """Test scanning multiple tickers."""
    # Provide list of tickers
    # Verify all scanned
    # Verify sorted by conviction
    # Verify failed tickers handled gracefully
```

#### Edge Cases

- No data available for ticker
- Partial data (some APIs fail)
- Very high/low conviction scores
- Empty watchlist

---

### 7. pre_trade_check.py

#### Integration Tests

**Test: `check_trade` - Long Trade Validation**
```python
def test_check_trade_long():
    """Test long trade validation."""
    # Positive velocity → APPROVED
    # Negative velocity → BLOCKED
    # Positive acceleration → APPROVED
    # Negative acceleration → BLOCKED
    # Bullish composite → APPROVED
    # Bearish composite → BLOCKED
```

**Test: `check_trade` - Short Trade Validation**
```python
def test_check_trade_short():
    """Test short trade validation."""
    # Negative velocity → APPROVED
    # Positive velocity → BLOCKED
    # Negative acceleration → APPROVED
    # Positive acceleration → BLOCKED
    # Bearish composite → APPROVED
    # Bullish composite → BLOCKED
```

**Test: `check_trade` - Confidence Levels**
```python
def test_check_trade_confidence():
    """Test confidence-based validation."""
    # High confidence + aligned signals → APPROVED (high)
    # Medium confidence → APPROVED (moderate)
    # Low confidence → APPROVED (low) or BLOCKED
```

#### Edge Cases

- No narrative data available
- Missing market data
- Conflicting signals
- Edge case velocity/acceleration values

---

### 8. narrative_radar.py

#### Integration Tests

**Test: `main` - CLI Execution**
```python
def test_main_cli_execution():
    """Test main CLI function."""
    # Mock argparse arguments
    # Mock API responses
    # Run main()
    # Verify output format
    # Verify markdown export (if requested)
```

**Test: `display_cli_radar` - Output Formatting**
```python
def test_display_cli_radar():
    """Test CLI output formatting."""
    # Create enriched snapshots
    # Call display_cli_radar
    # Verify table format
    # Verify indicators (🚀, 📈, etc.)
```

**Test: `export_markdown` - Markdown Export**
```python
def test_export_markdown():
    """Test markdown export functionality."""
    # Create enriched snapshots
    # Export to markdown
    # Verify file created
    # Verify markdown format correct
```

#### Edge Cases

- No tickers provided
- All tickers fail
- Empty results
- Invalid window format

---

## Integration Test Scenarios

### Scenario 1: Complete Workflow

```text
1. Fetch narrative data (elfa_client)
2. Enrich with velocity/acceleration (narrative_enricher)
3. Store in DuckDB (delta_store)
4. Calculate composite signal (signal_composer)
5. Check alerts (alerts_engine)
6. Generate output (narrative_radar)
```

**Test:** Verify all components work together correctly.

---

### Scenario 2: Error Propagation

```text
1. API call fails
2. Verify graceful degradation
3. Verify partial results still work
4. Verify error messages clear
```

**Test:** Verify errors don't crash system.

---

### Scenario 3: Rate Limiting

```text
1. Make 60 API calls rapidly
2. Verify 61st call rate limited
3. Wait for window to expire
4. Verify calls resume
```

**Test:** Verify rate limiting works correctly.

---

### Scenario 4: Cache Behavior

```text
1. Make API call (cache miss)
2. Make same call immediately (cache hit)
3. Wait for TTL expiration
4. Make call again (cache miss)
```

**Test:** Verify caching works correctly.

---

## API Mocking Strategy

### Mock Framework

Use `unittest.mock` or `responses` library to mock HTTP requests.

### Mock Responses

**Elfa API Mock:**

```python
{
    "results": [
        {
            "ticker": "BTC",
            "total_mentions": 100,
            "mindshare_score": 0.15,
            "top_smart_accounts": ["account1", "account2", "account3"]
        }
    ]
}
```

**Binance API Mock:**

```python
# Premium Index
{
    "lastFundingRate": "0.0001"
}

# 24hr Ticker
{
    "lastPrice": "50000",
    "priceChangePercent": "2.5",
    "volume": "1000000"
}
```


---

## Test Data Setup

### Fixtures

**Create test fixtures for:**

- TickerNarrativeSnapshot
- EnrichedSnapshot
- CompositeSignal
- AlertRule
- Historical snapshots

### Database Setup

**For each test:**

- Create temporary database files
- Clean up after test
- Use in-memory databases when possible


---

## Performance Tests

### Test: Rate Limit Performance

- Measure time for 60 requests
- Verify no rate limit violations
- Measure cleanup time

---

### Test: Cache Performance

- Measure cache hit time
- Measure cache miss time (with API call)
- Verify cache reduces API calls

---

### Test: Database Performance

- Measure insert time
- Measure query time
- Test with large datasets (1000+ snapshots)


---

## Test Coverage Goals

### Target Coverage

- **Unit Tests:** 90%+ code coverage
- **Integration Tests:** All major workflows
- **Edge Cases:** All identified edge cases
- **Error Handling:** All error paths

### Critical Paths

Must have 100% coverage:
- API error handling
- Rate limiting logic
- Cache logic
- Database operations
- Signal composition
- Alert cooldown logic

---

## Test Execution

### Running Tests

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_elfa_client.py

# Run with coverage
pytest --cov=elfa_tools --cov-report=html

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

### Continuous Integration

**CI Pipeline:**
1. Lint code
2. Run unit tests
3. Run integration tests
4. Generate coverage report
5. Check coverage thresholds

---

## Test Maintenance

### When to Update Tests

- New features added
- Bug fixes
- API changes
- Logic changes
- Edge cases discovered

### Test Documentation

- Each test should have docstring
- Explain what is being tested
- Document expected behavior
- Note any assumptions

---

## Known Test Gaps

### Areas Needing Tests

1. **onchain_client.py** - Template, not implemented
2. **narrative_heatmap.py** - Visualization tests
3. **narrative_digest.py** - Format generation tests
4. **decision_moment.py** - Policy engine tests

### Future Test Additions

- Load testing
- Stress testing
- Security testing
- Performance benchmarking

---

*End of Test Plan*
