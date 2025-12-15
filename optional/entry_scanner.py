#!/usr/bin/env python3
"""
entry_scanner.py - Find high-conviction entry setups

Scans watchlist for high-quality entry opportunities:
- Narrative spikes (continuation plays)
- Strong velocity (momentum to ride)
- Anomalies (mean reversion plays)
- Smart money activity (follow the flow)

Usage:
    python entry_scanner.py BTC ETH SOL HYPE PENGU
    python entry_scanner.py --watchlist watchlist.txt
"""

import sys
import argparse
from typing import List, Dict, Optional
from datetime import datetime

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher
from optional.delta_store import DeltaStore
from optional.signal_composer import SignalComposer
from optional.perp_client import get_perp_market_data


class EntryScanner:
    """Scans tickers for high-conviction entry setups."""
    
    def __init__(self):
        self.enricher = NarrativeEnricher()
        self.store = DeltaStore()
        self.composer = SignalComposer()
    
    def scan_ticker(self, ticker: str, window: str = "4h") -> Optional[Dict]:
        """
        Scan a single ticker for entry opportunities.
        
        Returns dict with setup analysis or None if no data.
        Never raises exceptions.
        """
        try:
            # Get narrative data
            snapshot = get_ticker_narrative_snapshot(ticker, window=window)
            if not snapshot:
                return None
            
            # Enrich with velocity/acceleration
            enriched = self.enricher.enrich_snapshot(snapshot)
            self.store.insert(enriched)
            
            # Get historical context
            velocity_data = self.store.calculate_velocity(ticker, window=window)
            anomaly = self.store.detect_anomalies(ticker, window=window, std_threshold=2.0)
            
            # Get market data for composite signal
            market_data = get_perp_market_data(ticker)
            
            # Generate composite signal
            signal = self.composer.compose(
                ticker=ticker,
                narrative_data=enriched,
                market_data={
                    'funding_rate': market_data.funding_rate if market_data else 0,
                    'price_change_24h': market_data.price_change_24h if market_data else 0,
                    'volume_ratio': market_data.volume_ratio if market_data else 1.0
                } if market_data else None
            )
            
            # Analyze for entry setups
            setups = []
            conviction = 0.0
            reasoning = []
            
            # 1. Narrative Spike (continuation play)
            if enriched.delta_mentions > 20 and enriched.acceleration is not None and enriched.acceleration > 10:
                setups.append("spike")
                conviction += 0.3
                reasoning.append(f"🚀 Narrative spike: +{enriched.delta_mentions} mentions, "
                               f"accel +{enriched.acceleration}" if enriched.acceleration is not None else "accel N/A")
            
            # 2. Strong Velocity (momentum play)
            if velocity_data and velocity_data.get('mentions_velocity', 0) > 15:
                setups.append("momentum")
                conviction += 0.25
                reasoning.append(f"📈 Strong momentum: {velocity_data['mentions_velocity']:.1f} mentions/snapshot")
            
            # 3. Anomaly (mean reversion play)
            if anomaly and abs(anomaly['z_score']) >= 2.5:
                setups.append("anomaly")
                conviction += 0.2
                direction = "spike" if anomaly['z_score'] > 0 else "drop"
                reasoning.append(f"🚨 Statistical anomaly: {anomaly['z_score']:+.1f}σ ({direction})")
            
            # 4. Smart Money Activity
            if enriched.new_accounts and len(enriched.new_accounts) >= 2:
                setups.append("smart_money")
                conviction += 0.15
                reasoning.append(f"💡 Smart money: {len(enriched.new_accounts)} new accounts")
            
            # 5. High Confidence Composite Signal
            if signal and signal.confidence > 0.7:
                if signal.signal_strength.value in ["strong_bullish", "bullish"]:
                    setups.append("composite_bullish")
                    conviction += 0.1
                    reasoning.append(f"✅ High-confidence bullish signal ({signal.confidence:.0%})")
                elif signal.signal_strength.value in ["strong_bearish", "bearish"]:
                    setups.append("composite_bearish")
                    conviction += 0.1
                    reasoning.append(f"✅ High-confidence bearish signal ({signal.confidence:.0%})")
            
            # Calculate overall conviction score
            conviction = min(conviction, 1.0)
            
            # Determine entry recommendation
            if conviction >= 0.6:
                recommendation = "STRONG BUY" if signal and signal.composite_score > 0 else "STRONG SELL"
            elif conviction >= 0.4:
                recommendation = "BUY" if signal and signal.composite_score > 0 else "SELL"
            elif conviction >= 0.2:
                recommendation = "WATCH"
            else:
                recommendation = "PASS"
            
            return {
                'ticker': ticker,
                'conviction': conviction,
                'recommendation': recommendation,
                'setups': setups,
                'reasoning': reasoning,
                'mentions': enriched.total_mentions,
                'velocity': enriched.delta_mentions,
                'acceleration': enriched.acceleration if enriched.acceleration is not None else 0,
                'mindshare': enriched.mindshare_score,
                'composite_score': signal.composite_score if signal else 0,
                'confidence': signal.confidence if signal else 0,
                'anomaly': anomaly,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            print(f"Warning: Failed to scan {ticker}: {e}")
            return None
    
    def scan(self, enriched_snapshots: List) -> List[Dict]:
        """
        Scan a list of enriched snapshots for entry opportunities.
        
        Args:
            enriched_snapshots: List of EnrichedSnapshot objects
            
        Returns:
            List of scan results, sorted by conviction (highest first)
        """
        results = []
        for enriched in enriched_snapshots:
            if enriched is None:
                continue
            try:
                # Store snapshot
                self.store.insert(enriched)
                
                # Get historical context
                velocity_data = self.store.calculate_velocity(enriched.ticker, window=enriched.window)
                anomaly = self.store.detect_anomalies(enriched.ticker, window=enriched.window, std_threshold=2.0)
                
                # Get market data
                market_data = get_perp_market_data(enriched.ticker)
                
                # Generate composite signal
                signal = self.composer.compose(
                    ticker=enriched.ticker,
                    narrative_data=enriched,
                    market_data={
                        'funding_rate': market_data.funding_rate if market_data else 0,
                        'price_change_24h': market_data.price_change_24h if market_data else 0,
                        'volume_ratio': market_data.volume_ratio if market_data else 1.0
                    } if market_data else None
                )
                
                # Analyze for entry setups
                setups = []
                conviction = 0.0
                reasoning = []
                
                # 1. Narrative Spike
                if enriched.delta_mentions > 20 and enriched.acceleration is not None and enriched.acceleration > 10:
                    setups.append("spike")
                    conviction += 0.3
                    reasoning.append(f"🚀 Narrative spike: +{enriched.delta_mentions} mentions")
                
                # 2. Strong Velocity
                if velocity_data and velocity_data.get('mentions_velocity', 0) > 15:
                    setups.append("momentum")
                    conviction += 0.25
                    reasoning.append(f"📈 Strong momentum: {velocity_data['mentions_velocity']:.1f} mentions/snapshot")
                
                # 3. Anomaly
                if anomaly and abs(anomaly['z_score']) >= 2.5:
                    setups.append("anomaly")
                    conviction += 0.2
                    direction = "spike" if anomaly['z_score'] > 0 else "drop"
                    reasoning.append(f"🚨 Statistical anomaly: {anomaly['z_score']:+.1f}σ ({direction})")
                
                # 4. Smart Money Activity (consistent with scan_ticker)
                if enriched.new_accounts and len(enriched.new_accounts) >= 2:
                    setups.append("smart_money")
                    conviction += 0.15
                    reasoning.append(f"💡 Smart money: {len(enriched.new_accounts)} new accounts")
                
                # 5. High Confidence Composite Signal (consistent with scan_ticker)
                if signal and signal.confidence > 0.7:
                    if signal.signal_strength.value in ["strong_bullish", "bullish"]:
                        setups.append("composite_bullish")
                        conviction += 0.1
                        reasoning.append(f"✅ High-confidence bullish signal ({signal.confidence:.0%})")
                    elif signal.signal_strength.value in ["strong_bearish", "bearish"]:
                        setups.append("composite_bearish")
                        conviction += 0.1
                        reasoning.append(f"✅ High-confidence bearish signal ({signal.confidence:.0%})")
                
                results.append({
                    'ticker': enriched.ticker,
                    'setups': setups,
                    'conviction': min(conviction, 1.0),  # Cap at 1.0
                    'reasoning': reasoning,
                    'signal': signal,
                    'velocity': velocity_data,
                    'anomaly': anomaly
                })
            except Exception as e:
                print(f"Warning: Failed to scan {enriched.ticker if enriched else 'unknown'}: {e}")
                continue
        
        # Sort by conviction (highest first)
        results.sort(key=lambda x: x['conviction'], reverse=True)
        return results
    
    def scan_watchlist(self, tickers: List[str], window: str = "4h") -> List[Dict]:
        """Scan multiple tickers and return sorted by conviction."""
        results = []
        
        for ticker in tickers:
            result = self.scan_ticker(ticker, window)
            if result:
                results.append(result)
        
        # Sort by conviction (highest first)
        results.sort(key=lambda x: x['conviction'], reverse=True)
        return results
    
    def print_results(self, results: List[Dict]):
        """Print scan results in readable format."""
        if not results:
            print("No entry opportunities found.")
            return
        
        print(f"\n{'='*80}")
        print(f"ENTRY SCANNER RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        for result in results:
            ticker = result['ticker']
            conviction = result['conviction']
            recommendation = result['recommendation']
            setups = result['setups']
            
            # Print header
            if recommendation in ["STRONG BUY", "STRONG SELL"]:
                emoji = "🔥"
            elif recommendation in ["BUY", "SELL"]:
                emoji = "✅"
            elif recommendation == "WATCH":
                emoji = "👀"
            else:
                emoji = "➡️"
            
            print(f"{emoji} {ticker:6s} | {recommendation:12s} | Conviction: {conviction:.0%}")
            print(f"   Setups: {', '.join(setups) if setups else 'None'}")
            
            # Print reasoning
            for reason in result['reasoning']:
                print(f"   {reason}")
            
            # Print metrics
            print(f"   Metrics: {result['mentions']} mentions, "
                  f"velocity {result['velocity']:+d}, "
                  f"accel {result['acceleration']:+d}, " if result.get('acceleration') is not None else "accel N/A, "
                  f"mindshare {result['mindshare']:.2f}" if result['mindshare'] else "N/A")
            
            if result['composite_score']:
                print(f"   Signal: {result['composite_score']:+.2f} "
                      f"({result['confidence']:.0%} confidence)")
            
            if result['anomaly']:
                anomaly = result['anomaly']
                print(f"   🚨 Anomaly: {anomaly['z_score']:+.1f}σ "
                      f"({anomaly['severity']})")
            
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Scan tickers for high-conviction entry setups"
    )
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Ticker symbols to scan (e.g., BTC ETH SOL)'
    )
    parser.add_argument(
        '--watchlist',
        type=str,
        help='File containing ticker symbols (one per line)'
    )
    parser.add_argument(
        '--window',
        type=str,
        default='4h',
        help='Time window for analysis (default: 4h)'
    )
    parser.add_argument(
        '--min-conviction',
        type=float,
        default=0.2,
        help='Minimum conviction score to show (0.0-1.0, default: 0.2)'
    )
    
    args = parser.parse_args()
    
    # Get ticker list
    tickers = []
    if args.watchlist:
        try:
            with open(args.watchlist, 'r') as f:
                tickers = [line.strip().upper() for line in f if line.strip()]
        except Exception as e:
            print(f"Error: Failed to read watchlist file: {e}")
            sys.exit(1)
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        print("Error: No tickers provided. Use --watchlist or provide tickers as arguments.")
        sys.exit(1)
    
    if not tickers:
        print("Error: No tickers to scan.")
        sys.exit(1)
    
    # Scan
    scanner = EntryScanner()
    results = scanner.scan_watchlist(tickers, window=args.window)
    
    # Filter by minimum conviction
    results = [r for r in results if r['conviction'] >= args.min_conviction]
    
    # Print results
    scanner.print_results(results)
    
    # Summary
    if results:
        strong = [r for r in results if r['recommendation'] in ["STRONG BUY", "STRONG SELL"]]
        buy_sell = [r for r in results if r['recommendation'] in ["BUY", "SELL"]]
        watch = [r for r in results if r['recommendation'] == "WATCH"]
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {len(strong)} strong, {len(buy_sell)} moderate, {len(watch)} watch")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
