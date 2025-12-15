"""
signal_composer.py - Multi-source signal fusion

Combines narrative (Elfa) + market data (perps, funding) + on-chain
to generate composite trading signals with confidence scores.

Integrates with:
- elfa_client.TickerNarrativeSnapshot
- narrative_enricher.EnrichedSnapshot
- perp_client (for funding rates)
- onchain_client (for on-chain metrics)
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Union
from datetime import datetime
from enum import Enum

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing data structures
from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot

class SignalStrength(Enum):
    """Signal confidence levels."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"
    CONFLICTED = "conflicted"

@dataclass
class CompositeSignal:
    """Fused signal from multiple data sources."""
    ticker: str
    timestamp: datetime
    
    # Individual component signals
    narrative_score: float  # -1 to 1
    market_score: float     # -1 to 1
    onchain_score: float    # -1 to 1
    
    # Composite output
    composite_score: float  # -1 to 1
    signal_strength: SignalStrength
    confidence: float       # 0 to 1
    
    # Supporting evidence
    evidence: Dict
    warnings: List[str]
    
    def explain(self) -> str:
        """Human-readable explanation."""
        emoji_map = {
            SignalStrength.STRONG_BULLISH: "🚀",
            SignalStrength.BULLISH: "📈",
            SignalStrength.NEUTRAL: "➡️",
            SignalStrength.BEARISH: "📉",
            SignalStrength.STRONG_BEARISH: "💥",
            SignalStrength.CONFLICTED: "⚠️"
        }
        
        lines = [
            f"{emoji_map[self.signal_strength]} {self.ticker} Composite Signal",
            f"",
            f"Overall: {self.composite_score:+.2f} ({self.confidence:.0%} confidence)",
            f"",
            f"Components:",
            f"• Narrative: {self.narrative_score:+.2f}",
            f"• Market: {self.market_score:+.2f}",
            f"• On-chain: {self.onchain_score:+.2f}",
        ]
        
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"⚠️ {warning}")
        
        lines.append("")
        lines.append("Evidence:")
        for key, value in self.evidence.items():
            lines.append(f"• {key}: {value}")
        
        return "\n".join(lines)


class SignalComposer:
    """Fuses multiple data sources into actionable signals."""
    
    def __init__(
        self,
        narrative_weight: float = 0.4,
        market_weight: float = 0.35,
        onchain_weight: float = 0.25
    ):
        """
        Initialize with custom weights for each signal type.
        
        Weights should sum to 1.0.
        """
        total = narrative_weight + market_weight + onchain_weight
        self.narrative_weight = narrative_weight / total
        self.market_weight = market_weight / total
        self.onchain_weight = onchain_weight / total
    
    def compose(
        self,
        ticker: str,
        narrative_data: Optional[Union[Dict, TickerNarrativeSnapshot, EnrichedSnapshot]] = None,
        market_data: Optional[Dict] = None,
        onchain_data: Optional[Dict] = None
    ) -> CompositeSignal:
        """
        Generate composite signal from available data sources.
        
        Args:
            ticker: Ticker symbol
            narrative_data: Can be:
                - Dict with narrative metrics
                - TickerNarrativeSnapshot
                - EnrichedSnapshot
            market_data: Dict with market metrics (funding_rate, price_change_24h, volume_ratio)
            onchain_data: Dict with on-chain metrics (exchange_netflow_btc, whale_balance_change, etc.)
        
        Returns:
            CompositeSignal with fused signal and confidence score
        """
        # Normalize narrative data to dict format
        narrative_dict = self._normalize_narrative_data(narrative_data)
        
        # Calculate individual scores
        narrative_score = self._score_narrative(narrative_dict) if narrative_dict else 0
        market_score = self._score_market(market_data) if market_data else 0
        onchain_score = self._score_onchain(onchain_data) if onchain_data else 0
        
        # Normalize weights based on available data sources
        available_weights = []
        if narrative_dict:
            available_weights.append(('narrative', self.narrative_weight))
        if market_data:
            available_weights.append(('market', self.market_weight))
        if onchain_data:
            available_weights.append(('onchain', self.onchain_weight))
        
        # If no data available, return neutral signal
        if not available_weights:
            total_weight = 0
        else:
            total_weight = sum(w for _, w in available_weights)
        
        # Calculate composite with normalized weights
        if total_weight > 0:
            composite_score = sum(
                (narrative_score if name == 'narrative' else 
                 market_score if name == 'market' else 
                 onchain_score) * (weight / total_weight)
                for name, weight in available_weights
            )
        else:
            composite_score = 0.0
        
        # Determine signal strength
        signal_strength = self._classify_signal(composite_score, {
            'narrative': narrative_score,
            'market': market_score,
            'onchain': onchain_score
        })
        
        # Calculate confidence based on agreement
        confidence = self._calculate_confidence([
            narrative_score, market_score, onchain_score
        ])
        
        # Collect evidence
        evidence = {}
        if narrative_dict:
            evidence.update(self._extract_narrative_evidence(narrative_dict))
        if market_data:
            evidence.update(self._extract_market_evidence(market_data))
        if onchain_data:
            evidence.update(self._extract_onchain_evidence(onchain_data))
        
        # Generate warnings
        warnings = self._generate_warnings(
            narrative_score, market_score, onchain_score,
            narrative_dict, market_data, onchain_data
        )
        
        return CompositeSignal(
            ticker=ticker,
            timestamp=datetime.now(),
            narrative_score=narrative_score,
            market_score=market_score,
            onchain_score=onchain_score,
            composite_score=composite_score,
            signal_strength=signal_strength,
            confidence=confidence,
            evidence=evidence,
            warnings=warnings
        )
    
    def _normalize_narrative_data(
        self, 
        data: Optional[Union[Dict, TickerNarrativeSnapshot, EnrichedSnapshot]]
    ) -> Optional[Dict]:
        """
        Normalize narrative data from various formats to a common dict.
        
        Returns None if data is None or invalid.
        """
        if data is None:
            return None
        
        if isinstance(data, (TickerNarrativeSnapshot, EnrichedSnapshot)):
            # Convert snapshot to dict format
            return {
                'mentions': data.total_mentions,
                'mindshare': data.mindshare_score,
                'smart_accounts': data.top_smart_accounts,
                'mentions_velocity': getattr(data, 'delta_mentions', 0) if isinstance(data, EnrichedSnapshot) else 0,
                'acceleration': getattr(data, 'acceleration', None) if isinstance(data, EnrichedSnapshot) else None
            }
        elif isinstance(data, dict):
            return data
        else:
            print(f"Warning: Unsupported narrative data type: {type(data)}")
            return None
    
    def _score_narrative(self, data: Dict) -> float:
        """
        Score narrative strength from -1 (bearish) to 1 (bullish).
        
        Considers: mentions, mindshare, velocity, smart accounts
        
        Never raises exceptions.
        """
        try:
            score = 0.0
            
            # Mindshare component (0 to 0.4)
            mindshare = data.get('mindshare', 0) or 0
            if mindshare:
                score += min(mindshare * 4, 0.4)  # Cap at 0.4
            
            # Mentions velocity component (-0.3 to 0.3)
            velocity = data.get('mentions_velocity', 0) or 0
            if velocity:
                # Normalize velocity (assumes typical range of -50 to +50)
                score += max(min(velocity / 20, 0.3), -0.3)
            
            # Smart accounts component (0 to 0.3)
            smart_accounts = data.get('smart_accounts', [])
            if smart_accounts:
                smart_count = len(smart_accounts) if isinstance(smart_accounts, list) else 0
                score += min(smart_count * 0.1, 0.3)
            
            return max(min(score, 1.0), -1.0)
        except Exception as e:
            print(f"Warning: Failed to score narrative: {e}")
            return 0.0
    
    def _score_market(self, data: Dict) -> float:
        """
        Score market conditions from -1 (bearish) to 1 (bullish).
        
        Considers: funding rate, price action, volume
        """
        score = 0.0
        
        # Funding rate component (-0.4 to 0.4)
        funding = data.get('funding_rate', 0)
        if funding:
            # Extreme positive funding = bearish (over-leveraged longs)
            # Extreme negative funding = bullish (over-leveraged shorts)
            score -= max(min(funding * 100, 0.4), -0.4)
        
        # Price momentum component (-0.3 to 0.3)
        price_change = data.get('price_change_24h', 0)
        if price_change:
            score += max(min(price_change / 10, 0.3), -0.3)
        
        # Volume component (0 to 0.3)
        vol_ratio = data.get('volume_ratio', 1.0)  # vs 7d avg
        if vol_ratio > 1.5:
            score += 0.3
        elif vol_ratio > 1.2:
            score += 0.15
        
        return max(min(score, 1.0), -1.0)
    
    def _score_onchain(self, data: Dict) -> float:
        """
        Score on-chain activity from -1 (bearish) to 1 (bullish).
        
        Considers: whale flows, exchange flows, active addresses
        """
        score = 0.0
        
        # Exchange net flow component (-0.4 to 0.4)
        # Negative (outflow) = bullish, Positive (inflow) = bearish
        net_flow = data.get('exchange_netflow_btc', 0)
        if net_flow:
            score -= max(min(net_flow / 10000, 0.4), -0.4)
        
        # Whale accumulation component (-0.3 to 0.3)
        whale_delta = data.get('whale_balance_change', 0)
        if whale_delta > 0:
            score += 0.3
        elif whale_delta < 0:
            score -= 0.3
        
        # Active addresses component (0 to 0.3)
        active_ratio = data.get('active_addresses_ratio', 1.0)
        if active_ratio > 1.2:
            score += 0.3
        elif active_ratio > 1.0:
            score += 0.15
        
        return max(min(score, 1.0), -1.0)
    
    def _classify_signal(self, composite: float, components: Dict) -> SignalStrength:
        """Classify signal strength based on composite score."""
        # Check for conflicted signals (components disagree)
        scores = list(components.values())
        if max(scores) > 0.3 and min(scores) < -0.3:
            return SignalStrength.CONFLICTED
        
        # Clear signals
        if composite >= 0.6:
            return SignalStrength.STRONG_BULLISH
        elif composite >= 0.2:
            return SignalStrength.BULLISH
        elif composite <= -0.6:
            return SignalStrength.STRONG_BEARISH
        elif composite <= -0.2:
            return SignalStrength.BEARISH
        else:
            return SignalStrength.NEUTRAL
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """
        Calculate confidence based on score agreement.
        
        High confidence = all scores agree in direction and magnitude.
        Low confidence = scores conflict or are weak.
        """
        non_zero = [s for s in scores if s != 0]
        if not non_zero:
            return 0.0
        
        # Check directional agreement
        all_positive = all(s > 0 for s in non_zero)
        all_negative = all(s < 0 for s in non_zero)
        
        if not (all_positive or all_negative):
            # Mixed signals = low confidence
            return 0.3
        
        # Calculate agreement strength
        avg_magnitude = sum(abs(s) for s in non_zero) / len(non_zero)
        std_dev = (sum((abs(s) - avg_magnitude) ** 2 for s in non_zero) / len(non_zero)) ** 0.5
        
        # Low std dev + high magnitude = high confidence
        confidence = avg_magnitude * (1 - min(std_dev, 0.5))
        return max(min(confidence, 1.0), 0.0)
    
    def _extract_narrative_evidence(self, data: Dict) -> Dict:
        """Extract key narrative metrics for evidence. Never raises exceptions."""
        try:
            smart_accounts = data.get('smart_accounts', [])
            smart_count = len(smart_accounts) if isinstance(smart_accounts, list) else 0
            
            return {
                'Mentions': data.get('mentions', 0),
                'Mindshare': f"{data.get('mindshare', 0):.2f}" if data.get('mindshare') else 'N/A',
                'Smart accounts': smart_count,
                'Velocity': data.get('mentions_velocity', 0) or 0
            }
        except Exception as e:
            print(f"Warning: Failed to extract narrative evidence: {e}")
            return {}
    
    def _extract_market_evidence(self, data: Dict) -> Dict:
        """Extract key market metrics for evidence."""
        evidence = {}
        if 'funding_rate' in data:
            evidence['Funding rate'] = f"{data['funding_rate']*100:.3f}%"
        if 'price_change_24h' in data:
            evidence['Price Δ 24h'] = f"{data['price_change_24h']:+.1f}%"
        if 'volume_ratio' in data:
            evidence['Volume ratio'] = f"{data['volume_ratio']:.2f}x"
        return evidence
    
    def _extract_onchain_evidence(self, data: Dict) -> Dict:
        """Extract key on-chain metrics for evidence."""
        evidence = {}
        if 'exchange_netflow_btc' in data:
            flow = data['exchange_netflow_btc']
            evidence['Exchange flow'] = f"{flow:+.0f} BTC"
        if 'whale_balance_change' in data:
            evidence['Whale activity'] = 'Accumulating' if data['whale_balance_change'] > 0 else 'Distributing'
        return evidence
    
    def _generate_warnings(
        self,
        narrative_score: float,
        market_score: float,
        onchain_score: float,
        narrative_data: Optional[Dict],
        market_data: Optional[Dict],
        onchain_data: Optional[Dict]
    ) -> List[str]:
        """Generate warnings for conflicting signals or extreme conditions."""
        warnings = []
        
        # Conflicting signals
        if narrative_score > 0.3 and market_score < -0.3:
            warnings.append("Narrative bullish but market bearish")
        if onchain_score > 0.3 and market_score < -0.3:
            warnings.append("On-chain bullish but price weak")
        
        # Extreme conditions
        if market_data:
            funding = market_data.get('funding_rate', 0)
            if funding and abs(funding) > 0.01:  # >1% daily
                warnings.append(f"Extreme funding: {funding*100:.2f}%")
        
        if narrative_data:
            z_score = narrative_data.get('z_score', 0)
            if z_score and abs(z_score) >= 2.5:
                warnings.append(f"Narrative anomaly: {z_score:+.1f}σ")
        
        return warnings


# Usage example
if __name__ == "__main__":
    composer = SignalComposer()
    
    # Example: BTC with strong narrative, mixed market
    signal = composer.compose(
        ticker="BTC",
        narrative_data={
            'mentions': 85,
            'mindshare': 0.15,
            'mentions_velocity': 12.5,
            'smart_accounts': ['whale1', 'whale2', 'whale3']
        },
        market_data={
            'funding_rate': 0.008,  # Slightly elevated
            'price_change_24h': -2.3,
            'volume_ratio': 1.4
        },
        onchain_data={
            'exchange_netflow_btc': -1500,  # Outflow (bullish)
            'whale_balance_change': 1,  # Accumulating
            'active_addresses_ratio': 1.15
        }
    )
    
    print(signal.explain())