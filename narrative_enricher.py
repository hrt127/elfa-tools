#!/usr/bin/env python3
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from elfa_client import TickerNarrativeSnapshot

DB_PATH = Path("./narrative_history.db")


@dataclass
class EnrichedSnapshot:
    ticker: str
    window: str
    timestamp: datetime
    total_mentions: int
    mindshare_score: Optional[float]
    top_smart_accounts: List[str]
    delta_mentions: int = 0
    acceleration: Optional[int] = None
    new_accounts: List[str] = field(default_factory=list)
    lost_accounts: List[str] = field(default_factory=list)
    source_query: str = ""
    # New fields from enhancements
    sentiment_score: Optional[float] = None
    news_mentions: int = 0
    organic_mentions: int = 0
    platform: Optional[str] = None
    weighted_mentions: Optional[float] = None  # Account-type weighted


class NarrativeEnricher:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Create table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                window TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                total_mentions INTEGER NOT NULL,
                mindshare_score REAL,
                top_accounts TEXT,
                source_query TEXT
            )
        """)
        conn.commit()
        conn.close()

    def store_snapshot(self, snap: TickerNarrativeSnapshot):
        """Persist a raw snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        accounts_str = ",".join(snap.top_smart_accounts) if snap.top_smart_accounts else ""
        cursor.execute("""
            INSERT INTO snapshots (ticker, window, timestamp, total_mentions, mindshare_score, top_accounts, source_query)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snap.ticker,
            snap.window,
            datetime.utcnow().isoformat(),
            snap.total_mentions,
            snap.mindshare_score,
            accounts_str,
            snap.source_query
        ))
        conn.commit()
        conn.close()

    def get_last_snapshot(self, ticker: str, window: str) -> Optional[TickerNarrativeSnapshot]:
        """Retrieve the most recent snapshot for a ticker/window"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticker, window, timestamp, total_mentions, mindshare_score, top_accounts, source_query
            FROM snapshots
            WHERE ticker = ? AND window = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (ticker, window))
        row = cursor.fetchone()
        conn.close()
        if row:
            accounts = row[5].split(",") if row[5] else []
            return TickerNarrativeSnapshot(
                ticker=row[0],
                window=row[1],
                total_mentions=row[3],
                mindshare_score=row[4],
                top_smart_accounts=accounts,
                source_query=row[6]
            )
        return None

    def get_last_two_snapshots(self, ticker: str, window: str) -> Tuple[Optional[TickerNarrativeSnapshot], Optional[TickerNarrativeSnapshot]]:
        """Retrieve the last two snapshots for computing acceleration (second derivative)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticker, window, timestamp, total_mentions, mindshare_score, top_accounts, source_query
            FROM snapshots
            WHERE ticker = ? AND window = ?
            ORDER BY timestamp DESC
            LIMIT 2
        """, (ticker, window))
        rows = cursor.fetchall()
        conn.close()
        
        def row_to_snapshot(row):
            accounts = row[5].split(",") if row[5] else []
            return TickerNarrativeSnapshot(
                ticker=row[0],
                window=row[1],
                total_mentions=row[3],
                mindshare_score=row[4],
                top_smart_accounts=accounts,
                source_query=row[6]
            )
        
        if len(rows) >= 2:
            return row_to_snapshot(rows[0]), row_to_snapshot(rows[1])
        elif len(rows) == 1:
            return row_to_snapshot(rows[0]), None
        else:
            return None, None

    def enrich_snapshot(self, snap: TickerNarrativeSnapshot) -> EnrichedSnapshot:
        """Compute velocity, acceleration, and account churn"""
        from elfa_client import calculate_weighted_mentions
        
        last_snap, prev_snap = self.get_last_two_snapshots(snap.ticker, snap.window)
        delta_mentions = snap.total_mentions
        acceleration = None  # Default to None (insufficient data)
        # Create defensive copy to avoid reference issues
        new_accounts = list(snap.top_smart_accounts) if snap.top_smart_accounts else []
        lost_accounts = []
        
        # Calculate weighted mentions based on account types
        weighted_data = calculate_weighted_mentions(snap)
        weighted_mentions = weighted_data.get("weighted_mentions")

        if last_snap:
            # Velocity: change in mentions from last snapshot
            delta_mentions = snap.total_mentions - last_snap.total_mentions
            
            # Acceleration: change in velocity (second derivative)
            # Requires at least 3 snapshots to calculate true acceleration
            if prev_snap:
                prev_velocity = last_snap.total_mentions - prev_snap.total_mentions
                current_velocity = delta_mentions
                acceleration = current_velocity - prev_velocity
            else:
                # Only 2 snapshots available - cannot calculate acceleration yet
                # Return None to indicate insufficient data (caller should handle)
                acceleration = None
            
            # Account churn: compare current accounts with last snapshot
            last_accounts = set(last_snap.top_smart_accounts or [])
            curr_accounts = set(snap.top_smart_accounts or [])
            new_accounts = list(curr_accounts - last_accounts)
            lost_accounts = list(last_accounts - curr_accounts)

        enriched = EnrichedSnapshot(
            ticker=snap.ticker,
            window=snap.window,
            timestamp=datetime.utcnow(),
            total_mentions=snap.total_mentions,
            mindshare_score=snap.mindshare_score,
            top_smart_accounts=snap.top_smart_accounts,
            delta_mentions=delta_mentions,
            acceleration=acceleration,
            new_accounts=new_accounts,
            lost_accounts=lost_accounts,
            source_query=snap.source_query,
            sentiment_score=snap.sentiment_score,
            news_mentions=snap.news_mentions,
            organic_mentions=snap.organic_mentions,
            platform=snap.platform,
            weighted_mentions=weighted_mentions
        )

        # store snapshot after enrichment for next comparison
        self.store_snapshot(snap)
        return enriched

    def enrich_batch(self, snapshots: List[TickerNarrativeSnapshot]) -> List[EnrichedSnapshot]:
        """Enrich multiple snapshots at once"""
        return [self.enrich_snapshot(snap) for snap in snapshots]


# -------------------------------
# Convenience function for simple usage
# -------------------------------
_default_enricher = None

def enrich_snapshot(snap: Optional[TickerNarrativeSnapshot], db_path: Optional[Path] = None) -> Optional[EnrichedSnapshot]:
    """
    Convenience function to enrich a snapshot.
    
    Uses a default global enricher instance for convenience.
    For production use, consider creating your own NarrativeEnricher instance.
    
    Args:
        snap: TickerNarrativeSnapshot to enrich, or None
        db_path: Optional custom database path
        
    Returns:
        EnrichedSnapshot or None if snap is None
    """
    global _default_enricher
    
    if snap is None:
        return None
    
    if db_path is not None:
        enricher = NarrativeEnricher(db_path=db_path)
    else:
        if _default_enricher is None:
            _default_enricher = NarrativeEnricher()
        enricher = _default_enricher
    
    return enricher.enrich_snapshot(snap)


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    from elfa_client import get_ticker_narrative_snapshot

    tickers = ["BTC", "ETH", "SOL"]
    window = "1h"
    enricher = NarrativeEnricher()

    enriched_results = []
    for ticker in tickers:
        snap = get_ticker_narrative_snapshot(ticker, window)
        if snap:
            enriched = enricher.enrich_snapshot(snap)
            enriched_results.append(enriched)
            print(f"{enriched.ticker} | mentions: {enriched.total_mentions} | Δmentions: {enriched.delta_mentions} | new accounts: {enriched.new_accounts}")
