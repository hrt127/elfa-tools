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

from elfa_client import get_ticker_narrative_snapshot, is_organic_narrative_spike, calculate_weighted_mentions, calculate_platform_divergence
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
            
            # Check organic status and sentiment
            organic_analysis = is_organic_narrative_spike(ticker, window, min_mentions=1)
            is_organic = organic_analysis.get("is_organic", True)
            
            # Get weighted mentions for conviction calculation
            weighted_data = calculate_weighted_mentions(snapshot)
            weighted_mentions = weighted_data.get("weighted_mentions", enriched.total_mentions)
            
            # Check sentiment alignment
            sentiment = enriched.sentiment_score
            is_bullish_sentiment = sentiment is not None and sentiment > 0.2
            is_bearish_sentiment = sentiment is not None and sentiment < -0.2
            
            # Check cross-platform divergence
            divergence = calculate_platform_divergence(ticker, window)
            has_early_signal = divergence and divergence.get("early_signal", False)
            
            # Analyze for entry setups
            setups = []
            conviction = 0.0
            reasoning = []
            
            # 1. Narrative Spike (continuation play) - only if organic
            if is_organic and enriched.delta_mentions > 20 and enriched.acceleration is not None and enriched.acceleration > 10:
                setups.append("spike")
                conviction += 0.3
                reasoning.append(f"🚀 Organic narrative spike: +{enriched.delta_mentions} mentions, "
                               f"accel +{enriched.acceleration}")
            elif not is_organic and enriched.delta_mentions > 20:
                reasoning.append(f"⚠️ News-driven spike detected (skipping)")
            
            # 2. Strong Velocity (momentum play) - use weighted mentions
            if velocity_data and velocity_data.get('mentions_velocity', 0) > 15:
                # Use weighted mentions threshold if available
                if weighted_mentions > enriched.total_mentions * 0.8:  # High quality accounts
                    setups.append("momentum")
                    conviction += 0.25
                    reasoning.append(f"📈 Strong momentum: {velocity_data['mentions_velocity']:.1f} mentions/snapshot (weighted: {weighted_mentions:.1f})")
            
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
            
            # 5. Cross-platform divergence (early signal)
            if has_early_signal:
                setups.append("divergence")
                conviction += 0.2
                ratio = divergence.get("divergence_ratio", 1.0)
                platform = divergence.get("leading_platform", "unknown")
                reasoning.append(f"🔍 Early signal: {platform} leading by {ratio:.1f}x")
            
            # 6. High Confidence Composite Signal - check sentiment alignment
            if signal and signal.confidence > 0.7:
                if signal.signal_strength.value in ["strong_bullish", "bullish"]:
                    if is_bullish_sentiment or sentiment is None:
                        setups.append("composite_bullish")
                        conviction += 0.1
                        reasoning.append(f"✅ High-confidence bullish signal ({signal.confidence:.0%})")
                    else:
                        reasoning.append(f"⚠️ Bullish signal but bearish sentiment - caution")
                elif signal.signal_strength.value in ["strong_bearish", "bearish"]:
                    if is_bearish_sentiment or sentiment is None:
                        setups.append("composite_bearish")
                        conviction += 0.1
                        reasoning.append(f"✅ High-confidence bearish signal ({signal.confidence:.0%})")
                    else:
                        reasoning.append(f"⚠️ Bearish signal but bullish sentiment - caution")
            
            # Calculate overall conviction score
            conviction = min(conviction, 1.0)
            
            # Determine entry recommendation - consider sentiment alignment
            # For long setups, require bullish sentiment or neutral
            # For short setups, require bearish sentiment or neutral
            can_long = is_bullish_sentiment or sentiment is None or sentiment > -0.2
            can_short = is_bearish_sentiment or sentiment is None or sentiment < 0.2
            
            if conviction >= 0.6:
                if signal and signal.composite_score > 0 and can_long:
                    recommendation = "STRONG BUY"
                elif signal and signal.composite_score < 0 and can_short:
                    recommendation = "STRONG SELL"
                else:
                    recommendation = "WATCH"  # High conviction but sentiment mismatch
            elif conviction >= 0.4:
                if signal and signal.composite_score > 0 and can_long:
                    recommendation = "BUY"
                elif signal and signal.composite_score < 0 and can_short:
                    recommendation = "SELL"
                else:
                    recommendation = "WATCH"
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
                'weighted_mentions': weighted_mentions,
                'organic': is_organic,
                'sentiment': sentiment,
                'velocity': enriched.delta_mentions,
                'acceleration': enriched.acceleration if enriched.acceleration is not None else 0,
                'mindshare': enriched.mindshare_score,
                'composite_score': signal.composite_score if signal else 0,
                'confidence': signal.confidence if signal else 0,
                'anomaly': anomaly,
                'divergence': divergence if has_early_signal else None,
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
                
                # Check organic status
                organic_analysis = is_organic_narrative_spike(enriched.ticker, enriched.window, min_mentions=1)
                is_organic = organic_analysis.get("is_organic", True)
                
                # Get weighted mentions
                from elfa_client import get_ticker_narrative_snapshot
                snapshot = get_ticker_narrative_snapshot(enriched.ticker, enriched.window)
                weighted_data = calculate_weighted_mentions(snapshot) if snapshot else {}
                weighted_mentions = weighted_data.get("weighted_mentions", enriched.total_mentions)
                
                # Check sentiment
                sentiment = enriched.sentiment_score
                is_bullish_sentiment = sentiment is not None and sentiment > 0.2
                is_bearish_sentiment = sentiment is not None and sentiment < -0.2
                
                # Check divergence
                divergence = calculate_platform_divergence(enriched.ticker, enriched.window)
                has_early_signal = divergence and divergence.get("early_signal", False)
                
                # Analyze for entry setups
                setups = []
                conviction = 0.0
                reasoning = []
                
                # 1. Narrative Spike - only if organic
                if is_organic and enriched.delta_mentions > 20 and enriched.acceleration is not None and enriched.acceleration > 10:
                    setups.append("spike")
                    conviction += 0.3
                    reasoning.append(f"🚀 Organic narrative spike: +{enriched.delta_mentions} mentions")
                
                # 2. Strong Velocity - use weighted mentions
                if velocity_data and velocity_data.get('mentions_velocity', 0) > 15:
                    if weighted_mentions > enriched.total_mentions * 0.8:
                        setups.append("momentum")
                        conviction += 0.25
                        reasoning.append(f"📈 Strong momentum: {velocity_data['mentions_velocity']:.1f} mentions/snapshot (weighted: {weighted_mentions:.1f})")
                
                # 3. Anomaly
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
                
                # 5. Cross-platform divergence
                if has_early_signal:
                    setups.append("divergence")
                    conviction += 0.2
                    ratio = divergence.get("divergence_ratio", 1.0)
                    platform = divergence.get("leading_platform", "unknown")
                    reasoning.append(f"🔍 Early signal: {platform} leading by {ratio:.1f}x")
                
                # 6. High Confidence Composite Signal - check sentiment alignment
                if signal and signal.confidence > 0.7:
                    if signal.signal_strength.value in ["strong_bullish", "bullish"]:
                        if is_bullish_sentiment or sentiment is None:
                            setups.append("composite_bullish")
                            conviction += 0.1
                            reasoning.append(f"✅ High-confidence bullish signal ({signal.confidence:.0%})")
                    elif signal.signal_strength.value in ["strong_bearish", "bearish"]:
                        if is_bearish_sentiment or sentiment is None:
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
                    'anomaly': anomaly,
                    'weighted_mentions': weighted_mentions,
                    'organic': is_organic,
                    'sentiment': sentiment,
                    'divergence': divergence if has_early_signal else None
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
            metrics_parts = [
                f"{result['mentions']} mentions",
                f"weighted {result.get('weighted_mentions', result['mentions']):.1f}" if result.get('weighted_mentions') else None,
                f"velocity {result['velocity']:+d}",
                f"accel {result['acceleration']:+d}" if result.get('acceleration') is not None else "accel N/A",
                f"mindshare {result['mindshare']:.2f}" if result.get('mindshare') else None
            ]
            metrics_str = ", ".join([m for m in metrics_parts if m])
            print(f"   Metrics: {metrics_str}")
            
            # Print sentiment and organic status
            if result.get('sentiment') is not None:
                sentiment_label = "Bullish" if result['sentiment'] > 0.2 else "Bearish" if result['sentiment'] < -0.2 else "Neutral"
                print(f"   Sentiment: {result['sentiment']:+.2f} ({sentiment_label})")
            if result.get('organic') is not None:
                organic_label = "✅ Organic" if result['organic'] else "⚠️ News-driven"
                print(f"   Status: {organic_label}")
            
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
