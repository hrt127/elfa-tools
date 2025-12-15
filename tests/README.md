# Elfa Tools Test Suite

Comprehensive test suite following the test plan in [../TEST_PLAN.md](../TEST_PLAN.md).

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── conftest.py           # Shared fixtures and configuration
├── test_elfa_client.py  # API client tests
├── test_narrative_enricher.py  # Enrichment tests
├── test_signal_composer.py    # Signal composition tests
└── README.md            # This file
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_elfa_client.py
```

### Run Specific Test

```bash
pytest tests/test_elfa_client.py::TestGetTickerNarrativeSnapshot::test_success_case
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run with Verbose Output

```bash
pytest -v
```

### Run Only Fast Tests

```bash
pytest -m "not slow"
```

## Test Principles

All tests follow the design principles:

- **Never crash** - Tests verify graceful error handling
- **Explainable** - Test names and docstrings are clear
- **Robust** - Tests handle missing data gracefully
- **Composable** - Tests work standalone and together

## Test Coverage Goals

- **Unit Tests:** 90%+ code coverage
- **Integration Tests:** All major workflows
- **Edge Cases:** All identified edge cases
- **Error Handling:** All error paths

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `mock_env_elfa_api_key` - Sets ELFA_API_KEY for tests
- `sample_ticker_snapshot` - Sample TickerNarrativeSnapshot
- `sample_enriched_snapshot` - Sample EnrichedSnapshot
- `sample_composite_signal` - Sample CompositeSignal
- `mock_elfa_api_response` - Mock Elfa API response
- `mock_binance_premium_index` - Mock Binance premium index
- `mock_binance_ticker_24hr` - Mock Binance 24hr ticker
- `temp_db_path` - Temporary SQLite database path
- `temp_duckdb_path` - Temporary DuckDB path
- `temp_alerts_db_path` - Temporary alerts database path
- `clear_caches` - Clears all caches before/after tests

## Writing New Tests

1. Follow the naming convention: `test_<module_name>.py`
2. Use descriptive test class names: `Test<FeatureName>`
3. Use descriptive test method names: `test_<scenario>`
4. Include docstrings explaining what is being tested
5. Use fixtures from `conftest.py` when possible
6. Mock external API calls
7. Use temporary databases for persistence tests
8. Clean up after tests

## Example Test

```python
def test_success_case(self, mock_env_elfa_api_key, mock_elfa_api_response):
    """Test successful API call and response parsing."""
    with patch('elfa_client.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_elfa_api_response
        mock_get.return_value = mock_response
        
        result = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
        
        assert result is not None
        assert result.ticker == "BTC"
```

## Continuous Integration

Tests should pass in CI with:

```bash
pytest --cov=. --cov-report=term --cov-fail-under=70
```

## Known Test Gaps

See [TEST_PLAN.md](../TEST_PLAN.md) for areas needing tests:

- `onchain_client.py` - Template, not implemented
- `narrative_heatmap.py` - Visualization tests
- `narrative_digest.py` - Format generation tests
- `decision_moment.py` - Policy engine tests
