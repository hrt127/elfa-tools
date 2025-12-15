#!/usr/bin/env python3
"""
Narrative Co-Heatmap Generator - Visualize nested relationships between ticker narratives.

Creates various heatmaps showing:
- Account overlap between tickers
- Account-ticker mention patterns
- Velocity correlations
- Mindshare similarities
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
import numpy as np
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: matplotlib/seaborn not installed. Install with: pip install matplotlib seaborn")

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import NarrativeEnricher, EnrichedSnapshot


def compute_account_overlap_matrix(enriched_snapshots: List[EnrichedSnapshot]) -> Tuple[np.ndarray, List[str]]:
    """
    Compute account overlap matrix between tickers.
    
    Returns:
        (matrix, tickers) where matrix[i][j] = Jaccard similarity of accounts between tickers i and j
    """
    tickers = [snap.ticker for snap in enriched_snapshots]
    n = len(tickers)
    matrix = np.zeros((n, n))
    
    # Convert to account sets
    account_sets = {}
    for i, snap in enumerate(enriched_snapshots):
        account_sets[snap.ticker] = set(snap.top_smart_accounts or [])
    
    # Compute Jaccard similarity for each pair
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0  # Perfect overlap with itself
            else:
                set_i = account_sets[tickers[i]]
                set_j = account_sets[tickers[j]]
                
                if not set_i and not set_j:
                    similarity = 1.0  # Both empty
                elif not set_i or not set_j:
                    similarity = 0.0  # One empty
                else:
                    intersection = len(set_i & set_j)
                    union = len(set_i | set_j)
                    similarity = intersection / union if union > 0 else 0.0
                
                matrix[i][j] = similarity
    
    return matrix, tickers


def compute_account_ticker_matrix(enriched_snapshots: List[EnrichedSnapshot]) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Compute account-ticker mention matrix.
    
    Returns:
        (matrix, tickers, accounts) where matrix[i][j] = 1 if account j mentions ticker i
    """
    # Collect all unique accounts
    all_accounts = set()
    ticker_account_map = {}
    
    for snap in enriched_snapshots:
        accounts = set(snap.top_smart_accounts or [])
        ticker_account_map[snap.ticker] = accounts
        all_accounts.update(accounts)
    
    tickers = [snap.ticker for snap in enriched_snapshots]
    accounts = sorted(list(all_accounts))
    
    # Build binary matrix
    matrix = np.zeros((len(tickers), len(accounts)))
    for i, ticker in enumerate(tickers):
        for j, account in enumerate(accounts):
            if account in ticker_account_map[ticker]:
                matrix[i][j] = 1.0
    
    return matrix, tickers, accounts


def compute_velocity_correlation_matrix(enriched_snapshots: List[EnrichedSnapshot]) -> Tuple[np.ndarray, List[str]]:
    """
    Compute velocity correlation matrix.
    
    Returns:
        (matrix, tickers) where matrix[i][j] = correlation of velocity patterns
    """
    tickers = [snap.ticker for snap in enriched_snapshots]
    n = len(tickers)
    matrix = np.zeros((n, n))
    
    # Extract velocities
    velocities = [snap.delta_mentions for snap in enriched_snapshots]
    
    # For now, use simple correlation based on velocity values
    # In a full implementation, you'd track velocity over time
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0
            else:
                # Simple similarity: how close are the velocities?
                v1, v2 = velocities[i], velocities[j]
                if v1 == 0 and v2 == 0:
                    corr = 1.0
                elif v1 == 0 or v2 == 0:
                    corr = 0.0
                else:
                    # Normalize and compute similarity
                    max_abs = max(abs(v1), abs(v2), 1)
                    diff = abs(v1 - v2) / max_abs
                    corr = 1.0 - min(diff, 1.0)
                matrix[i][j] = corr
    
    return matrix, tickers


def compute_mindshare_similarity_matrix(enriched_snapshots: List[EnrichedSnapshot]) -> Tuple[np.ndarray, List[str]]:
    """
    Compute mindshare similarity matrix.
    
    Returns:
        (matrix, tickers) where matrix[i][j] = similarity of mindshare scores
    """
    tickers = [snap.ticker for snap in enriched_snapshots]
    n = len(tickers)
    matrix = np.zeros((n, n))
    
    # Extract mindshare scores (handle None)
    mindshares = []
    for snap in enriched_snapshots:
        score = snap.mindshare_score if snap.mindshare_score is not None else 0.0
        mindshares.append(score)
    
    # Compute similarity
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0
            else:
                s1, s2 = mindshares[i], mindshares[j]
                if s1 == 0 and s2 == 0:
                    similarity = 1.0
                else:
                    max_score = max(abs(s1), abs(s2), 0.01)
                    diff = abs(s1 - s2) / max_score
                    similarity = 1.0 - min(diff, 1.0)
                matrix[i][j] = similarity
    
    return matrix, tickers


def plot_heatmap(
    matrix: np.ndarray,
    row_labels: List[str],
    col_labels: Optional[List[str]] = None,
    title: str = "Heatmap",
    xlabel: str = "",
    ylabel: str = "",
    cmap: str = "viridis",
    figsize: Tuple[int, int] = (10, 8),
    output_path: Optional[Path] = None,
    annot: bool = True,
    fmt: str = ".2f"
):
    """Plot a heatmap using matplotlib/seaborn."""
    if not HAS_PLOTTING:
        print("Error: matplotlib/seaborn required for plotting")
        return
    
    if col_labels is None:
        col_labels = row_labels
    
    plt.figure(figsize=figsize)
    sns.heatmap(
        matrix,
        xticklabels=col_labels,
        yticklabels=row_labels,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        cbar_kws={'label': 'Similarity/Correlation'},
        square=True,
        linewidths=0.5
    )
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Heatmap saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def export_heatmap_markdown(
    matrix: np.ndarray,
    row_labels: List[str],
    col_labels: Optional[List[str]] = None,
    title: str = "Heatmap",
    output_path: Path
):
    """Export heatmap as markdown table."""
    if col_labels is None:
        col_labels = row_labels
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write("---\n\n")
        
        # Create markdown table
        header = "| | " + " | ".join(col_labels) + " |\n"
        separator = "|" + "|".join(["---"] * (len(col_labels) + 1)) + "|\n"
        f.write(header)
        f.write(separator)
        
        for i, row_label in enumerate(row_labels):
            row = f"| **{row_label}** |"
            for j in range(len(col_labels)):
                value = matrix[i][j]
                row += f" {value:.3f} |"
            row += "\n"
            f.write(row)
        
        f.write("\n---\n\n")
        f.write("*Values represent similarity/correlation scores (0.0 = no relationship, 1.0 = identical)*\n")
    
    print(f"✅ Markdown heatmap exported to: {output_path}")


def generate_co_heatmaps(
    enriched_snapshots: List[EnrichedSnapshot],
    output_dir: Path,
    formats: List[str] = ["png", "md"]
):
    """Generate all co-heatmaps for the given snapshots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # 1. Account Overlap Matrix
    print("📊 Generating account overlap matrix...")
    overlap_matrix, tickers = compute_account_overlap_matrix(enriched_snapshots)
    
    if "png" in formats and HAS_PLOTTING:
        plot_heatmap(
            overlap_matrix,
            tickers,
            title="Account Overlap Matrix\n(Jaccard Similarity)",
            xlabel="Ticker",
            ylabel="Ticker",
            cmap="YlOrRd",
            output_path=output_dir / f"account_overlap_{timestamp}.png"
        )
    
    if "md" in formats:
        export_heatmap_markdown(
            overlap_matrix,
            tickers,
            title="Account Overlap Matrix (Jaccard Similarity)",
            output_path=output_dir / f"account_overlap_{timestamp}.md"
        )
    
    # 2. Account-Ticker Matrix
    print("📊 Generating account-ticker mention matrix...")
    account_ticker_matrix, tickers, accounts = compute_account_ticker_matrix(enriched_snapshots)
    
    if "png" in formats and HAS_PLOTTING:
        # For large matrices, only show if reasonable size
        if len(accounts) <= 20:
            plot_heatmap(
                account_ticker_matrix,
                tickers,
                accounts,
                title="Account-Ticker Mention Matrix",
                xlabel="Account",
                ylabel="Ticker",
                cmap="Blues",
                output_path=output_dir / f"account_ticker_{timestamp}.png",
                annot=True,
                fmt=".0f"
            )
        else:
            print(f"⚠️  Skipping account-ticker PNG (too many accounts: {len(accounts)})")
    
    if "md" in formats:
        export_heatmap_markdown(
            account_ticker_matrix,
            tickers,
            accounts,
            title="Account-Ticker Mention Matrix",
            output_path=output_dir / f"account_ticker_{timestamp}.md"
        )
    
    # 3. Velocity Correlation Matrix
    print("📊 Generating velocity correlation matrix...")
    velocity_matrix, tickers = compute_velocity_correlation_matrix(enriched_snapshots)
    
    if "png" in formats and HAS_PLOTTING:
        plot_heatmap(
            velocity_matrix,
            tickers,
            title="Velocity Correlation Matrix",
            xlabel="Ticker",
            ylabel="Ticker",
            cmap="RdYlGn",
            output_path=output_dir / f"velocity_correlation_{timestamp}.png"
        )
    
    if "md" in formats:
        export_heatmap_markdown(
            velocity_matrix,
            tickers,
            title="Velocity Correlation Matrix",
            output_path=output_dir / f"velocity_correlation_{timestamp}.md"
        )
    
    # 4. Mindshare Similarity Matrix
    print("📊 Generating mindshare similarity matrix...")
    mindshare_matrix, tickers = compute_mindshare_similarity_matrix(enriched_snapshots)
    
    if "png" in formats and HAS_PLOTTING:
        plot_heatmap(
            mindshare_matrix,
            tickers,
            title="Mindshare Similarity Matrix",
            xlabel="Ticker",
            ylabel="Ticker",
            cmap="Purples",
            output_path=output_dir / f"mindshare_similarity_{timestamp}.png"
        )
    
    if "md" in formats:
        export_heatmap_markdown(
            mindshare_matrix,
            tickers,
            title="Mindshare Similarity Matrix",
            output_path=output_dir / f"mindshare_similarity_{timestamp}.md"
        )
    
    print(f"\n✅ All heatmaps generated in: {output_dir}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate co-heatmaps showing relationships between ticker narratives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate heatmaps for multiple tickers
  python narrative_heatmap.py BTC ETH SOL --window 1h --output ./heatmaps

  # Only markdown format
  python narrative_heatmap.py BTC ETH --window 1h --output ./heatmaps --format md

  # Only PNG images
  python narrative_heatmap.py BTC ETH SOL --window 1h --output ./heatmaps --format png
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='+',
        help='Ticker symbols to analyze (e.g., BTC ETH SOL AAPL)'
    )
    
    parser.add_argument(
        '--window',
        default='1h',
        help='Time window for aggregation (default: 1h)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('./heatmaps'),
        help='Output directory for heatmaps (default: ./heatmaps)'
    )
    
    parser.add_argument(
        '--format',
        choices=['png', 'md', 'both'],
        default='both',
        help='Output format: png (images), md (markdown), or both (default: both)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching for fresh data'
    )
    
    args = parser.parse_args()
    
    # Determine formats
    formats = []
    if args.format == 'both':
        formats = ['png', 'md']
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
    
    if len(enriched_snapshots) < 2:
        print("\n⚠️  Warning: Need at least 2 tickers for relationship analysis.")
        sys.exit(1)
    
    # Generate heatmaps
    print(f"\n📈 Generating co-heatmaps...")
    generate_co_heatmaps(enriched_snapshots, args.output, formats)
    
    if failed_tickers:
        sys.exit(1)


if __name__ == "__main__":
    main()