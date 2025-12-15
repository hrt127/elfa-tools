# Provider Registry System

## Overview

The provider registry system provides a unified interface to multiple on-chain data providers with automatic fallback logic. This ensures high availability and redundancy when fetching on-chain metrics.

## Architecture

```
get_onchain_data()
    ↓
provider_registry.fetch_with_fallback()
    ↓
Try primary provider → If fails, try fallback providers in order
    ↓
Return OnChainData from first successful provider
```

## Available Providers

| Provider | Status | API Key Required | Data Provided |
|----------|--------|------------------|---------------|
| **Glassnode** | ✅ Implemented | `GLASSNODE_API_KEY` | Exchange flows, active addresses, transactions, whale metrics |
| **CryptoQuant** | 🚧 Placeholder | `CRYPTOQUANT_API_KEY` | Exchange flows, miner reserves, stablecoin metrics |
| **Zapper** | 🚧 Placeholder | `ZAPPER_API_KEY` | Portfolio balances, DeFi positions, multi-chain data |
| **Zerion** | 🚧 Placeholder | `ZERION_API_KEY` | Wallet balances, NFT holdings, DeFi positions |
| **Covalent** | 🚧 Placeholder | `COVALENT_API_KEY` | Multi-chain transactions, token balances, historical data |

## Usage

### Basic Usage (Automatic Fallback)

```python
from optional.onchain_client import get_onchain_data

# Automatically tries Glassnode first, then falls back to other providers
data = get_onchain_data("BTC", use_fallback=True)
```

### Single Provider (No Fallback)

```python
# Only try Glassnode, fail if it doesn't work
data = get_onchain_data("BTC", api_provider="glassnode", use_fallback=False)
```

### Custom Fallback Chain

```python
# Try CryptoQuant first, then Glassnode, then Zapper
data = get_onchain_data(
    "BTC",
    api_provider="cryptoquant",
    use_fallback=True,
    fallback_providers=["glassnode", "zapper"]
)
```

### Direct Provider Registry Usage

```python
from optional.provider_registry import fetch_with_fallback, list_providers

# List available providers
print(list_providers())  # ['glassnode', 'cryptoquant', 'zapper', 'zerion', 'covalent']

# Fetch with custom fallback
data = fetch_with_fallback(
    ticker="BTC",
    primary_provider="glassnode",
    fallback_providers=["cryptoquant", "zapper"]
)
```

## Fallback Logic

The system implements intelligent fallback:

1. **Primary Provider**: Tries the specified primary provider first
2. **Rate Limiting**: If primary is rate-limited, automatically tries fallbacks
3. **Error Handling**: If primary fails (API error, missing key, etc.), tries next provider
4. **Graceful Degradation**: Returns `None` only if all providers fail

### Default Fallback Chain

If no custom fallback chain is specified, the system tries providers in this order:

1. Glassnode (primary if not specified)
2. CryptoQuant
3. Zapper
4. Zerion
5. Covalent

## Provider-Specific Notes

### Glassnode

- **Status**: ✅ Fully implemented
- **Metrics**: Exchange netflow, active addresses, transaction count, whale balance changes
- **Rate Limits**: 60 requests/minute (handled automatically)
- **Cache TTL**: 10 minutes

### CryptoQuant

- **Status**: 🚧 Placeholder (needs implementation)
- **API Docs**: https://cryptoquant.com/api
- **Metrics**: Exchange flows, miner reserves, stablecoin metrics

### Zapper

- **Status**: 🚧 Placeholder (needs implementation)
- **API Docs**: https://docs.zapper.fi/
- **Metrics**: Portfolio balances, DeFi positions, multi-chain data

### Zerion

- **Status**: 🚧 Placeholder (needs implementation)
- **API Docs**: https://docs.zerion.io/
- **Metrics**: Wallet balances, NFT holdings, DeFi positions

### Covalent

- **Status**: 🚧 Placeholder (needs implementation)
- **API Docs**: https://www.covalenthq.com/docs/api/
- **Metrics**: Multi-chain transactions, token balances, historical data

## Testing

Run the test script to verify provider registry functionality:

```bash
python optional/test_provider_fallback.py BTC
```

This will test:
1. Automatic fallback mechanism
2. Single provider mode
3. Custom fallback chains

## Environment Variables

Set API keys for providers you want to use:

```bash
export GLASSNODE_API_KEY=your_glassnode_key
export CRYPTOQUANT_API_KEY=your_cryptoquant_key
export ZAPPER_API_KEY=your_zapper_key
export ZERION_API_KEY=your_zerion_key
export COVALENT_API_KEY=your_covalent_key
```

## Integration with Signal Composer

The provider registry integrates seamlessly with `signal_composer`:

```python
from optional.onchain_client import get_onchain_data
from optional.signal_composer import SignalComposer

# Get on-chain data with automatic fallback
onchain_data = get_onchain_data("BTC", use_fallback=True)

# Use in signal composition
composer = SignalComposer()
signal = composer.compose(
    ticker="BTC",
    narrative_data=enriched_snapshot,
    market_data=perp_data,
    onchain_data=onchain_data  # Automatically uses best available provider
)
```

## Best Practices

1. **Always use fallback**: Enable `use_fallback=True` for production use
2. **Set multiple API keys**: More providers = better redundancy
3. **Monitor provider health**: Check `source_query` field to see which provider succeeded
4. **Cache results**: Use `use_cache=True` to reduce API calls
5. **Handle None gracefully**: Always check if data is None before using

## Future Enhancements

- [ ] Implement CryptoQuant API integration
- [ ] Implement Zapper API integration
- [ ] Implement Zerion API integration
- [ ] Implement Covalent API integration
- [ ] Add provider health monitoring
- [ ] Add provider performance metrics
- [ ] Add automatic provider selection based on success rate
- [ ] Add support for provider-specific rate limit handling

