#!/usr/bin/env python3
"""
Test script to verify provider registry and fallback mechanism.

Usage:
    python optional/test_provider_fallback.py BTC
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from optional.onchain_client import get_onchain_data
from optional.provider_registry import fetch_with_fallback, list_providers


def test_provider_registry():
    """Test the provider registry system."""
    print("=" * 80)
    print("Provider Registry Test")
    print("=" * 80)
    
    print(f"\n📋 Available providers: {', '.join(list_providers())}")
    
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"\n🔍 Testing with ticker: {ticker}\n")
    
    # Test 1: Fallback mechanism
    print("Test 1: Fallback mechanism (Glassnode → CryptoQuant → ...)")
    print("-" * 80)
    result = fetch_with_fallback(
        ticker=ticker,
        primary_provider="glassnode",
        fallback_providers=["cryptoquant", "zapper", "zerion", "covalent"]
    )
    
    if result:
        print(f"✅ Success! Got data from provider: {result.source_query.split(':')[0]}")
        print(f"\n📊 Data Summary:")
        print(f"   Ticker: {result.ticker}")
        if result.exchange_netflow_btc is not None:
            print(f"   Exchange Netflow: {result.exchange_netflow_btc:+.2f} BTC")
        if result.active_addresses_24h is not None:
            print(f"   Active Addresses (24h): {result.active_addresses_24h:,}")
        if result.transaction_count_24h is not None:
            print(f"   Transaction Count (24h): {result.transaction_count_24h:,}")
        if result.whale_balance_change is not None:
            status = "Accumulating" if result.whale_balance_change > 0 else "Distributing" if result.whale_balance_change < 0 else "Neutral"
            print(f"   Whale Activity: {status}")
        print(f"   Source: {result.source_query}")
    else:
        print("❌ All providers failed (check API keys)")
    
    print("\n" + "=" * 80)
    
    # Test 2: Single provider mode
    print("\nTest 2: Single provider mode (no fallback)")
    print("-" * 80)
    result2 = get_onchain_data(
        ticker=ticker,
        use_cache=False,
        api_provider="glassnode",
        use_fallback=False
    )
    
    if result2:
        print(f"✅ Success! Got data from: {result2.source_query}")
    else:
        print("❌ Provider failed (expected if no API key)")
    
    print("\n" + "=" * 80)
    
    # Test 3: Custom fallback chain
    print("\nTest 3: Custom fallback chain (CryptoQuant → Glassnode)")
    print("-" * 80)
    result3 = get_onchain_data(
        ticker=ticker,
        use_cache=False,
        api_provider="cryptoquant",
        use_fallback=True,
        fallback_providers=["glassnode"]
    )
    
    if result3:
        print(f"✅ Success! Got data from: {result3.source_query}")
    else:
        print("❌ All providers failed")
    
    print("\n" + "=" * 80)
    print("\n✅ Provider registry test complete!")


if __name__ == "__main__":
    test_provider_registry()

