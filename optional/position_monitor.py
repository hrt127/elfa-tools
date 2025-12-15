#!/usr/bin/env python3
"""
position_monitor.py - Monitor open positions for narrative changes

Continuously monitors your positions and alerts when narrative moves against you.
Prevents holding losers too long by warning when:
- Long position + fading narrative = trim warning
- Short position + spiking narrative = cover warning

Usage:
    # Edit positions in this file, then run:
    python position_monitor.py 300  # Check every 300 seconds (5 min)
    
    # Or run in background:
    nohup python position_monitor.py 300 > alerts.log &
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher
from alerts_engine import AlertsEngine, AlertRule
from delta_store import DeltaStore


# ============================================================================
# EDIT YOUR POSITIONS HERE
# ============================================================================
POSITIONS = {
    # Format: "TICKER": {"side": "long" | "short", "size": float, "entry_price": float}
    # Example:
    # "BTC": {"side": "long", "size": 1.0, "entry_price": 45000},
    # "ETH": {"side": "short", "size": 10.0, "entry_price": 2800},
}


def load_positions() -> Dict:
    """Load positions from file or use default."""
    positions_file = Path("positions.json")
    if positions_file.exists():
        try:
            with open(positions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load positions.json: {e}")
            return POSITIONS
    return POSITIONS


def save_positions(positions: Dict):
    """Save positions to file."""
    try:
        with open("positions.json", 'w') as f:
            json.dump(positions, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save positions: {e}")


def check_position_narrative(
    ticker: str,
    side: str,
    enricher: NarrativeEnricher,
    store: DeltaStore
) -> Optional[Dict]:
    """
    Check narrative state for a position.
    
    Returns dict with narrative status and warning if needed.
    Never raises exceptions.
    """
    try:
        # Get current narrative snapshot
        snapshot = get_ticker_narrative_snapshot(ticker, window="1h", use_cache=False)
        if not snapshot:
            return None
        
        # Enrich with velocity/acceleration
        enriched = enricher.enrich_snapshot(snapshot)
        
        # Store for historical analysis
        store.insert(enriched)
        
        # Get historical context
        velocity_data = store.calculate_velocity(ticker, window="1h")
        anomaly = store.detect_anomalies(ticker, window="1h", std_threshold=2.0)
        
        # Determine narrative direction
        # Positive velocity = narrative strengthening
        # Negative velocity = narrative weakening
        narrative_velocity = enriched.delta_mentions if enriched else 0
        narrative_acceleration = enriched.acceleration if enriched else 0
        
        # Check if narrative is moving against position
        warning = None
        severity = "info"
        
        if side == "long":
            # Long position: worry if narrative is fading
            if narrative_velocity < -10 and narrative_acceleration < -5:
                warning = "⚠️ TRIM WARNING: Narrative fading rapidly"
                severity = "high"
            elif narrative_velocity < -5:
                warning = "📉 CAUTION: Narrative weakening"
                severity = "medium"
            elif narrative_velocity > 10 and narrative_acceleration > 5:
                # Good: narrative strengthening
                pass
        elif side == "short":
            # Short position: worry if narrative is spiking
            if narrative_velocity > 10 and narrative_acceleration > 5:
                warning = "⚠️ COVER WARNING: Narrative spiking rapidly"
                severity = "high"
            elif narrative_velocity > 5:
                warning = "📈 CAUTION: Narrative strengthening"
                severity = "medium"
            elif narrative_velocity < -10 and narrative_acceleration < -5:
                # Good: narrative weakening
                pass
        
        return {
            'ticker': ticker,
            'side': side,
            'mentions': enriched.total_mentions,
            'velocity': narrative_velocity,
            'acceleration': narrative_acceleration,
            'mindshare': enriched.mindshare_score,
            'warning': warning,
            'severity': severity,
            'anomaly': anomaly,
            'timestamp': datetime.now()
        }
    
    except Exception as e:
        print(f"Warning: Failed to check {ticker}: {e}")
        return None


def monitor_loop(interval_seconds: int = 300):
    """
    Main monitoring loop.
    
    Args:
        interval_seconds: How often to check positions (default: 300 = 5 min)
    """
    print(f"🚀 Position Monitor Started")
    print(f"Checking positions every {interval_seconds} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    enricher = NarrativeEnricher()
    store = DeltaStore()
    engine = AlertsEngine()
    
    # Add console channel
    def console_alert(message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    engine.add_channel(console_alert)
    
    try:
        while True:
            positions = load_positions()
            
            if not positions:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No positions to monitor")
                time.sleep(interval_seconds)
                continue
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking {len(positions)} positions...")
            
            for ticker, position_info in positions.items():
                side = position_info.get("side", "long")
                size = position_info.get("size", 0)
                
                if size == 0:
                    continue  # Skip zero-size positions
                
                result = check_position_narrative(ticker, side, enricher, store)
                
                if result:
                    # Print status
                    status_emoji = "✅" if not result['warning'] else "⚠️"
                    print(f"{status_emoji} {ticker} ({side}): "
                          f"{result['mentions']} mentions, "
                          f"velocity: {result['velocity']:+d}, "
                          f"accel: {result['acceleration']:+d}")
                    
                    # Alert if warning
                    if result['warning']:
                        message = f"{result['warning']}\n" \
                                 f"  {ticker} ({side}): " \
                                 f"Velocity {result['velocity']:+d}, " \
                                 f"Accel {result['acceleration']:+d}, " \
                                 f"Mentions {result['mentions']}"
                        
                        # Fire alert
                        engine._fire_alert("position_warning", ticker, message)
                        
                        # Print anomaly if detected
                        if result['anomaly']:
                            anomaly = result['anomaly']
                            print(f"  🚨 Anomaly: {anomaly['z_score']:+.1f}σ "
                                  f"({anomaly['severity']})")
            
            # Sleep until next check
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n👋 Position Monitor Stopped")
    except Exception as e:
        print(f"\n❌ Error in monitor loop: {e}")
        print("Restarting in 60 seconds...")
        time.sleep(60)
        monitor_loop(interval_seconds)  # Restart


if __name__ == "__main__":
    # Get interval from command line or use default
    interval = 300  # 5 minutes default
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Invalid interval '{sys.argv[1]}', using default 300 seconds")
    
    # Check if positions file exists, if not create from template
    positions_file = Path("positions.json")
    if not positions_file.exists():
        print("📝 Creating positions.json template...")
        print("   Edit positions.json with your actual positions")
        save_positions(POSITIONS)
        print(f"   Current template: {json.dumps(POSITIONS, indent=2)}")
        print("\n   To add positions, edit positions.json with format:")
        print('   {"BTC": {"side": "long", "size": 1.0, "entry_price": 45000}}')
        print("\n   Then run this script again.\n")
        sys.exit(0)
    
    # Start monitoring
    monitor_loop(interval)
