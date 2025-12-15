"""
delta_store.py - Chronicle backend for narrative signals

Stores narrative snapshots in DuckDB for historical analysis.
Enables shift detection, trend analysis, and anomaly detection.

Supports both TickerNarrativeSnapshot and EnrichedSnapshot from the codebase.
"""

import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union
import json

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing data structures
from elfa_client import TickerNarrativeSnapshot
from narrative_enricher import EnrichedSnapshot


class DeltaStore:
    """Lightweight time-series store for narrative signals."""

    def __init__(self, db_path: str = "narrative_chronicle.duckdb"):
        """
        Initialize DuckDB connection and create tables if needed.
        
        Args:
            db_path: Path to DuckDB database file
        """
        try:
            self.db_path = db_path
            self.conn = duckdb.connect(db_path)
            self._init_tables()
        except Exception as e:
            print(f"Warning: Failed to initialize DeltaStore: {e}")
            raise
    
    def _init_tables(self):
        """Create tables for narrative snapshots."""
        try:
            # Check if table exists and has new columns
            try:
                self.conn.execute("SELECT sentiment_score FROM narrative_snapshots LIMIT 1")
                # Table exists with new columns
            except:
                # Table exists but missing new columns - add them
                try:
                    self.conn.execute("ALTER TABLE narrative_snapshots ADD COLUMN sentiment_score DOUBLE")
                except:
                    pass  # Column might already exist
                try:
                    self.conn.execute("ALTER TABLE narrative_snapshots ADD COLUMN organic_mentions INTEGER DEFAULT 0")
                except:
                    pass
                try:
                    self.conn.execute("ALTER TABLE narrative_snapshots ADD COLUMN news_mentions INTEGER DEFAULT 0")
                except:
                    pass
                try:
                    self.conn.execute("ALTER TABLE narrative_snapshots ADD COLUMN weighted_mentions DOUBLE")
                except:
                    pass
                try:
                    self.conn.execute("ALTER TABLE narrative_snapshots ADD COLUMN platform VARCHAR")
                except:
                    pass
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS narrative_snapshots (
                    id INTEGER PRIMARY KEY,
                    ticker VARCHAR NOT NULL,
                    "window" VARCHAR NOT NULL,
                    mentions INTEGER NOT NULL,
                    mindshare DOUBLE,
                    smart_accounts VARCHAR,
                    timestamp TIMESTAMP NOT NULL,
                    source_query VARCHAR,
                    sentiment_score DOUBLE,
                    organic_mentions INTEGER DEFAULT 0,
                    news_mentions INTEGER DEFAULT 0,
                    weighted_mentions DOUBLE,
                    platform VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # DuckDB doesn't support AUTO_INCREMENT directly, so we'll use a sequence
            # But actually, we can just omit id and let DuckDB handle it
            # Let's check if we need to modify the INSERT
            
            # Index for fast queries
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
                ON narrative_snapshots(ticker, timestamp DESC)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_window_timestamp 
                ON narrative_snapshots("window", timestamp DESC)
            """)
        except Exception as e:
            print(f"Warning: Failed to initialize tables: {e}")
            raise
    
    def insert(self, snapshot: Union[TickerNarrativeSnapshot, EnrichedSnapshot]) -> bool:
        """
        Insert a snapshot into the store.
        
        Supports both TickerNarrativeSnapshot and EnrichedSnapshot.
        
        Args:
            snapshot: TickerNarrativeSnapshot or EnrichedSnapshot to store
            
        Returns:
            True if successful, False otherwise. Never raises exceptions.
        """
        try:
            # Handle both data types
            if isinstance(snapshot, EnrichedSnapshot):
                mentions = snapshot.total_mentions
                mindshare = snapshot.mindshare_score
                smart_accounts = snapshot.top_smart_accounts
                timestamp = snapshot.timestamp
                source_query = snapshot.source_query
                sentiment_score = snapshot.sentiment_score
                organic_mentions = snapshot.organic_mentions
                news_mentions = snapshot.news_mentions
                weighted_mentions = snapshot.weighted_mentions
                platform = snapshot.platform
            elif isinstance(snapshot, TickerNarrativeSnapshot):
                mentions = snapshot.total_mentions
                mindshare = snapshot.mindshare_score
                smart_accounts = snapshot.top_smart_accounts
                timestamp = datetime.utcnow()  # TickerNarrativeSnapshot doesn't have timestamp
                source_query = snapshot.source_query
                sentiment_score = snapshot.sentiment_score
                organic_mentions = snapshot.organic_mentions
                news_mentions = snapshot.news_mentions
                weighted_mentions = None  # Will need to calculate
                platform = snapshot.platform
            else:
                print(f"Warning: Unsupported snapshot type: {type(snapshot)}")
                return False
            
            # Ensure timestamp is datetime object
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.utcnow()
            
            # Get next ID (DuckDB doesn't have AUTO_INCREMENT, so we calculate it)
            max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM narrative_snapshots").fetchone()
            next_id = (max_id_result[0] if max_id_result else 0) + 1
            
            self.conn.execute("""
                INSERT INTO narrative_snapshots 
                (id, ticker, "window", mentions, mindshare, smart_accounts, timestamp, source_query,
                 sentiment_score, organic_mentions, news_mentions, weighted_mentions, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                next_id,
                snapshot.ticker,
                snapshot.window,
                mentions,
                mindshare,
                json.dumps(smart_accounts) if smart_accounts else None,
                timestamp,
                source_query or "",
                sentiment_score,
                organic_mentions,
                news_mentions,
                weighted_mentions,
                platform
            ))
            return True
        except Exception as e:
            print(f"Warning: Insert error: {e}")
            return False
    
    def get_latest(self, ticker: str, window: str = "4h") -> Optional[Dict]:
        """
        Get most recent snapshot for a ticker.
        
        Args:
            ticker: Ticker symbol
            window: Time window (e.g., "1h", "4h", "24h")
            
        Returns:
            Dict with snapshot data, or None if not found. Never raises exceptions.
        """
        try:
            result = self.conn.execute("""
                SELECT ticker, "window", mentions, mindshare, smart_accounts, timestamp, source_query
                FROM narrative_snapshots
                WHERE ticker = ? AND "window" = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (ticker.upper(), window)).fetchone()
            
            if not result:
                return None
            
            return {
                'ticker': result[0],
                'window': result[1],
                'mentions': result[2],
                'mindshare': result[3],
                'smart_accounts': json.loads(result[4]) if result[4] else [],
                'timestamp': result[5],
                'source_query': result[6] or ""
            }
        except Exception as e:
            print(f"Warning: Failed to get latest snapshot: {e}")
            return None
    
    def get_history(
        self, 
        ticker: str, 
        window: str = "4h",
        hours_back: int = 24
    ) -> List[Dict]:
        """
        Get historical snapshots for trend analysis.
        
        Args:
            ticker: Ticker symbol
            window: Time window (e.g., "1h", "4h", "24h")
            hours_back: Number of hours to look back
            
        Returns:
            List of snapshot dicts, ordered by timestamp ASC. Never raises exceptions.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours_back)
            
            results = self.conn.execute("""
                SELECT ticker, "window", mentions, mindshare, smart_accounts, timestamp, source_query
                FROM narrative_snapshots
                WHERE ticker = ? AND "window" = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (ticker.upper(), window, cutoff)).fetchall()
            
            return [{
                'ticker': r[0],
                'window': r[1],
                'mentions': r[2],
                'mindshare': r[3],
                'smart_accounts': json.loads(r[4]) if r[4] else [],
                'timestamp': r[5],
                'source_query': r[6] or ""
            } for r in results]
        except Exception as e:
            print(f"Warning: Failed to get history: {e}")
            return []
    
    def calculate_velocity(self, ticker: str, window: str = "4h") -> Optional[Dict]:
        """
        Calculate narrative velocity (rate of change).
        
        Returns dict with current, previous, and velocity metrics.
        Never raises exceptions.
        """
        try:
            history = self.get_history(ticker, window, hours_back=8)
            
            if len(history) < 2:
                return None
            
            current = history[-1]
            previous = history[0]
            
            # Calculate time delta in hours
            current_time = current['timestamp']
            previous_time = previous['timestamp']
            if isinstance(current_time, str):
                current_time = datetime.fromisoformat(current_time)
            if isinstance(previous_time, str):
                previous_time = datetime.fromisoformat(previous_time)
            
            time_delta_hours = (current_time - previous_time).total_seconds() / 3600
            if time_delta_hours <= 0:
                time_delta_hours = 1  # Avoid division by zero
            
            # Calculate deltas
            mentions_delta = current['mentions'] - previous['mentions']
            mentions_velocity = mentions_delta / time_delta_hours if time_delta_hours > 0 else 0
            
            mindshare_delta = 0
            mindshare_velocity = 0
            if current['mindshare'] and previous['mindshare']:
                mindshare_delta = current['mindshare'] - previous['mindshare']
                mindshare_velocity = mindshare_delta / time_delta_hours if time_delta_hours > 0 else 0
            
            return {
                'ticker': ticker,
                'current_mentions': current['mentions'],
                'previous_mentions': previous['mentions'],
                'mentions_delta': mentions_delta,
                'mentions_velocity': mentions_velocity,
                'current_mindshare': current['mindshare'],
                'previous_mindshare': previous['mindshare'],
                'mindshare_delta': mindshare_delta,
                'mindshare_velocity': mindshare_velocity,
                'acceleration': 'up' if mentions_velocity > 0 else 'down',
                'datapoints': len(history)
            }
        except Exception as e:
            print(f"Warning: Failed to calculate velocity: {e}")
            return None
    
    def detect_anomalies(
        self, 
        ticker: str, 
        window: str = "4h",
        std_threshold: float = 2.0
    ) -> Optional[Dict]:
        """
        Detect statistical anomalies in narrative data.
        
        Returns dict if current value is >threshold std devs from mean.
        Never raises exceptions.
        """
        try:
            history = self.get_history(ticker, window, hours_back=48)
            
            if len(history) < 10:
                return None
            
            current = history[-1]
            
            # Use rolling window: only last 24 hours for mean/std calculation
            # This prevents stale data from affecting anomaly detection
            window_hours = 24
            cutoff_time = current['timestamp']
            if isinstance(cutoff_time, str):
                cutoff_time = datetime.fromisoformat(cutoff_time)
            elif isinstance(cutoff_time, (int, float)):
                cutoff_time = datetime.fromtimestamp(cutoff_time)
            
            # Filter to last 24 hours
            recent_history = []
            for h in history[:-1]:  # Excludes current
                h_time = h['timestamp']
                if isinstance(h_time, str):
                    h_time = datetime.fromisoformat(h_time)
                elif isinstance(h_time, (int, float)):
                    h_time = datetime.fromtimestamp(h_time)
                
                hours_ago = (cutoff_time - h_time).total_seconds() / 3600
                if hours_ago <= window_hours:
                    recent_history.append(h)
            
            # If we don't have enough recent data, use all available (but at least 10)
            if len(recent_history) < 10:
                mentions = [h['mentions'] for h in history[:-1]]
            else:
                mentions = [h['mentions'] for h in recent_history]
            
            import statistics
            mean = statistics.mean(mentions)
            stdev = statistics.stdev(mentions) if len(mentions) > 1 else 0
            
            z_score = (current['mentions'] - mean) / stdev if stdev > 0 else 0
            
            if abs(z_score) >= std_threshold:
                return {
                    'ticker': ticker,
                    'current_mentions': current['mentions'],
                    'mean_mentions': round(mean, 2),
                    'stdev': round(stdev, 2),
                    'z_score': round(z_score, 2),
                    'anomaly_type': 'spike' if z_score > 0 else 'drop',
                    'severity': 'extreme' if abs(z_score) >= 3.0 else 'significant'
                }
            
            return None
        except Exception as e:
            print(f"Warning: Failed to detect anomalies: {e}")
            return None
    
    def get_watchlist_summary(
        self, 
        tickers: List[str], 
        window: str = "4h"
    ) -> List[Dict]:
        """
        Get latest data for multiple tickers, sorted by momentum.
        
        Never raises exceptions.
        """
        try:
            if not tickers:
                return []
            
            tickers_upper = [t.upper() for t in tickers]
            placeholders = ','.join(['?' for _ in tickers_upper])
            results = self.conn.execute(f"""
                WITH latest AS (
                    SELECT 
                        ticker,
                        "window",
                        mentions,
                        mindshare,
                        smart_accounts,
                        timestamp,
                        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp DESC) as rn
                    FROM narrative_snapshots
                    WHERE ticker IN ({placeholders}) AND "window" = ?
                )
                SELECT ticker, "window", mentions, mindshare, smart_accounts, timestamp
                FROM latest
                WHERE rn = 1
                ORDER BY (COALESCE(mindshare, 0) * mentions) DESC
            """, (*tickers_upper, window)).fetchall()
            
            return [{
                'ticker': r[0],
                'window': r[1],
                'mentions': r[2],
                'mindshare': r[3],
                'smart_accounts': json.loads(r[4]) if r[4] else [],
                'timestamp': r[5],
                'momentum_score': (r[3] or 0) * r[2]
            } for r in results]
        except Exception as e:
            print(f"Warning: Failed to get watchlist summary: {e}")
            return []
    
    def get_sentiment_history(
        self,
        ticker: str,
        window: str = "1h",
        days: int = 7
    ) -> List[Dict]:
        """
        Get sentiment history for a ticker.
        
        Args:
            ticker: Ticker symbol
            window: Time window
            days: Number of days of history to retrieve
            
        Returns:
            List of sentiment records. Never raises exceptions.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            results = self.conn.execute("""
                SELECT timestamp, sentiment_score, mentions, weighted_mentions
                FROM narrative_snapshots
                WHERE ticker = ? AND "window" = ? AND timestamp >= ? AND sentiment_score IS NOT NULL
                ORDER BY timestamp ASC
            """, (ticker.upper(), window, cutoff)).fetchall()
            
            return [{
                'timestamp': r[0],
                'sentiment_score': r[1],
                'mentions': r[2],
                'weighted_mentions': r[3]
            } for r in results]
        except Exception as e:
            print(f"Warning: Failed to get sentiment history: {e}")
            return []
    
    def get_organic_spikes(
        self,
        window: str = "1h",
        min_organic_ratio: float = 0.7,
        min_mentions: int = 20,
        days: int = 7
    ) -> List[Dict]:
        """
        Get organic narrative spikes (excluding news-driven).
        
        Args:
            window: Time window
            min_organic_ratio: Minimum ratio of organic to total mentions
            min_mentions: Minimum total mentions to consider
            days: Number of days to look back
            
        Returns:
            List of organic spike records. Never raises exceptions.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            results = self.conn.execute("""
                SELECT ticker, timestamp, organic_mentions, news_mentions, mentions, weighted_mentions
                FROM narrative_snapshots
                WHERE "window" = ? 
                  AND timestamp >= ?
                  AND mentions >= ?
                  AND organic_mentions > 0
                  AND (CAST(organic_mentions AS DOUBLE) / NULLIF(mentions, 0)) >= ?
                ORDER BY timestamp DESC, mentions DESC
            """, (window, cutoff, min_mentions, min_organic_ratio)).fetchall()
            
            return [{
                'ticker': r[0],
                'timestamp': r[1],
                'organic_mentions': r[2],
                'news_mentions': r[3],
                'total_mentions': r[4],
                'weighted_mentions': r[5],
                'organic_ratio': r[2] / r[4] if r[4] > 0 else 0.0
            } for r in results]
        except Exception as e:
            print(f"Warning: Failed to get organic spikes: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """
        Remove data older than N days to keep DB size manageable.
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            True if successful, False otherwise. Never raises exceptions.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = self.conn.execute("""
                DELETE FROM narrative_snapshots
                WHERE timestamp < ?
            """, (cutoff,))
            
            deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0
            print(f"Cleaned up {deleted_count} records older than {days_to_keep} days")
            return True
        except Exception as e:
            print(f"Warning: Failed to cleanup old data: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        try:
            self.conn.close()
        except Exception as e:
            print(f"Warning: Failed to close connection: {e}")


# Usage example
if __name__ == "__main__":
    store = DeltaStore()
    
    # Example: Calculate velocity for BTC
    velocity = store.calculate_velocity("BTC", "4h")
    if velocity:
        print(f"\nBTC Narrative Velocity:")
        print(f"Mentions: {velocity['current_mentions']} (Δ {velocity['mentions_delta']:+d})")
        print(f"Velocity: {velocity['mentions_velocity']:.1f} mentions/snapshot")
        print(f"Trend: {velocity['acceleration']}")
    
    # Example: Detect anomalies
    anomaly = store.detect_anomalies("BTC", "4h")
    if anomaly:
        print(f"\n🚨 ANOMALY DETECTED:")
        print(f"{anomaly['ticker']}: {anomaly['current_mentions']} mentions")
        print(f"Mean: {anomaly['mean_mentions']}, Z-score: {anomaly['z_score']}")
        print(f"Type: {anomaly['anomaly_type']} ({anomaly['severity']})")
    
    store.close()

