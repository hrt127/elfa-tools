#!/usr/bin/env python3
"""
pre_trade_check.py - Validate trades before entry

Prevents bad trades by checking narrative state before you enter:
- Buying calls when narrative is fading ❌
- Shorting into a narrative spike ❌
- Trading without momentum confirmation ❌

Usage:
    python pre_trade_check.py TICKER long
    python pre_trade_check.py TICKER short
    python pre_trade_check.py BTC long --window 1h
"""

import sys
import argparse
from typing import Optional, Dict
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


class PreTradeChecker:
    """Validates trades before entry based on narrative state."""
    
    def __init__(self):
        self.enricher = NarrativeEnricher()
        self.store = DeltaStore()
        self.composer = SignalComposer()
    
    def check_trade(
        self,
        ticker: str,
        side: str,
        window: str = "1h"
    ) -> Dict:
        """
        Check if a trade is valid given current narrative state.
        
        Args:
            ticker: Ticker symbol
            side: "long" or "short"
            window: Time window for analysis
        
        Returns:
            Dict with validation result and reasoning.
        Never raises exceptions.
        """
        try:
            # Get narrative data
            snapshot = get_ticker_narrative_snapshot(ticker, window=window, use_cache=False)
            if not snapshot:
                return {
                    'valid': False,
                    'reason': "No narrative data available",
                    'confidence': 0.0
                }
            
            # Enrich with velocity/acceleration
            enriched = self.enricher.enrich_snapshot(snapshot)
            self.store.insert(enriched)
            
            # Get historical context
            velocity_data = self.store.calculate_velocity(ticker, window=window)
            anomaly = self.store.detect_anomalies(ticker, window=window, std_threshold=2.0)
            
            # Get market data
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
            
            # Check organic status
            organic_analysis = is_organic_narrative_spike(ticker, window, min_mentions=1)
            is_organic = organic_analysis.get("is_organic", True)
            
            # Get weighted mentions for confidence calculation
            weighted_data = calculate_weighted_mentions(snapshot)
            weighted_mentions = weighted_data.get("weighted_mentions", enriched.total_mentions)
            
            # Check sentiment alignment
            sentiment = enriched.sentiment_score
            is_bullish_sentiment = sentiment is not None and sentiment > 0.2
            is_bearish_sentiment = sentiment is not None and sentiment < -0.2
            
            # Check cross-platform divergence
            divergence = calculate_platform_divergence(ticker, window)
            has_early_signal = divergence and divergence.get("early_signal", False)
            
            # Validate trade
            warnings = []
            errors = []
            positives = []
            confidence = 0.5  # Start neutral
            
            # Check organic status (block news-driven spikes)
            if not is_organic:
                errors.append(f"❌ News-driven spike detected (not organic)")
                confidence -= 0.3
            
            # Check narrative velocity
            velocity = enriched.delta_mentions
            acceleration = enriched.acceleration
            
            if side == "long":
                # Long trade validation
                # Check sentiment alignment (long requires bullish or neutral)
                if is_bearish_sentiment:
                    errors.append(f"❌ Bearish sentiment detected: {sentiment:+.2f} (long requires bullish)")
                    confidence -= 0.25
                elif is_bullish_sentiment:
                    positives.append(f"✅ Bullish sentiment: {sentiment:+.2f}")
                    confidence += 0.15
                
                if velocity < -10:
                    errors.append(f"❌ Narrative fading: {velocity:+d} mentions")
                    confidence -= 0.3
                elif velocity < -5:
                    warnings.append(f"⚠️ Narrative weakening: {velocity:+d} mentions")
                    confidence -= 0.15
                elif velocity > 10:
                    positives.append(f"✅ Narrative strengthening: {velocity:+d} mentions")
                    confidence += 0.2
                
                if acceleration < -5:
                    errors.append(f"❌ Negative acceleration: {acceleration:+d}")
                    confidence -= 0.2
                elif acceleration > 5:
                    positives.append(f"✅ Positive acceleration: {acceleration:+d}")
                    confidence += 0.15
                
                # Use weighted mentions for confidence boost
                if weighted_mentions > enriched.total_mentions * 0.8:
                    positives.append(f"✅ High-quality accounts: weighted {weighted_mentions:.1f} vs raw {enriched.total_mentions}")
                    confidence += 0.1
                
                # Check early signal (divergence)
                if has_early_signal:
                    ratio = divergence.get("divergence_ratio", 1.0)
                    platform = divergence.get("leading_platform", "unknown")
                    positives.append(f"✅ Early signal: {platform} leading by {ratio:.1f}x")
                    confidence += 0.1
                
                # Check composite signal
                if signal:
                    if signal.composite_score < -0.3:
                        errors.append(f"❌ Bearish composite signal: {signal.composite_score:+.2f}")
                        confidence -= 0.25
                    elif signal.composite_score > 0.3:
                        positives.append(f"✅ Bullish composite signal: {signal.composite_score:+.2f}")
                        confidence += 0.2
                    
                    if signal.confidence < 0.5:
                        warnings.append(f"⚠️ Low signal confidence: {signal.confidence:.0%}")
                        confidence -= 0.1
            
            elif side == "short":
                # Short trade validation
                # Check sentiment alignment (short requires bearish or neutral)
                if is_bullish_sentiment:
                    errors.append(f"❌ Bullish sentiment detected: {sentiment:+.2f} (short requires bearish)")
                    confidence -= 0.25
                elif is_bearish_sentiment:
                    positives.append(f"✅ Bearish sentiment: {sentiment:+.2f}")
                    confidence += 0.15
                
                if velocity > 10:
                    errors.append(f"❌ Narrative spiking: {velocity:+d} mentions")
                    confidence -= 0.3
                elif velocity > 5:
                    warnings.append(f"⚠️ Narrative strengthening: {velocity:+d} mentions")
                    confidence -= 0.15
                elif velocity < -10:
                    positives.append(f"✅ Narrative weakening: {velocity:+d} mentions")
                    confidence += 0.2
                
                if acceleration > 5:
                    errors.append(f"❌ Positive acceleration: {acceleration:+d}")
                    confidence -= 0.2
                elif acceleration < -5:
                    positives.append(f"✅ Negative acceleration: {acceleration:+d}")
                    confidence += 0.15
                
                # Use weighted mentions for confidence boost
                if weighted_mentions > enriched.total_mentions * 0.8:
                    positives.append(f"✅ High-quality accounts: weighted {weighted_mentions:.1f} vs raw {enriched.total_mentions}")
                    confidence += 0.1
                
                # Check early signal (divergence)
                if has_early_signal:
                    ratio = divergence.get("divergence_ratio", 1.0)
                    platform = divergence.get("leading_platform", "unknown")
                    positives.append(f"✅ Early signal: {platform} leading by {ratio:.1f}x")
                    confidence += 0.1
                
                # Check composite signal
                if signal:
                    if signal.composite_score > 0.3:
                        errors.append(f"❌ Bullish composite signal: {signal.composite_score:+.2f}")
                        confidence -= 0.25
                    elif signal.composite_score < -0.3:
                        positives.append(f"✅ Bearish composite signal: {signal.composite_score:+.2f}")
                        confidence += 0.2
                    
                    if signal.confidence < 0.5:
                        warnings.append(f"⚠️ Low signal confidence: {signal.confidence:.0%}")
                        confidence -= 0.1
            
            # Check for anomalies (can be opportunity or warning)
            if anomaly:
                if side == "long" and anomaly['z_score'] < -2.0:
                    # Negative anomaly for long = warning
                    warnings.append(f"⚠️ Negative narrative anomaly: {anomaly['z_score']:+.1f}σ")
                    confidence -= 0.1
                elif side == "short" and anomaly['z_score'] > 2.0:
                    # Positive anomaly for short = warning
                    warnings.append(f"⚠️ Positive narrative anomaly: {anomaly['z_score']:+.1f}σ")
                    confidence -= 0.1
            
            # Determine validity
            confidence = max(0.0, min(1.0, confidence))
            
            if errors:
                valid = False
                reason = "BLOCKED: " + "; ".join(errors)
            elif len(warnings) >= 2:
                valid = False
                reason = "CAUTION: Multiple warnings - " + "; ".join(warnings)
            elif warnings:
                valid = True
                reason = "WARNINGS: " + "; ".join(warnings)
            else:
                valid = True
                reason = "CLEAR" if not positives else "; ".join(positives)
            
            return {
                'valid': valid,
                'reason': reason,
                'confidence': confidence,
                'warnings': warnings,
                'errors': errors,
                'positives': positives,
                'ticker': ticker,
                'side': side,
                'mentions': enriched.total_mentions,
                'weighted_mentions': weighted_mentions,
                'organic': is_organic,
                'sentiment': sentiment,
                'velocity': velocity,
                'acceleration': acceleration,
                'mindshare': enriched.mindshare_score,
                'composite_score': signal.composite_score if signal else 0,
                'signal_confidence': signal.confidence if signal else 0,
                'anomaly': anomaly,
                'divergence': divergence if has_early_signal else None,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            return {
                'valid': False,
                'reason': f"Error during check: {e}",
                'confidence': 0.0
            }
    
    def print_result(self, result: Dict):
        """Print validation result in readable format."""
        ticker = result['ticker']
        side = result['side']
        valid = result['valid']
        confidence = result['confidence']
        reason = result['reason']
        
        print(f"\n{'='*80}")
        print(f"PRE-TRADE CHECK: {ticker} {side.upper()}")
        print(f"{'='*80}\n")
        
        # Print verdict
        if valid:
            if confidence >= 0.7:
                verdict = "✅ APPROVED (High Confidence)"
            elif confidence >= 0.5:
                verdict = "✅ APPROVED (Moderate Confidence)"
            else:
                verdict = "⚠️ APPROVED (Low Confidence)"
        else:
            verdict = "❌ BLOCKED"
        
        print(f"Verdict: {verdict}")
        print(f"Confidence: {confidence:.0%}")
        print(f"Reason: {reason}\n")
        
        # Print details
        print("Narrative State:")
        print(f"  Mentions: {result['mentions']}")
        if result.get('weighted_mentions'):
            print(f"  Weighted Mentions: {result['weighted_mentions']:.1f}")
        if result.get('sentiment') is not None:
            sentiment_label = "Bullish" if result['sentiment'] > 0.2 else "Bearish" if result['sentiment'] < -0.2 else "Neutral"
            print(f"  Sentiment: {result['sentiment']:+.2f} ({sentiment_label})")
        if result.get('organic') is not None:
            organic_label = "✅ Organic" if result['organic'] else "⚠️ News-driven"
            print(f"  Status: {organic_label}")
        print(f"  Velocity: {result['velocity']:+d} mentions")
        print(f"  Acceleration: {result['acceleration']:+d}")
        if result['mindshare']:
            print(f"  Mindshare: {result['mindshare']:.2f}")
        if result.get('divergence'):
            div = result['divergence']
            print(f"  Early Signal: {div.get('leading_platform', 'unknown')} leading by {div.get('divergence_ratio', 1.0):.1f}x")
        
        if result['composite_score']:
            print(f"\nComposite Signal:")
            print(f"  Score: {result['composite_score']:+.2f}")
            print(f"  Confidence: {result['signal_confidence']:.0%}")
        
        if result['anomaly']:
            anomaly = result['anomaly']
            print(f"\nAnomaly Detection:")
            print(f"  Z-score: {anomaly['z_score']:+.1f}σ")
            print(f"  Severity: {anomaly['severity']}")
        
        # Print warnings/errors/positives
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  {error}")
        
        if result['warnings']:
            print(f"\n⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"  {warning}")
        
        if result['positives']:
            print(f"\n✅ Positives:")
            for positive in result['positives']:
                print(f"  {positive}")
        
        print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Validate trades before entry based on narrative state"
    )
    parser.add_argument(
        'ticker',
        type=str,
        help='Ticker symbol to check'
    )
    parser.add_argument(
        'side',
        type=str,
        choices=['long', 'short'],
        help='Trade side: long or short'
    )
    parser.add_argument(
        '--window',
        type=str,
        default='1h',
        help='Time window for analysis (default: 1h)'
    )
    
    args = parser.parse_args()
    
    # Check trade
    checker = PreTradeChecker()
    result = checker.check_trade(
        ticker=args.ticker.upper(),
        side=args.side.lower(),
        window=args.window
    )
    
    # Print result
    checker.print_result(result)
    
    # Exit code
    sys.exit(0 if result['valid'] else 1)


if __name__ == "__main__":
    main()
