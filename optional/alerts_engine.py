"""
alerts_engine.py - Configurable rule-based alert system

Define narrative thresholds and get notified when they trigger.
Supports multiple notification channels and custom rule logic.

Integrates with:
- elfa_client.TickerNarrativeSnapshot
- narrative_enricher.EnrichedSnapshot
- signal_composer.CompositeSignal
"""

from typing import List, Dict, Callable, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import sqlite3
from pathlib import Path

import sys
from pathlib import Path

# Add parent directory to path for MVP core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing data structures
from elfa_client import TickerNarrativeSnapshot, is_organic_narrative_spike, calculate_weighted_mentions, calculate_platform_divergence, get_trending_contracts
from narrative_enricher import EnrichedSnapshot

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

@dataclass
class AlertRule:
    """A single alert rule with condition and action."""
    name: str
    ticker: str
    condition: Callable[[Dict], bool]
    message_template: str
    cooldown_minutes: int = 15  # Prevent spam
    last_triggered: Optional[datetime] = None
    
    def check(
        self, 
        data: Dict,
        get_cooldown_state: Optional[Callable] = None,
        save_cooldown_state: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Check if rule triggers and return message if so.
        
        Args:
            data: Data dictionary to check
            get_cooldown_state: Optional function to get persisted cooldown state
            save_cooldown_state: Optional function to save cooldown state
        
        Returns None if:
        - Condition not met
        - Still in cooldown period
        """
        # Check cooldown - prefer persisted state if available
        last_triggered = self.last_triggered
        if get_cooldown_state:
            persisted = get_cooldown_state(self.name, self.ticker)
            if persisted:
                last_triggered = persisted
        
        if last_triggered:
            minutes_since = (datetime.now() - last_triggered).total_seconds() / 60
            if minutes_since < self.cooldown_minutes:
                return None
        
        # Check condition
        if not self.condition(data):
            return None
        
        # Trigger!
        self.last_triggered = datetime.now()
        return self.message_template.format(**data)


class AlertsEngine:
    """
    Manages multiple alert rules and notification channels.
    
    Features:
    - Rule-based alert conditions
    - Multi-channel notification delivery
    - Alert history persistence (SQLite)
    - Cooldown management to prevent spam
    - Graceful error handling (never crashes)
    """
    
    def __init__(self, db_path: str = "alerts_history.db"):
        """
        Initialize alerts engine.
        
        Args:
            db_path: Path to SQLite database for alert history
        """
        self.rules: List[AlertRule] = []
        self.channels: List[Callable] = []
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for alert history and cooldown state."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
                ON alert_history(ticker, timestamp DESC)
            """)
            # Cooldown state table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_cooldowns (
                    rule_name TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    last_triggered TEXT NOT NULL,
                    PRIMARY KEY (rule_name, ticker)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to initialize alert database: {e}")
    
    def add_rule(self, rule: AlertRule):
        """Add a new alert rule and load its cooldown state from database."""
        # Load persisted cooldown state
        self._load_cooldown_state(rule)
        self.rules.append(rule)
    
    def load_rules_from_config(self, config_path: str):
        """
        Load alert rules from YAML/JSON configuration file.
        
        Args:
            config_path: Path to YAML or JSON config file
        """
        rules = RuleConfigLoader.load_from_file(config_path)
        for rule in rules:
            self.add_rule(rule)
        print(f"Loaded {len(rules)} rules from {config_path}")
    
    def add_channel(self, channel: Callable):
        """
        Add a notification channel.
        
        Channel should be a function that takes (message: str) and sends it.
        Example: print, telegram_send, discord_send, email_send
        """
        self.channels.append(channel)
    
    def check_all(
        self, 
        ticker: str, 
        data: Union[Dict, TickerNarrativeSnapshot, EnrichedSnapshot]
    ):
        """
        Check all rules for a ticker and fire alerts.
        
        Args:
            ticker: Ticker symbol
            data: Can be Dict, TickerNarrativeSnapshot, or EnrichedSnapshot
        
        Never raises exceptions.
        """
        try:
            # Normalize data to dict format
            data_dict = self._normalize_data(data)
            if not data_dict:
                return
            
            for rule in self.rules:
                if rule.ticker.upper() != ticker.upper():
                    continue
                
                # Load cooldown state from database before checking
                self._load_cooldown_state(rule)
                
                # Use persisted cooldown state functions
                message = rule.check(
                    data_dict,
                    get_cooldown_state=self._get_cooldown_state,
                    save_cooldown_state=self._save_cooldown_state
                )
                if message:
                    self._fire_alert(rule.name, ticker, message)
                    # Save cooldown state after alert fires
                    if rule.last_triggered:
                        self._save_cooldown_state(rule.name, ticker, rule.last_triggered)
        except Exception as e:
            print(f"Warning: Failed to check alerts: {e}")
    
    def _normalize_data(
        self, 
        data: Union[Dict, TickerNarrativeSnapshot, EnrichedSnapshot]
    ) -> Optional[Dict]:
        """Normalize data from various formats to dict. Never raises exceptions."""
        try:
            if isinstance(data, (TickerNarrativeSnapshot, EnrichedSnapshot)):
                # Calculate weighted mentions if not already present
                weighted_mentions = None
                if isinstance(data, EnrichedSnapshot) and data.weighted_mentions is not None:
                    weighted_mentions = data.weighted_mentions
                elif isinstance(data, TickerNarrativeSnapshot):
                    weighted_data = calculate_weighted_mentions(data)
                    weighted_mentions = weighted_data.get("weighted_mentions")
                
                # Check organic status
                is_organic = True
                organic_mentions = getattr(data, 'organic_mentions', 0)
                news_mentions = getattr(data, 'news_mentions', 0)
                if isinstance(data, TickerNarrativeSnapshot):
                    analysis = is_organic_narrative_spike(data.ticker, data.window, min_mentions=1)
                    is_organic = analysis.get("is_organic", True)
                    organic_mentions = data.organic_mentions
                    news_mentions = data.news_mentions
                elif isinstance(data, EnrichedSnapshot):
                    # Determine if spike is truly organic by checking that organic mentions
                    # significantly outweigh news mentions (similar to is_organic_narrative_spike logic)
                    total_mentions = data.total_mentions
                    if total_mentions == 0:
                        is_organic = False
                    else:
                        news_ratio = news_mentions / total_mentions
                        # Consider organic if news ratio is less than 30% (same threshold as is_organic_narrative_spike)
                        is_organic = news_ratio < 0.3 and organic_mentions > 0
                
                # Calculate news_ratio for alert templates
                total_mentions = data.total_mentions
                news_ratio = news_mentions / total_mentions if total_mentions > 0 else 0.0
                
                return {
                    'ticker': data.ticker,
                    'mentions': total_mentions,
                    'weighted_mentions': weighted_mentions,
                    'organic_mentions': organic_mentions,
                    'news_mentions': news_mentions,
                    'news_ratio': news_ratio,
                    'is_organic': is_organic,
                    'sentiment_score': getattr(data, 'sentiment_score', None),
                    'mindshare': data.mindshare_score,
                    'smart_accounts': data.top_smart_accounts,
                    'smart_accounts_count': len(data.top_smart_accounts) if data.top_smart_accounts else 0,
                    'mentions_velocity': getattr(data, 'delta_mentions', 0) if isinstance(data, EnrichedSnapshot) else 0,
                    'acceleration': getattr(data, 'acceleration', 0) if isinstance(data, EnrichedSnapshot) else 0,
                    'window': getattr(data, 'window', '1h')
                }
            elif isinstance(data, dict):
                return data
            else:
                print(f"Warning: Unsupported data type: {type(data)}")
                return None
        except Exception as e:
            print(f"Warning: Failed to normalize data: {e}")
            return None
    
    def _fire_alert(self, rule_name: str, ticker: str, message: str):
        """
        Send alert through all channels and persist to database.
        
        Never raises exceptions.
        """
        try:
            alert_record = {
                'rule': rule_name,
                'ticker': ticker,
                'message': message,
                'timestamp': datetime.utcnow()
            }
            
            # Persist to database
            self._save_alert(alert_record)
            
            # Send through all channels
            for channel in self.channels:
                try:
                    channel(message)
                except Exception as e:
                    print(f"Warning: Channel error: {e}")
        except Exception as e:
            print(f"Warning: Failed to fire alert: {e}")
    
    def _save_alert(self, alert: Dict):
        """Save alert to database. Never raises exceptions."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO alert_history (rule_name, ticker, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                alert['rule'],
                alert['ticker'],
                alert['message'],
                alert['timestamp'].isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to save alert: {e}")
    
    def get_history(self, ticker: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get alert history, optionally filtered by ticker.
        
        Args:
            ticker: Optional ticker to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of alert records. Never raises exceptions.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            if ticker:
                cursor = conn.execute("""
                    SELECT rule_name, ticker, message, timestamp, acknowledged
                    FROM alert_history
                    WHERE ticker = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (ticker.upper(), limit))
            else:
                cursor = conn.execute("""
                    SELECT rule_name, ticker, message, timestamp, acknowledged
                    FROM alert_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [{
                'rule': r[0],
                'ticker': r[1],
                'message': r[2],
                'timestamp': datetime.fromisoformat(r[3]),
                'acknowledged': bool(r[4])
            } for r in results]
        except Exception as e:
            print(f"Warning: Failed to get alert history: {e}")
            return []
    
    def _load_cooldown_state(self, rule: AlertRule):
        """Load cooldown state from database for a rule. Never raises exceptions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT last_triggered
                FROM alert_cooldowns
                WHERE rule_name = ? AND ticker = ?
            """, (rule.name, rule.ticker))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                rule.last_triggered = datetime.fromisoformat(row[0])
        except Exception as e:
            print(f"Warning: Failed to load cooldown state: {e}")
    
    def _get_cooldown_state(self, rule_name: str, ticker: str) -> Optional[datetime]:
        """Get cooldown state from database. Never raises exceptions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT last_triggered
                FROM alert_cooldowns
                WHERE rule_name = ? AND ticker = ?
            """, (rule_name, ticker))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return datetime.fromisoformat(row[0])
            return None
        except Exception as e:
            print(f"Warning: Failed to get cooldown state: {e}")
            return None
    
    def _save_cooldown_state(self, rule_name: str, ticker: str, last_triggered: datetime):
        """Save cooldown state to database. Never raises exceptions."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO alert_cooldowns (rule_name, ticker, last_triggered)
                VALUES (?, ?, ?)
            """, (rule_name, ticker, last_triggered.isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to save cooldown state: {e}")


# Example rule factories (pre-built common rules)
class RuleFactory:
    """Pre-built alert rule templates."""
    
    @staticmethod
    def spike_detector(ticker: str, threshold: int = 50, organic_only: bool = False) -> AlertRule:
        """Alert when mentions spike above threshold. Optionally filter to organic spikes only."""
        def condition(d):
            mentions = d.get('mentions', 0)
            if mentions <= threshold:
                return False
            if organic_only:
                return d.get('is_organic', True)
            return True
        
        return AlertRule(
            name=f"{ticker}_spike" + ("_organic" if organic_only else ""),
            ticker=ticker,
            condition=condition,
            message_template=(
                "🔥 SPIKE: {ticker}\n"
                "{mentions} mentions (threshold: " + str(threshold) + ")\n"
                "Mindshare: {mindshare:.2f}" +
                ("\n✅ Organic spike" if organic_only else "")
            ),
            cooldown_minutes=30
        )
    
    @staticmethod
    def velocity_alert(ticker: str, velocity_threshold: float = 10.0) -> AlertRule:
        """Alert when mention velocity exceeds threshold."""
        return AlertRule(
            name=f"{ticker}_velocity",
            ticker=ticker,
            condition=lambda d: abs(d.get('mentions_velocity', 0)) > velocity_threshold,
            message_template=(
                "📈 ACCELERATION: {ticker}\n"
                "Velocity: {mentions_velocity:+.1f} mentions/snapshot\n"
                "Trend: {acceleration}"
            ),
            cooldown_minutes=20
        )
    
    @staticmethod
    def anomaly_alert(ticker: str) -> AlertRule:
        """Alert when statistical anomaly detected."""
        return AlertRule(
            name=f"{ticker}_anomaly",
            ticker=ticker,
            condition=lambda d: (d.get('z_score') is not None) and abs(d['z_score']) >= 2.0,
            message_template=(
                "🚨 ANOMALY: {ticker}\n"
                "Current: {current_mentions} mentions\n"
                "Mean: {mean_mentions:.0f}, Z-score: {z_score:+.1f}\n"
                "Severity: {severity}"
            ),
            cooldown_minutes=60
        )
    
    @staticmethod
    def smart_money_alert(ticker: str, min_accounts: int = 3) -> AlertRule:
        """Alert when multiple smart accounts mention ticker."""
        return AlertRule(
            name=f"{ticker}_smart_money",
            ticker=ticker,
            condition=lambda d: len(d.get('smart_accounts', [])) >= min_accounts,
            message_template=(
                "💡 SMART MONEY: {ticker}\n"
                "Active accounts: {smart_accounts_count}\n"
                "Mentions: {mentions}"
            ),
            cooldown_minutes=120
        )
    
    @staticmethod
    def mindshare_threshold(ticker: str, threshold: float = 0.1) -> AlertRule:
        """Alert when mindshare crosses threshold."""
        return AlertRule(
            name=f"{ticker}_mindshare",
            ticker=ticker,
            condition=lambda d: (d.get('mindshare') or 0) > threshold,
            message_template=(
                "🎯 HIGH MINDSHARE: {ticker}\n"
                "Score: {mindshare:.2f} (threshold: " + str(threshold) + ")\n"
                "Mentions: {mentions}"
            ),
            cooldown_minutes=45
        )
    
    @staticmethod
    def contract_address_alert(platform: str = "twitter", min_mentions: int = 20, limit: int = 10) -> AlertRule:
        """Alert when contract addresses are trending."""
        def condition(d):
            # This rule works differently - it checks trending contracts
            # We'll need to fetch contracts separately
            contracts = get_trending_contracts(platform=platform, window="1h", limit=limit)
            if contracts:
                # Check if any contract has enough mentions
                return any(c.mentions >= min_mentions for c in contracts)
            return False
        
        return AlertRule(
            name=f"contract_trending_{platform}",
            ticker="*",  # Wildcard for all contracts
            condition=condition,
            message_template=(
                f"🔍 TRENDING CONTRACT: {{address}}\n"
                f"{{mentions}} mentions on {platform}\n"
                f"Top accounts: {{top_accounts}}"
            ),
            cooldown_minutes=60
        )
    
    @staticmethod
    def platform_divergence_alert(ticker: str, min_ratio: float = 2.0) -> AlertRule:
        """Alert when cross-platform divergence detected (early signal)."""
        def condition(d):
            divergence = calculate_platform_divergence(ticker, d.get('window', '1h'))
            if divergence and divergence.get("early_signal", False):
                ratio = divergence.get("divergence_ratio", 1.0)
                return ratio >= min_ratio
            return False
        
        return AlertRule(
            name=f"{ticker}_divergence",
            ticker=ticker,
            condition=condition,
            message_template=(
                "🔍 PLATFORM DIVERGENCE: {ticker}\n"
                "Early signal detected!\n"
                "Telegram: {telegram_mentions} mentions\n"
                "Twitter: {twitter_mentions} mentions\n"
                "Ratio: {divergence_ratio:.1f}x"
            ),
            cooldown_minutes=45
        )
    
    @staticmethod
    def organic_spike_alert(ticker: str, threshold: int = 30) -> AlertRule:
        """Alert when organic narrative spike detected (excluding news-driven)."""
        def condition(d):
            mentions = d.get('mentions', 0)
            if mentions < threshold:
                return False
            return d.get('is_organic', True)
        
        return AlertRule(
            name=f"{ticker}_organic_spike",
            ticker=ticker,
            condition=condition,
            message_template=(
                "✅ ORGANIC SPIKE: {ticker}\n"
                "{organic_mentions} organic mentions (total: {mentions})\n"
                "News ratio: {news_ratio:.0%}"
            ),
            cooldown_minutes=30
        )
    
    @staticmethod
    def sentiment_alert(ticker: str, min_sentiment: float = 0.3, bearish: bool = False) -> AlertRule:
        """Alert when sentiment crosses threshold (bullish or bearish)."""
        def condition(d):
            sentiment = d.get('sentiment_score')
            if sentiment is None:
                return False
            if bearish:
                return sentiment <= -min_sentiment
            else:
                return sentiment >= min_sentiment
        
        direction = "bearish" if bearish else "bullish"
        return AlertRule(
            name=f"{ticker}_sentiment_{direction}",
            ticker=ticker,
            condition=condition,
            message_template=(
                f"📊 {direction.upper()} SENTIMENT: {{ticker}}\n"
                f"Sentiment score: {{sentiment_score:+.2f}}\n"
                f"Mentions: {{mentions}}"
            ),
            cooldown_minutes=60
        )
    
    @staticmethod
    def weighted_mentions_alert(ticker: str, threshold: float = 50.0) -> AlertRule:
        """Alert when weighted mentions (account-type weighted) exceed threshold."""
        def condition(d):
            weighted = d.get('weighted_mentions')
            if weighted is None:
                return False
            return weighted >= threshold
        
        return AlertRule(
            name=f"{ticker}_weighted_mentions",
            ticker=ticker,
            condition=condition,
            message_template=(
                "⚖️ WEIGHTED MENTIONS: {ticker}\n"
                "Weighted: {weighted_mentions:.1f} (raw: {mentions})\n"
                "High-quality account activity detected"
            ),
            cooldown_minutes=45
        )


# Example notification channels
def console_channel(message: str):
    """Print to console (for testing)."""
    print(f"\n[ALERT {datetime.now().strftime('%H:%M:%S')}]")
    print(message)
    print()

def telegram_channel(message: str, bot_token: str = None, chat_id: str = None):
    """Send via Telegram bot."""
    if not bot_token or not chat_id:
        print("Warning: Telegram credentials not configured")
        return
    
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    })

def discord_channel(message: str, webhook_url: str = None):
    """Send via Discord webhook."""
    if not webhook_url:
        print("Warning: Discord webhook not configured")
        return
    
    import requests
    requests.post(webhook_url, json={'content': message})


# Configuration file support
class RuleConfigLoader:
    """Load alert rules from YAML/JSON configuration files."""
    
    @staticmethod
    def load_from_file(config_path: str) -> List[AlertRule]:
        """
        Load alert rules from YAML or JSON configuration file.
        
        Args:
            config_path: Path to YAML or JSON config file
            
        Returns:
            List of AlertRule objects
            
        Example YAML config:
            alerts:
              - name: "BTC Spike"
                ticker: "BTC"
                type: "spike"
                threshold: 60
                cooldown_minutes: 30
                message: "🔥 SPIKE: {ticker} has {mentions} mentions"
              
              - name: "ETH Velocity"
                ticker: "ETH"
                type: "velocity"
                velocity_threshold: 10.0
                cooldown_minutes: 20
                
        Example JSON config:
            {
              "alerts": [
                {
                  "name": "BTC Spike",
                  "ticker": "BTC",
                  "type": "spike",
                  "threshold": 60,
                  "cooldown_minutes": 30
                }
              ]
            }
        """
        try:
            config_path_obj = Path(config_path)
            if not config_path_obj.exists():
                print(f"Warning: Config file not found: {config_path}")
                return []
            
            # Load config based on file extension
            if config_path_obj.suffix.lower() in ['.yaml', '.yml']:
                return RuleConfigLoader.load_from_yaml(config_path)
            elif config_path_obj.suffix.lower() == '.json':
                return RuleConfigLoader.load_from_json(config_path)
            else:
                # Try to auto-detect
                try:
                    return RuleConfigLoader.load_from_yaml(config_path)
                except:
                    return RuleConfigLoader.load_from_json(config_path)
        
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return []
    
    @staticmethod
    def load_from_yaml(config_path: str) -> List[AlertRule]:
        """Load rules from YAML file."""
        if not YAML_AVAILABLE:
            print("Warning: PyYAML not installed. Install with: pip install pyyaml")
            return []
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            return RuleConfigLoader._parse_config(config)
        except Exception as e:
            print(f"Warning: Failed to parse YAML config: {e}")
            return []
    
    @staticmethod
    def load_from_json(config_path: str) -> List[AlertRule]:
        """Load rules from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return RuleConfigLoader._parse_config(config)
        except Exception as e:
            print(f"Warning: Failed to parse JSON config: {e}")
            return []
    
    @staticmethod
    def _parse_config(config: Dict) -> List[AlertRule]:
        """Parse config dict into AlertRule objects."""
        rules = []
        
        if not isinstance(config, dict) or 'alerts' not in config:
            print("Warning: Config must have 'alerts' key")
            return []
        
        for alert_config in config['alerts']:
            try:
                rule = RuleConfigLoader._create_rule_from_config(alert_config)
                if rule:
                    rules.append(rule)
            except Exception as e:
                print(f"Warning: Failed to create rule from config: {e}")
                continue
        
        return rules
    
    @staticmethod
    def _create_rule_from_config(config: Dict) -> Optional[AlertRule]:
        """Create AlertRule from config dict."""
        # Required fields
        name = config.get('name')
        ticker = config.get('ticker')
        rule_type = config.get('type')
        
        if not all([name, ticker, rule_type]):
            print(f"Warning: Rule missing required fields: name, ticker, type")
            return None
        
        # Get cooldown (default 15 minutes)
        cooldown_minutes = config.get('cooldown_minutes', 15)
        
        # Get message template (optional, will use default if not provided)
        message_template = config.get('message', None)
        
        # Create condition based on rule type
        condition = None
        
        if rule_type == 'spike':
            threshold = config.get('threshold', 50)
            condition = lambda d, t=threshold: d.get('mentions', 0) > t
            if not message_template:
                message_template = (
                    f"🔥 SPIKE: {{ticker}}\n"
                    f"{{mentions}} mentions (threshold: {threshold})\n"
                    f"Mindshare: {{mindshare:.2f}}"
                )
        
        elif rule_type == 'velocity':
            velocity_threshold = config.get('velocity_threshold', 10.0)
            condition = lambda d, vt=velocity_threshold: abs(d.get('mentions_velocity', 0)) > vt
            if not message_template:
                message_template = (
                    f"📈 ACCELERATION: {{ticker}}\n"
                    f"Velocity: {{mentions_velocity:+.1f}} mentions/snapshot\n"
                    f"Trend: {{acceleration}}"
                )
        
        elif rule_type == 'anomaly':
            z_threshold = config.get('z_threshold', 2.0)
            condition = lambda d, zt=z_threshold: d.get('z_score') and abs(d['z_score']) >= zt
            if not message_template:
                message_template = (
                    f"🚨 ANOMALY: {{ticker}}\n"
                    f"Current: {{current_mentions}} mentions\n"
                    f"Mean: {{mean_mentions:.0f}}, Z-score: {{z_score:+.1f}}\n"
                    f"Severity: {{severity}}"
                )
        
        elif rule_type == 'smart_money':
            min_accounts = config.get('min_accounts', 3)
            condition = lambda d, ma=min_accounts: len(d.get('smart_accounts', [])) >= ma
            if not message_template:
                message_template = (
                    f"💡 SMART MONEY: {{ticker}}\n"
                    f"Active accounts: {{smart_accounts_count}}\n"
                    f"Mentions: {{mentions}}"
                )
        
        elif rule_type == 'mindshare':
            threshold = config.get('threshold', 0.1)
            condition = lambda d, t=threshold: (d.get('mindshare') or 0) > t
            if not message_template:
                message_template = (
                    f"🎯 HIGH MINDSHARE: {{ticker}}\n"
                    f"Score: {{mindshare:.2f}} (threshold: {threshold})\n"
                    f"Mentions: {{mentions}}"
                )
        
        elif rule_type == 'custom':
            # Custom condition - requires condition_code or condition_function
            condition_code = config.get('condition_code')
            if condition_code:
                # Evaluate condition code (be careful with security!)
                # In production, you might want to use a safer evaluation method
                try:
                    condition = eval(condition_code)
                except Exception as e:
                    print(f"Warning: Failed to evaluate condition_code: {e}")
                    return None
            else:
                print("Warning: Custom rule type requires 'condition_code'")
                return None
            
            if not message_template:
                message_template = config.get('message', f"Alert: {{ticker}}")
        
        else:
            print(f"Warning: Unknown rule type: {rule_type}")
            return None
        
        if condition is None:
            return None
        
        return AlertRule(
            name=name,
            ticker=ticker,
            condition=condition,
            message_template=message_template,
            cooldown_minutes=cooldown_minutes
        )
    
    @staticmethod
    def save_to_file(rules: List[AlertRule], config_path: str, format: str = 'yaml'):
        """
        Save alert rules to YAML or JSON file.
        
        Args:
            rules: List of AlertRule objects
            config_path: Path to save config file
            format: 'yaml' or 'json'
        """
        try:
            config = {'alerts': []}
            
            for rule in rules:
                # Convert rule to config dict (simplified - doesn't preserve all condition logic)
                rule_config = {
                    'name': rule.name,
                    'ticker': rule.ticker,
                    'cooldown_minutes': rule.cooldown_minutes
                }
                # Note: We can't easily serialize lambda conditions, so this is limited
                config['alerts'].append(rule_config)
            
            if format.lower() == 'yaml':
                if not YAML_AVAILABLE:
                    print("Warning: PyYAML not installed. Saving as JSON instead.")
                    format = 'json'
                else:
                    with open(config_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    return
            
            # Save as JSON
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")


# Usage example
if __name__ == "__main__":
    # Initialize engine
    engine = AlertsEngine()
    
    # Add notification channels
    engine.add_channel(console_channel)
    # engine.add_channel(lambda m: telegram_channel(m, "YOUR_TOKEN", "YOUR_CHAT_ID"))
    
    # Add rules using factory
    engine.add_rule(RuleFactory.spike_detector("BTC", threshold=60))
    engine.add_rule(RuleFactory.velocity_alert("BTC", velocity_threshold=8.0))
    engine.add_rule(RuleFactory.anomaly_alert("BTC"))
    engine.add_rule(RuleFactory.smart_money_alert("ETH", min_accounts=3))
    engine.add_rule(RuleFactory.mindshare_threshold("SOL", threshold=0.08))
    
    # Simulate checking data
    test_data = {
        'ticker': 'BTC',
        'mentions': 75,
        'mindshare': 0.12,
        'mentions_velocity': 12.5,
        'acceleration': 'up',
        'smart_accounts': ['account1', 'account2', 'account3'],
        'smart_accounts_count': 3
    }
    
    print("Testing alert engine with sample data...")
    engine.check_all("BTC", test_data)
    
    # Show history
    print("\nAlert History:")
    for alert in engine.get_history():
        print(f"- {alert['rule']} @ {alert['timestamp'].strftime('%H:%M:%S')}")