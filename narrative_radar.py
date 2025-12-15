#!/usr/bin/env python3
"""
Next-Gen Narrative Radar - Track ticker narrative velocity, acceleration, and account churn.

This tool fetches narrative snapshots for multiple tickers, enriches them with historical
data to compute velocity and acceleration, and displays results in CLI or exports to markdown.
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher, EnrichedSnapshot

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


def format_number(num: int) -> str:
    """Format number with sign prefix."""
    sign = "+" if num > 0 else ""
    return f"{sign}{num}"


def format_percentage(value: float, total: int) -> str:
    """Format as percentage."""
    if total == 0:
        return "N/A"
    pct = (value / total) * 100
    return f"{pct:+.1f}%"


def get_velocity_indicator(delta: int) -> str:
    """Get visual indicator for velocity."""
    if delta > 10:
        return "🚀"
    elif delta > 5:
        return "📈"
    elif delta > 0:
        return "↗️"
    elif delta == 0:
        return "➡️"
    elif delta > -5:
        return "↘️"
    elif delta > -10:
        return "📉"
    else:
        return "💥"


def get_acceleration_indicator(accel: Optional[int]) -> str:
    """Get visual indicator for acceleration."""
    if accel is None:
        return "➡️"  # Neutral when insufficient data
    if accel > 5:
        return "⚡"
    elif accel > 0:
        return "🔺"
    elif accel == 0:
        return "➡️"
    elif accel > -5:
        return "🔻"
    else:
        return "⚡"


def display_cli_radar(enriched_snapshots: List[EnrichedSnapshot], window: str):
    """Display radar view in CLI with rich formatting."""
    if not enriched_snapshots:
        print("No data available.")
        return
    
    print("\n" + "=" * 100)
    print(f"📡 NARRATIVE RADAR - {window.upper()} WINDOW")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 100)
    
    # Header
    header = f"{'Ticker':<8} {'Mentions':<10} {'Velocity':<12} {'Accel':<8} {'Mindshare':<12} {'Churn':<30}"
    print(header)
    print("-" * 100)
    
    # Sort by total mentions (descending)
    sorted_snapshots = sorted(enriched_snapshots, key=lambda x: x.total_mentions, reverse=True)
    
    for snap in sorted_snapshots:
        velocity_str = f"{get_velocity_indicator(snap.delta_mentions)} {format_number(snap.delta_mentions)}"
        accel_str = f"{get_acceleration_indicator(snap.acceleration)} {format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}"
        mindshare_str = f"{snap.mindshare_score:.2f}" if snap.mindshare_score else "N/A"
        
        # Account churn summary
        churn_parts = []
        if snap.new_accounts:
            churn_parts.append(f"+{len(snap.new_accounts)} new")
        if snap.lost_accounts:
            churn_parts.append(f"-{len(snap.lost_accounts)} lost")
        churn_str = ", ".join(churn_parts) if churn_parts else "stable"
        
        row = (
            f"{snap.ticker:<8} "
            f"{snap.total_mentions:<10} "
            f"{velocity_str:<12} "
            f"{accel_str:<8} "
            f"{mindshare_str:<12} "
            f"{churn_str:<30}"
        )
        print(row)
    
    print("-" * 100)
    print()
    
    # Detailed account churn section
    print("📊 ACCOUNT CHURN DETAILS")
    print("=" * 100)
    for snap in sorted_snapshots:
        if snap.new_accounts or snap.lost_accounts:
            print(f"\n{snap.ticker}:")
            if snap.new_accounts:
                print(f"  🟢 New accounts: {', '.join(snap.new_accounts)}")
            if snap.lost_accounts:
                print(f"  🔴 Lost accounts: {', '.join(snap.lost_accounts)}")
            if snap.top_smart_accounts:
                print(f"  📌 Current top accounts: {', '.join(snap.top_smart_accounts)}")
    
    print("\n" + "=" * 100)


def export_markdown(enriched_snapshots: List[EnrichedSnapshot], window: str, output_path: Path):
    """Export radar data to markdown file."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Narrative Radar - {window.upper()} Window\n\n")
        f.write(f"**Generated:** {timestamp}\n\n")
        f.write("---\n\n")
        
        # Summary table
        f.write("## Summary\n\n")
        f.write("| Ticker | Mentions | Velocity | Acceleration | Mindshare | Account Churn |\n")
        f.write("|--------|----------|----------|--------------|-----------|---------------|\n")
        
        sorted_snapshots = sorted(enriched_snapshots, key=lambda x: x.total_mentions, reverse=True)
        
        for snap in sorted_snapshots:
            velocity_str = f"{format_number(snap.delta_mentions)}"
            accel_str = f"{format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}"
            mindshare_str = f"{snap.mindshare_score:.2f}" if snap.mindshare_score else "N/A"
            
            churn_parts = []
            if snap.new_accounts:
                churn_parts.append(f"+{len(snap.new_accounts)} new")
            if snap.lost_accounts:
                churn_parts.append(f"-{len(snap.lost_accounts)} lost")
            churn_str = ", ".join(churn_parts) if churn_parts else "stable"
            
            f.write(
                f"| {snap.ticker} | {snap.total_mentions} | {velocity_str} | {accel_str} | "
                f"{mindshare_str} | {churn_str} |\n"
            )
        
        f.write("\n---\n\n")
        
        # Detailed sections
        f.write("## Detailed Analysis\n\n")
        
        for snap in sorted_snapshots:
            f.write(f"### {snap.ticker}\n\n")
            f.write(f"- **Total Mentions:** {snap.total_mentions}\n")
            f.write(f"- **Velocity (Δ):** {format_number(snap.delta_mentions)}\n")
            f.write(f"- **Acceleration:** {format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}\n")
            if snap.mindshare_score:
                f.write(f"- **Mindshare Score:** {snap.mindshare_score:.2f}\n")
            
            f.write("\n#### Account Activity\n\n")
            if snap.new_accounts:
                f.write(f"**New Accounts ({len(snap.new_accounts)}):**\n")
                for account in snap.new_accounts:
                    f.write(f"- `{account}`\n")
                f.write("\n")
            
            if snap.lost_accounts:
                f.write(f"**Lost Accounts ({len(snap.lost_accounts)}):**\n")
                for account in snap.lost_accounts:
                    f.write(f"- `{account}`\n")
                f.write("\n")
            
            if snap.top_smart_accounts:
                f.write(f"**Current Top Accounts:**\n")
                for i, account in enumerate(snap.top_smart_accounts, 1):
                    f.write(f"{i}. `{account}`\n")
                f.write("\n")
            
            if snap.source_query:
                f.write(f"<details>\n<summary>Source Query (Audit Trail)</summary>\n\n")
                f.write(f"```\n{snap.source_query}\n```\n\n")
                f.write(f"</details>\n\n")
            
            f.write("---\n\n")
        
        # Footer
        f.write(f"*Report generated by Narrative Radar at {timestamp}*\n")
    
    print(f"✅ Markdown report exported to: {output_path}")


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Next-Gen Narrative Radar - Track ticker narrative metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Track multiple tickers with 1h window
  python narrative_radar.py BTC ETH SOL --window 1h

  # Export to markdown
  python narrative_radar.py BTC ETH --window 1h --export radar_report.md

  # Track single ticker
  python narrative_radar.py AAPL --window 24h
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='+',
        help='Ticker symbols to track (e.g., BTC ETH SOL AAPL)'
    )
    
    parser.add_argument(
        '--window',
        default='1h',
        help='Time window for aggregation (default: 1h)'
    )
    
    parser.add_argument(
        '--export',
        type=Path,
        help='Export results to markdown file (e.g., --export report.md)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching for fresh data'
    )
    
    args = parser.parse_args()
    
    # Check for API key upfront with clear error message
    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("❌ ERROR: ELFA_API_KEY environment variable is not set.", file=sys.stderr)
        print("\nTo fix this:", file=sys.stderr)
        print("  1. Get your API key from: https://docs.elfa.ai", file=sys.stderr)
        print("  2. Set it in your environment:", file=sys.stderr)
        print("     export ELFA_API_KEY='your_api_key_here'", file=sys.stderr)
        print("\n  Or create a .env file (see env.example)", file=sys.stderr)
        sys.exit(1)
    
    # Initialize enricher
    enricher = NarrativeEnricher()
    
    print(f"🔍 Fetching narrative data for {len(args.tickers)} ticker(s)...")
    print(f"⏱️  Window: {args.window}\n")
    
    enriched_snapshots = []
    failed_tickers = []
    
    for ticker in args.tickers:
        ticker_upper = ticker.upper()
        print(f"  Fetching {ticker_upper}...", end=" ", flush=True)
        
        snap = get_ticker_narrative_snapshot(
            ticker_upper,
            window=args.window,
            use_cache=not args.no_cache
        )
        
        if snap:
            enriched = enricher.enrich_snapshot(snap)
            enriched_snapshots.append(enriched)
            print("✅")
        else:
            failed_tickers.append(ticker_upper)
            print("❌")
    
    if failed_tickers:
        print(f"\n⚠️  Warning: Failed to fetch data for: {', '.join(failed_tickers)}")
    
    if not enriched_snapshots:
        print("\n❌ No data available. Exiting.")
        print("\n💡 Troubleshooting tips:", file=sys.stderr)
        print("  - Check the warning messages above for details", file=sys.stderr)
        print("  - Verify your API key is correct and has access", file=sys.stderr)
        print("  - Check your internet connection", file=sys.stderr)
        print("  - Try a different time window (e.g., --window 24h)", file=sys.stderr)
        print("  - Verify the ticker symbol is valid", file=sys.stderr)
        sys.exit(1)
    
    # Display CLI radar
    display_cli_radar(enriched_snapshots, args.window)
    
    # Export to markdown if requested
    if args.export:
        export_markdown(enriched_snapshots, args.window, args.export)
    
    # Exit with error if any failures
    if failed_tickers:
        sys.exit(1)


if __name__ == "__main__":
    main()

