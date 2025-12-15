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
from elfa_client import get_ticker_narrative_snapshot, calculate_weighted_mentions, is_organic_narrative_spike
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


def get_sentiment_indicator(sentiment: Optional[float]) -> str:
    """Get visual indicator for sentiment."""
    if sentiment is None:
        return "➡️"  # Neutral when unavailable
    if sentiment > 0.5:
        return "🚀"  # Very bullish
    elif sentiment > 0.2:
        return "📈"  # Bullish
    elif sentiment > -0.2:
        return "➡️"  # Neutral
    elif sentiment > -0.5:
        return "📉"  # Bearish
    else:
        return "💥"  # Very bearish


def display_cli_radar(enriched_snapshots: List[EnrichedSnapshot], window: str, weighted: bool = False, organic_only: bool = False):
    """Display radar view in CLI with rich formatting."""
    if not enriched_snapshots:
        print("No data available.")
        return
    
    # Filter organic-only if requested
    if organic_only:
        filtered_snapshots = []
        for snap in enriched_snapshots:
            analysis = is_organic_narrative_spike(snap.ticker, window, min_mentions=1)
            if analysis.get("is_organic", True):
                filtered_snapshots.append(snap)
        enriched_snapshots = filtered_snapshots
        if not enriched_snapshots:
            print("No organic narrative spikes found.")
            return
    
    print("\n" + "=" * 120)
    print(f"📡 NARRATIVE RADAR - {window.upper()} WINDOW")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if organic_only:
        print("🔍 Filter: Organic spikes only (news-driven excluded)")
    if weighted:
        print("⚖️  Sort: Weighted mentions (account-type weighted)")
    print("=" * 120)
    
    # Header with new columns
    header = f"{'Ticker':<8} {'Mentions':<10} {'Weighted':<10} {'Sentiment':<12} {'Velocity':<12} {'Accel':<8} {'Mindshare':<12} {'Churn':<30}"
    print(header)
    print("-" * 120)
    
    # Sort by weighted mentions if requested, otherwise by total mentions
    if weighted:
        sorted_snapshots = sorted(
            enriched_snapshots, 
            key=lambda x: x.weighted_mentions if x.weighted_mentions is not None else x.total_mentions, 
            reverse=True
        )
    else:
        sorted_snapshots = sorted(enriched_snapshots, key=lambda x: x.total_mentions, reverse=True)
    
    for snap in sorted_snapshots:
        velocity_str = f"{get_velocity_indicator(snap.delta_mentions)} {format_number(snap.delta_mentions)}"
        accel_str = f"{get_acceleration_indicator(snap.acceleration)} {format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}"
        mindshare_str = f"{snap.mindshare_score:.2f}" if snap.mindshare_score else "N/A"
        
        # Weighted mentions
        weighted_str = f"{snap.weighted_mentions:.1f}" if snap.weighted_mentions is not None else "N/A"
        
        # Sentiment indicator
        sentiment_indicator = get_sentiment_indicator(snap.sentiment_score)
        sentiment_str = f"{sentiment_indicator} {snap.sentiment_score:+.2f}" if snap.sentiment_score is not None else f"{sentiment_indicator} N/A"
        
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
            f"{weighted_str:<10} "
            f"{sentiment_str:<12} "
            f"{velocity_str:<12} "
            f"{accel_str:<8} "
            f"{mindshare_str:<12} "
            f"{churn_str:<30}"
        )
        print(row)
    
    print("-" * 120)
    print()
    
    # Detailed account churn section
    print("📊 ACCOUNT CHURN DETAILS")
    print("=" * 120)
    for snap in sorted_snapshots:
        if snap.new_accounts or snap.lost_accounts:
            print(f"\n{snap.ticker}:")
            if snap.new_accounts:
                print(f"  🟢 New accounts: {', '.join(snap.new_accounts)}")
            if snap.lost_accounts:
                print(f"  🔴 Lost accounts: {', '.join(snap.lost_accounts)}")
            if snap.top_smart_accounts:
                print(f"  📌 Current top accounts: {', '.join(snap.top_smart_accounts)}")
            # Show organic vs news breakdown
            if snap.organic_mentions > 0 or snap.news_mentions > 0:
                print(f"  📊 Mentions breakdown: {snap.organic_mentions} organic, {snap.news_mentions} news")
    
    print("\n" + "=" * 120)


def export_markdown(enriched_snapshots: List[EnrichedSnapshot], window: str, output_path: Path, weighted: bool = False, organic_only: bool = False):
    """Export radar data to markdown file."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Filter organic-only if requested
    if organic_only:
        filtered_snapshots = []
        for snap in enriched_snapshots:
            analysis = is_organic_narrative_spike(snap.ticker, window, min_mentions=1)
            if analysis.get("is_organic", True):
                filtered_snapshots.append(snap)
        enriched_snapshots = filtered_snapshots
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Narrative Radar - {window.upper()} Window\n\n")
        f.write(f"**Generated:** {timestamp}\n\n")
        if organic_only:
            f.write("**Filter:** Organic spikes only (news-driven excluded)\n\n")
        if weighted:
            f.write("**Sort:** Weighted mentions (account-type weighted)\n\n")
        f.write("---\n\n")
        
        # Summary table with new columns
        f.write("## Summary\n\n")
        f.write("| Ticker | Mentions | Weighted | Sentiment | Velocity | Acceleration | Mindshare | Account Churn |\n")
        f.write("|--------|----------|----------|-----------|----------|--------------|-----------|---------------|\n")
        
        # Sort by weighted mentions if requested, otherwise by total mentions
        if weighted:
            sorted_snapshots = sorted(
                enriched_snapshots, 
                key=lambda x: x.weighted_mentions if x.weighted_mentions is not None else x.total_mentions, 
                reverse=True
            )
        else:
            sorted_snapshots = sorted(enriched_snapshots, key=lambda x: x.total_mentions, reverse=True)
        
        for snap in sorted_snapshots:
            velocity_str = f"{format_number(snap.delta_mentions)}"
            accel_str = f"{format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}"
            mindshare_str = f"{snap.mindshare_score:.2f}" if snap.mindshare_score else "N/A"
            weighted_str = f"{snap.weighted_mentions:.1f}" if snap.weighted_mentions is not None else "N/A"
            sentiment_str = f"{snap.sentiment_score:+.2f}" if snap.sentiment_score is not None else "N/A"
            
            churn_parts = []
            if snap.new_accounts:
                churn_parts.append(f"+{len(snap.new_accounts)} new")
            if snap.lost_accounts:
                churn_parts.append(f"-{len(snap.lost_accounts)} lost")
            churn_str = ", ".join(churn_parts) if churn_parts else "stable"
            
            f.write(
                f"| {snap.ticker} | {snap.total_mentions} | {weighted_str} | {sentiment_str} | "
                f"{velocity_str} | {accel_str} | {mindshare_str} | {churn_str} |\n"
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

