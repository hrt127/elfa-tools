#!/usr/bin/env python3
"""
morning_routine.py - Automated morning scan routine

Runs the complete morning scan workflow:
1. Scan watchlist for narrative activity
2. Find high-conviction entry setups
3. Generate journal entry

Usage:
    python morning_routine.py BTC ETH SOL HYPE PENGU
    python morning_routine.py --watchlist watchlist.txt
    python morning_routine.py --watchlist watchlist.txt --journal ~/journal
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List


def run_command(cmd: List[str], description: str) -> bool:
    """
    Run a command and handle errors gracefully.
    
    Returns True if successful, False otherwise.
    Never raises exceptions.
    """
    try:
        print(f"\n{'='*80}")
        print(f"📊 {description}")
        print(f"{'='*80}\n")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"⚠️ Warning: {description} returned non-zero exit code")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"⚠️ Warning: Failed to run {description}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run complete morning scan routine"
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
        '--journal',
        type=str,
        help='Journal directory (default: current directory)'
    )
    parser.add_argument(
        '--skip-radar',
        action='store_true',
        help='Skip narrative radar scan'
    )
    parser.add_argument(
        '--skip-scanner',
        action='store_true',
        help='Skip entry scanner'
    )
    parser.add_argument(
        '--skip-digest',
        action='store_true',
        help='Skip digest generation'
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
    
    ticker_str = ' '.join(tickers)
    
    print(f"\n{'='*80}")
    print(f"🌅 MORNING ROUTINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"Scanning: {ticker_str}")
    print(f"Window: {args.window}\n")
    
    # 1. Narrative Radar Scan
    if not args.skip_radar:
        radar_cmd = [
            'python', 'narrative_radar.py',
            *tickers,
            '--window', args.window,
            '--export', 'morning_scan.md'
        ]
        run_command(radar_cmd, "Narrative Radar Scan")
    
    # 2. Entry Scanner
    if not args.skip_scanner:
        scanner_cmd = [
            'python', 'entry_scanner.py',
            *tickers,
            '--window', args.window
        ]
        run_command(scanner_cmd, "Entry Scanner")
    
    # 3. Generate Digest
    if not args.skip_digest:
        # Determine journal path
        if args.journal:
            journal_dir = Path(args.journal)
            journal_dir.mkdir(parents=True, exist_ok=True)
            journal_file = journal_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        else:
            journal_file = Path(f"journal_{datetime.now().strftime('%Y-%m-%d')}.md")
        
        digest_cmd = [
            'python', 'narrative_digest.py',
            *tickers,
            '--window', '24h',
            '--format', 'obsidian'
        ]
        
        try:
            result = subprocess.run(digest_cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                # Append to journal file
                with open(journal_file, 'a') as f:
                    f.write(f"\n## Morning Scan - {datetime.now().strftime('%H:%M:%S')}\n\n")
                    f.write(result.stdout)
                    f.write("\n---\n\n")
                
                print(f"\n✅ Journal entry saved to: {journal_file}")
            else:
                print(f"⚠️ Warning: Digest generation returned non-zero exit code")
        
        except Exception as e:
            print(f"⚠️ Warning: Failed to generate digest: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"✅ MORNING ROUTINE COMPLETE")
    print(f"{'='*80}\n")
    print(f"Next steps:")
    print(f"  1. Review morning_scan.md for narrative activity")
    print(f"  2. Check entry scanner results for high-conviction setups")
    print(f"  3. Review journal entry: {journal_file if not args.skip_digest else 'N/A'}")
    print(f"  4. Run: python pre_trade_check.py TICKER long/short before each trade")
    print(f"  5. Start position monitor: python position_monitor.py 300 &\n")


if __name__ == "__main__":
    main()
