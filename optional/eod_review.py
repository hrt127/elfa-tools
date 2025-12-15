#!/usr/bin/env python3
"""
eod_review.py - End-of-day review and analysis

Generates end-of-day review with:
1. Alert summary from position monitor
2. Momentum leaders (what worked today)
3. Daily digest for journal
4. Performance insights

Usage:
    python eod_review.py
    python eod_review.py --alerts alerts.log --journal ~/journal
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def read_alerts_log(log_path: Path) -> List[str]:
    """Read alerts from log file. Never raises exceptions."""
    try:
        if not log_path.exists():
            return []
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Get last 50 lines (or all if less)
        return lines[-50:] if len(lines) > 50 else lines
    
    except Exception as e:
        print(f"Warning: Failed to read alerts log: {e}")
        return []


def get_momentum_leaders(tickers: List[str], window: str = "24h") -> List[Dict]:
    """Get momentum leaders from delta store. Never raises exceptions."""
    try:
        from delta_store import DeltaStore
        
        store = DeltaStore()
        summary = store.get_watchlist_summary(tickers, window)
        
        # Sort by momentum score
        summary.sort(key=lambda x: x.get('momentum_score', 0), reverse=True)
        
        return summary
    
    except Exception as e:
        print(f"Warning: Failed to get momentum leaders: {e}")
        return []


def generate_digest(tickers: List[str], journal_file: Path):
    """Generate daily digest and append to journal. Never raises exceptions."""
    try:
        digest_cmd = [
            'python', 'narrative_digest.py',
            *tickers,
            '--window', '24h',
            '--format', 'obsidian'
        ]
        
        result = subprocess.run(digest_cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            # Append to journal file
            with open(journal_file, 'a') as f:
                f.write(f"\n## EOD Review - {datetime.now().strftime('%H:%M:%S')}\n\n")
                f.write(result.stdout)
                f.write("\n---\n\n")
            
            return True
        else:
            print(f"⚠️ Warning: Digest generation failed")
            return False
    
    except Exception as e:
        print(f"Warning: Failed to generate digest: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate end-of-day review and analysis"
    )
    parser.add_argument(
        '--alerts',
        type=str,
        default='alerts.log',
        help='Path to alerts log file (default: alerts.log)'
    )
    parser.add_argument(
        '--journal',
        type=str,
        help='Journal directory (default: current directory)'
    )
    parser.add_argument(
        '--watchlist',
        type=str,
        help='File containing ticker symbols for momentum analysis'
    )
    parser.add_argument(
        '--tickers',
        nargs='*',
        help='Ticker symbols for analysis (e.g., BTC ETH SOL)'
    )
    parser.add_argument(
        '--window',
        type=str,
        default='24h',
        help='Time window for analysis (default: 24h)'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"📊 END-OF-DAY REVIEW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # 1. Review Alerts
    alerts_path = Path(args.alerts)
    if alerts_path.exists():
        print(f"📋 Alert Summary ({alerts_path}):")
        print(f"{'='*80}\n")
        
        alerts = read_alerts_log(alerts_path)
        if alerts:
            # Count alert types
            trim_count = sum(1 for line in alerts if 'TRIM WARNING' in line)
            cover_count = sum(1 for line in alerts if 'COVER WARNING' in line)
            caution_count = sum(1 for line in alerts if 'CAUTION' in line)
            
            print(f"  ⚠️ Trim Warnings: {trim_count}")
            print(f"  ⚠️ Cover Warnings: {cover_count}")
            print(f"  📉 Cautions: {caution_count}")
            print(f"  Total Alerts: {len([l for l in alerts if any(x in l for x in ['WARNING', 'CAUTION'])])}\n")
            
            # Show recent alerts
            print("Recent Alerts:")
            for line in alerts[-10:]:
                if any(x in line for x in ['WARNING', 'CAUTION', 'ALERT']):
                    print(f"  {line.strip()}")
        else:
            print("  No alerts found.\n")
    else:
        print(f"⚠️ Alerts log not found: {alerts_path}\n")
    
    # 2. Momentum Leaders
    tickers = []
    if args.watchlist:
        try:
            with open(args.watchlist, 'r') as f:
                tickers = [line.strip().upper() for line in f if line.strip()]
        except Exception as e:
            print(f"Warning: Failed to read watchlist: {e}")
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    
    if tickers:
        print(f"📈 Momentum Leaders ({args.window}):")
        print(f"{'='*80}\n")
        
        leaders = get_momentum_leaders(tickers, args.window)
        if leaders:
            print(f"{'Ticker':<8} {'Mentions':<10} {'Mindshare':<10} {'Momentum':<10}")
            print(f"{'-'*40}")
            for item in leaders[:10]:  # Top 10
                momentum = item.get('momentum_score', 0)
                mentions = item.get('mentions', 0)
                mindshare = item.get('mindshare', 0) or 0
                print(f"{item['ticker']:<8} {mentions:<10} {mindshare:<10.2f} {momentum:<10.0f}")
        else:
            print("  No momentum data available.\n")
        print()
    
    # 3. Generate Daily Digest
    if tickers:
        # Determine journal path
        if args.journal:
            journal_dir = Path(args.journal)
            journal_dir.mkdir(parents=True, exist_ok=True)
            journal_file = journal_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        else:
            journal_file = Path(f"journal_{datetime.now().strftime('%Y-%m-%d')}.md")
        
        print(f"📝 Generating Daily Digest...")
        if generate_digest(tickers, journal_file):
            print(f"✅ Journal entry saved to: {journal_file}\n")
        else:
            print(f"⚠️ Failed to generate digest\n")
    
    # 4. Summary
    print(f"{'='*80}")
    print(f"✅ EOD REVIEW COMPLETE")
    print(f"{'='*80}\n")
    print(f"Review completed at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\nNext steps:")
    print(f"  1. Review alerts to see what worked/failed")
    print(f"  2. Check momentum leaders for tomorrow's watchlist")
    print(f"  3. Update positions.json for tomorrow's monitoring")
    print(f"  4. Review journal entry for insights\n")


if __name__ == "__main__":
    main()
