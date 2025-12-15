#!/usr/bin/env python3
"""
Daily Narrative Digest Writer - Generate comprehensive reports for multiple platforms.

Generates daily digests in various formats:
- Obsidian (markdown with tags and links)
- Telegram (formatted text)
- Discord (markdown with embeds)
- Email (HTML and plain text)
- Blog (markdown for publishing)
- JSON (structured data)
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher, EnrichedSnapshot


@dataclass
class DigestInsights:
    """Key insights extracted from the data."""
    top_movers: List[Tuple[str, int]]  # (ticker, velocity)
    fastest_accelerating: List[Tuple[str, int]]  # (ticker, acceleration)
    highest_mindshare: List[Tuple[str, float]]  # (ticker, score)
    most_mentioned: List[Tuple[str, int]]  # (ticker, mentions)
    top_weighted_movers: List[Tuple[str, float]]  # (ticker, weighted_mentions)
    sentiment_leaders: List[Tuple[str, float]]  # (ticker, sentiment_score) - most bullish/bearish
    organic_spikes: List[Tuple[str, int, int]]  # (ticker, organic_mentions, total_mentions)
    account_churn_leaders: List[Tuple[str, int]]  # (ticker, net_accounts)
    trending_accounts: List[str]  # Accounts appearing in multiple tickers
    total_mentions: int
    unique_accounts: int
    avg_mindshare: float


def analyze_snapshots(snapshots: List[EnrichedSnapshot]) -> DigestInsights:
    """Extract insights from enriched snapshots."""
    if not snapshots:
        return DigestInsights([], [], [], [], [], [], [], [], [], 0, 0, 0.0)
    
    # Sort by various metrics
    top_movers = sorted(
        [(s.ticker, s.delta_mentions) for s in snapshots],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    fastest_accelerating = sorted(
        [(s.ticker, s.acceleration) for s in snapshots if s.acceleration is not None],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    highest_mindshare = sorted(
        [(s.ticker, s.mindshare_score or 0.0) for s in snapshots if s.mindshare_score],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    most_mentioned = sorted(
        [(s.ticker, s.total_mentions) for s in snapshots],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Top weighted movers (account-type weighted)
    top_weighted_movers = sorted(
        [(s.ticker, s.weighted_mentions or s.total_mentions) for s in snapshots if s.weighted_mentions is not None],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Sentiment leaders (most bullish and bearish)
    sentiment_leaders = sorted(
        [(s.ticker, s.sentiment_score) for s in snapshots if s.sentiment_score is not None],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Organic spikes (high organic mentions)
    organic_spikes = sorted(
        [(s.ticker, s.organic_mentions, s.total_mentions) for s in snapshots if s.organic_mentions > 0],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Account churn (new - lost)
    account_churn = [
        (s.ticker, len(s.new_accounts) - len(s.lost_accounts))
        for s in snapshots
    ]
    account_churn_leaders = sorted(account_churn, key=lambda x: x[1], reverse=True)[:5]
    
    # Trending accounts (appear in multiple tickers)
    account_counts = defaultdict(int)
    for snap in snapshots:
        for account in snap.top_smart_accounts:
            account_counts[account] += 1
    
    trending_accounts = [
        account for account, count in sorted(account_counts.items(), key=lambda x: x[1], reverse=True)
        if count >= 2
    ][:10]
    
    # Aggregates
    total_mentions = sum(s.total_mentions for s in snapshots)
    all_accounts = set()
    for snap in snapshots:
        all_accounts.update(snap.top_smart_accounts)
    unique_accounts = len(all_accounts)
    
    mindshare_scores = [s.mindshare_score for s in snapshots if s.mindshare_score]
    avg_mindshare = sum(mindshare_scores) / len(mindshare_scores) if mindshare_scores else 0.0
    
    return DigestInsights(
        top_movers=top_movers,
        fastest_accelerating=fastest_accelerating,
        highest_mindshare=highest_mindshare,
        most_mentioned=most_mentioned,
        top_weighted_movers=top_weighted_movers,
        sentiment_leaders=sentiment_leaders,
        organic_spikes=organic_spikes,
        account_churn_leaders=account_churn_leaders,
        trending_accounts=trending_accounts,
        total_mentions=total_mentions,
        unique_accounts=unique_accounts,
        avg_mindshare=avg_mindshare
    )


def format_number(num: int) -> str:
    """Format number with sign."""
    sign = "+" if num > 0 else ""
    return f"{sign}{num}"


def generate_obsidian_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> str:
    """Generate Obsidian-formatted markdown."""
    date_str = date.strftime('%Y-%m-%d')
    title = f"Narrative Digest - {date_str}"
    
    content = f"""---
title: {title}
date: {date_str}
tags: [narrative, digest, daily, crypto, markets]
type: digest
---

# {title}

## 📊 Executive Summary

- **Total Mentions:** {insights.total_mentions:,}
- **Unique Accounts:** {insights.unique_accounts}
- **Average Mindshare:** {insights.avg_mindshare:.2f}

## 🚀 Top Movers (Velocity)

"""
    
    for ticker, velocity in insights.top_movers:
        content += f"- **[[{ticker}]]**: {format_number(velocity)} mentions\n"
    
    content += "\n## ⚡ Fastest Accelerating\n\n"
    for ticker, accel in insights.fastest_accelerating:
        content += f"- **[[{ticker}]]**: {format_number(accel)} acceleration\n"
    
    content += "\n## 💎 Highest Mindshare\n\n"
    for ticker, score in insights.highest_mindshare:
        content += f"- **[[{ticker}]]**: {score:.2f}\n"
    
    content += "\n## 📈 Most Mentioned\n\n"
    for ticker, mentions in insights.most_mentioned:
        content += f"- **[[{ticker}]]**: {mentions:,} mentions\n"
    
    if insights.top_weighted_movers:
        content += "\n## ⚖️ Top Weighted Movers (Account-Type Weighted)\n\n"
        for ticker, weighted in insights.top_weighted_movers:
            content += f"- **[[{ticker}]]**: {weighted:.1f} weighted mentions\n"
    
    if insights.sentiment_leaders:
        content += "\n## 📊 Sentiment Leaders\n\n"
        for ticker, sentiment in insights.sentiment_leaders:
            sentiment_label = "🚀 Bullish" if sentiment > 0.2 else "📉 Bearish" if sentiment < -0.2 else "➡️ Neutral"
            content += f"- **[[{ticker}]]**: {sentiment:+.2f} ({sentiment_label})\n"
    
    if insights.organic_spikes:
        content += "\n## ✅ Organic Spikes (News-Driven Excluded)\n\n"
        for ticker, organic, total in insights.organic_spikes:
            news = total - organic
            content += f"- **[[{ticker}]]**: {organic} organic / {total} total ({news} news)\n"
    
    if insights.trending_accounts:
        content += "\n## 🔥 Trending Accounts\n\n"
        for account in insights.trending_accounts:
            content += f"- `{account}`\n"
    
    content += "\n## 📋 Detailed Breakdown\n\n"
    for snap in sorted(snapshots, key=lambda x: x.total_mentions, reverse=True):
        content += f"""### {snap.ticker}

- **Mentions:** {snap.total_mentions:,}
"""
        if snap.weighted_mentions is not None:
            content += f"- **Weighted Mentions:** {snap.weighted_mentions:.1f}\n"
        if snap.sentiment_score is not None:
            sentiment_label = "Bullish" if snap.sentiment_score > 0.2 else "Bearish" if snap.sentiment_score < -0.2 else "Neutral"
            content += f"- **Sentiment:** {snap.sentiment_score:+.2f} ({sentiment_label})\n"
        if snap.organic_mentions > 0 or snap.news_mentions > 0:
            content += f"- **Organic:** {snap.organic_mentions}, **News:** {snap.news_mentions}\n"
        content += f"- **Velocity:** {format_number(snap.delta_mentions)}\n"
        content += f"- **Acceleration:** {format_number(snap.acceleration) if snap.acceleration is not None else 'N/A'}\n"
        if snap.mindshare_score:
            content += f"- **Mindshare:** {snap.mindshare_score:.2f}\n"
        
        if snap.new_accounts:
            content += f"- **New Accounts:** {', '.join(f'`{a}`' for a in snap.new_accounts)}\n"
        if snap.lost_accounts:
            content += f"- **Lost Accounts:** {', '.join(f'`{a}`' for a in snap.lost_accounts)}\n"
        
        content += "\n"
    
    content += f"\n---\n*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"
    
    return content


def generate_telegram_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> str:
    """Generate Telegram-formatted text (plain text with emojis)."""
    date_str = date.strftime('%Y-%m-%d')
    
    content = f"""📊 *Narrative Digest - {date_str}*

📈 *Summary*
• Total Mentions: {insights.total_mentions:,}
• Unique Accounts: {insights.unique_accounts}
• Avg Mindshare: {insights.avg_mindshare:.2f}

🚀 *Top Movers*
"""
    
    for ticker, velocity in insights.top_movers[:3]:
        content += f"• {ticker}: {format_number(velocity)}\n"
    
    content += "\n⚡ *Fastest Accelerating*\n"
    for ticker, accel in insights.fastest_accelerating[:3]:
        content += f"• {ticker}: {format_number(accel)}\n"
    
    content += "\n💎 *Highest Mindshare*\n"
    for ticker, score in insights.highest_mindshare[:3]:
        content += f"• {ticker}: {score:.2f}\n"
    
    if insights.top_weighted_movers:
        content += "\n⚖️ *Top Weighted Movers*\n"
        for ticker, weighted in insights.top_weighted_movers[:3]:
            content += f"• {ticker}: {weighted:.1f}\n"
    
    if insights.sentiment_leaders:
        content += "\n📊 *Sentiment Leaders*\n"
        for ticker, sentiment in insights.sentiment_leaders[:3]:
            emoji = "🚀" if sentiment > 0.2 else "📉" if sentiment < -0.2 else "➡️"
            content += f"• {ticker}: {sentiment:+.2f} {emoji}\n"
    
    if insights.organic_spikes:
        content += "\n✅ *Organic Spikes*\n"
        for ticker, organic, total in insights.organic_spikes[:3]:
            content += f"• {ticker}: {organic}/{total} organic\n"
    
    if insights.trending_accounts:
        content += "\n🔥 *Trending Accounts*\n"
        for account in insights.trending_accounts[:5]:
            content += f"• @{account}\n"
    
    content += f"\n_Generated: {datetime.utcnow().strftime('%H:%M UTC')}_"
    
    return content


def generate_discord_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> str:
    """Generate Discord-formatted markdown."""
    date_str = date.strftime('%Y-%m-%d')
    
    content = f"""# 📊 Narrative Digest - {date_str}

## 📈 Summary
**Total Mentions:** {insights.total_mentions:,}
**Unique Accounts:** {insights.unique_accounts}
**Average Mindshare:** {insights.avg_mindshare:.2f}

## 🚀 Top Movers
"""
    
    for ticker, velocity in insights.top_movers[:5]:
        emoji = "🚀" if velocity > 10 else "📈" if velocity > 0 else "📉"
        content += f"{emoji} **{ticker}**: `{format_number(velocity)}`\n"
    
    content += "\n## ⚡ Fastest Accelerating\n"
    for ticker, accel in insights.fastest_accelerating[:5]:
        content += f"⚡ **{ticker}**: `{format_number(accel)}`\n"
    
    content += "\n## 💎 Highest Mindshare\n"
    for ticker, score in insights.highest_mindshare[:5]:
        content += f"💎 **{ticker}**: `{score:.2f}`\n"
    
    if insights.top_weighted_movers:
        content += "\n## ⚖️ Top Weighted Movers\n"
        for ticker, weighted in insights.top_weighted_movers[:5]:
            content += f"⚖️ **{ticker}**: `{weighted:.1f}` weighted\n"
    
    if insights.sentiment_leaders:
        content += "\n## 📊 Sentiment Leaders\n"
        for ticker, sentiment in insights.sentiment_leaders[:5]:
            emoji = "🚀" if sentiment > 0.2 else "📉" if sentiment < -0.2 else "➡️"
            content += f"{emoji} **{ticker}**: `{sentiment:+.2f}`\n"
    
    if insights.organic_spikes:
        content += "\n## ✅ Organic Spikes\n"
        for ticker, organic, total in insights.organic_spikes[:5]:
            content += f"✅ **{ticker}**: `{organic}/{total}` organic\n"
    
    if insights.trending_accounts:
        content += "\n## 🔥 Trending Accounts\n"
        for account in insights.trending_accounts[:5]:
            content += f"• `{account}`\n"
    
    content += f"\n*Generated: {datetime.utcnow().strftime('%H:%M UTC')}*"
    
    return content


def generate_email_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> Tuple[str, str]:
    """Generate email digest (HTML and plain text)."""
    date_str = date.strftime('%Y-%m-%d')
    
    # HTML version
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .ticker {{ font-weight: bold; color: #2c3e50; }}
        .metric {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Narrative Digest - {date_str}</h1>
    </div>
    
    <div class="section">
        <h2>📈 Executive Summary</h2>
        <ul>
            <li><strong>Total Mentions:</strong> {insights.total_mentions:,}</li>
            <li><strong>Unique Accounts:</strong> {insights.unique_accounts}</li>
            <li><strong>Average Mindshare:</strong> {insights.avg_mindshare:.2f}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>🚀 Top Movers</h2>
        <table>
            <tr><th>Ticker</th><th>Velocity</th></tr>
"""
    
    for ticker, velocity in insights.top_movers:
        html += f"            <tr><td class='ticker'>{ticker}</td><td>{format_number(velocity)}</td></tr>\n"
    
    html += """        </table>
    </div>
    
    <div class="section">
        <h2>⚡ Fastest Accelerating</h2>
        <table>
            <tr><th>Ticker</th><th>Acceleration</th></tr>
"""
    
    for ticker, accel in insights.fastest_accelerating:
        html += f"            <tr><td class='ticker'>{ticker}</td><td>{format_number(accel)}</td></tr>\n"
    
    html += """        </table>
    </div>
    
    <div class="section">
        <h2>💎 Highest Mindshare</h2>
        <table>
            <tr><th>Ticker</th><th>Score</th></tr>
"""
    
    for ticker, score in insights.highest_mindshare:
        html += f"            <tr><td class='ticker'>{ticker}</td><td>{score:.2f}</td></tr>\n"
    
    html += """        </table>
    </div>
    
    <div class="section">
        <p><em>Generated: """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC') + """</em></p>
    </div>
</body>
</html>"""
    
    # Plain text version
    text = f"""NARRATIVE DIGEST - {date_str}

EXECUTIVE SUMMARY
Total Mentions: {insights.total_mentions:,}
Unique Accounts: {insights.unique_accounts}
Average Mindshare: {insights.avg_mindshare:.2f}

TOP MOVERS
"""
    
    for ticker, velocity in insights.top_movers:
        text += f"{ticker}: {format_number(velocity)}\n"
    
    text += "\nFASTEST ACCELERATING\n"
    for ticker, accel in insights.fastest_accelerating:
        text += f"{ticker}: {format_number(accel)}\n"
    
    text += "\nHIGHEST MINDSHARE\n"
    for ticker, score in insights.highest_mindshare:
        text += f"{ticker}: {score:.2f}\n"
    
    text += f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    
    return html, text


def generate_blog_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> str:
    """Generate blog-formatted markdown."""
    date_str = date.strftime('%B %d, %Y')
    
    content = f"""# Daily Narrative Digest - {date_str}

## Executive Summary

Today's narrative landscape shows significant activity across {len(snapshots)} tracked assets, with a total of {insights.total_mentions:,} mentions from {insights.unique_accounts} unique smart accounts. The average mindshare score stands at {insights.avg_mindshare:.2f}, indicating {('strong' if insights.avg_mindshare > 0.5 else 'moderate')} narrative engagement.

## Top Movers

The following assets showed the strongest velocity (change in mentions):

"""
    
    for i, (ticker, velocity) in enumerate(insights.top_movers, 1):
        content += f"{i}. **{ticker}**: {format_number(velocity)} mentions\n"
    
    content += "\n## Fastest Accelerating\n\nThe assets with the highest acceleration (change in velocity) are:\n\n"
    
    for i, (ticker, accel) in enumerate(insights.fastest_accelerating, 1):
        content += f"{i}. **{ticker}**: {format_number(accel)} acceleration\n"
    
    content += "\n## Highest Mindshare\n\nAssets with the strongest mindshare scores:\n\n"
    
    for i, (ticker, score) in enumerate(insights.highest_mindshare, 1):
        content += f"{i}. **{ticker}**: {score:.2f}\n"
    
    content += "\n## Detailed Analysis\n\n"
    
    for snap in sorted(snapshots, key=lambda x: x.total_mentions, reverse=True):
        content += f"""### {snap.ticker}

- **Total Mentions**: {snap.total_mentions:,}
- **Velocity**: {format_number(snap.delta_mentions)} mentions
- **Acceleration**: {format_number(snap.acceleration)}
"""
        if snap.mindshare_score:
            content += f"- **Mindshare Score**: {snap.mindshare_score:.2f}\n"
        
        if snap.new_accounts:
            content += f"- **New Accounts**: {', '.join(snap.new_accounts)}\n"
        if snap.lost_accounts:
            content += f"- **Lost Accounts**: {', '.join(snap.lost_accounts)}\n"
        
        content += "\n"
    
    if insights.trending_accounts:
        content += "## Trending Accounts\n\n"
        content += "The following accounts are actively engaging with multiple assets:\n\n"
        for account in insights.trending_accounts:
            content += f"- {account}\n"
        content += "\n"
    
    content += f"\n---\n\n*Report generated on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}*\n"
    
    return content


def generate_json_digest(snapshots: List[EnrichedSnapshot], insights: DigestInsights, date: datetime) -> Dict:
    """Generate JSON-structured digest."""
    return {
        "date": date.isoformat(),
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_mentions": insights.total_mentions,
            "unique_accounts": insights.unique_accounts,
            "average_mindshare": insights.avg_mindshare,
            "tickers_tracked": len(snapshots)
        },
        "insights": {
            "top_movers": [{"ticker": t, "velocity": v} for t, v in insights.top_movers],
            "fastest_accelerating": [{"ticker": t, "acceleration": a} for t, a in insights.fastest_accelerating],
            "highest_mindshare": [{"ticker": t, "score": s} for t, s in insights.highest_mindshare],
            "most_mentioned": [{"ticker": t, "mentions": m} for t, m in insights.most_mentioned],
            "account_churn_leaders": [{"ticker": t, "net_accounts": n} for t, n in insights.account_churn_leaders],
            "trending_accounts": insights.trending_accounts
        },
        "tickers": [
            {
                "ticker": snap.ticker,
                "total_mentions": snap.total_mentions,
                "velocity": snap.delta_mentions,
                "acceleration": snap.acceleration,
                "mindshare_score": snap.mindshare_score,
                "top_smart_accounts": snap.top_smart_accounts,
                "new_accounts": snap.new_accounts,
                "lost_accounts": snap.lost_accounts,
                "timestamp": snap.timestamp.isoformat()
            }
            for snap in snapshots
        ]
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate daily narrative digest in multiple formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all formats
  python narrative_digest.py BTC ETH SOL --window 24h --output ./digests

  # Generate specific format
  python narrative_digest.py BTC ETH --window 24h --output ./digests --format obsidian

  # Generate for specific date
  python narrative_digest.py BTC ETH SOL --window 24h --output ./digests --date 2024-01-15
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='+',
        help='Ticker symbols to include (e.g., BTC ETH SOL AAPL)'
    )
    
    parser.add_argument(
        '--window',
        default='24h',
        help='Time window for aggregation (default: 24h)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('./digests'),
        help='Output directory (default: ./digests)'
    )
    
    parser.add_argument(
        '--format',
        choices=['all', 'obsidian', 'telegram', 'discord', 'email', 'blog', 'json'],
        default='all',
        help='Output format (default: all)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Date for digest (YYYY-MM-DD), defaults to today'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching for fresh data'
    )
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        try:
            date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        date = datetime.utcnow()
    
    # Determine formats
    formats = []
    if args.format == 'all':
        formats = ['obsidian', 'telegram', 'discord', 'email', 'blog', 'json']
    else:
        formats = [args.format]
    
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
        sys.exit(1)
    
    # Analyze and generate insights
    print("\n📊 Analyzing data...")
    insights = analyze_snapshots(enriched_snapshots)
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    date_str = date.strftime('%Y%m%d')
    
    # Generate digests
    print(f"\n📝 Generating digests...")
    
    if 'obsidian' in formats:
        content = generate_obsidian_digest(enriched_snapshots, insights, date)
        output_path = args.output / f"digest_{date_str}.md"
        output_path.write_text(content, encoding='utf-8')
        print(f"✅ Obsidian digest: {output_path}")
    
    if 'telegram' in formats:
        content = generate_telegram_digest(enriched_snapshots, insights, date)
        output_path = args.output / f"digest_{date_str}_telegram.txt"
        output_path.write_text(content, encoding='utf-8')
        print(f"✅ Telegram digest: {output_path}")
    
    if 'discord' in formats:
        content = generate_discord_digest(enriched_snapshots, insights, date)
        output_path = args.output / f"digest_{date_str}_discord.md"
        output_path.write_text(content, encoding='utf-8')
        print(f"✅ Discord digest: {output_path}")
    
    if 'email' in formats:
        html, text = generate_email_digest(enriched_snapshots, insights, date)
        html_path = args.output / f"digest_{date_str}_email.html"
        text_path = args.output / f"digest_{date_str}_email.txt"
        html_path.write_text(html, encoding='utf-8')
        text_path.write_text(text, encoding='utf-8')
        print(f"✅ Email digest: {html_path}, {text_path}")
    
    if 'blog' in formats:
        content = generate_blog_digest(enriched_snapshots, insights, date)
        output_path = args.output / f"digest_{date_str}_blog.md"
        output_path.write_text(content, encoding='utf-8')
        print(f"✅ Blog digest: {output_path}")
    
    if 'json' in formats:
        data = generate_json_digest(enriched_snapshots, insights, date)
        output_path = args.output / f"digest_{date_str}.json"
        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f"✅ JSON digest: {output_path}")
    
    print(f"\n✅ All digests generated in: {args.output}")
    
    if failed_tickers:
        sys.exit(1)


if __name__ == "__main__":
    main()