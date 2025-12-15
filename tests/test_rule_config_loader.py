"""
Tests for rule configuration loader (YAML/JSON).

Tests cover:
- Loading rules from YAML files
- Loading rules from JSON files
- Rule type parsing (spike, velocity, anomaly, smart_money, mindshare)
- Custom rules
- Error handling
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from optional.alerts_engine import RuleConfigLoader, AlertRule


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file."""
    fd, path = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestYAMLConfigLoader:
    """Tests for YAML configuration loading."""
    
    def test_load_spike_rule_from_yaml(self, temp_yaml_file):
        """Test loading spike rule from YAML."""
        yaml_content = """
alerts:
  - name: "BTC Spike"
    ticker: "BTC"
    type: "spike"
    threshold: 60
    cooldown_minutes: 30
"""
        with open(temp_yaml_file, 'w') as f:
            f.write(yaml_content)
        
        rules = RuleConfigLoader.load_from_file(temp_yaml_file)
        
        assert len(rules) == 1
        assert rules[0].name == "BTC Spike"
        assert rules[0].ticker == "BTC"
        assert rules[0].cooldown_minutes == 30
    
    def test_load_velocity_rule_from_yaml(self, temp_yaml_file):
        """Test loading velocity rule from YAML."""
        yaml_content = """
alerts:
  - name: "ETH Velocity"
    ticker: "ETH"
    type: "velocity"
    velocity_threshold: 10.0
    cooldown_minutes: 20
"""
        with open(temp_yaml_file, 'w') as f:
            f.write(yaml_content)
        
        rules = RuleConfigLoader.load_from_file(temp_yaml_file)
        
        assert len(rules) == 1
        assert rules[0].name == "ETH Velocity"
        assert rules[0].ticker == "ETH"
    
    def test_load_multiple_rules_from_yaml(self, temp_yaml_file):
        """Test loading multiple rules from YAML."""
        yaml_content = """
alerts:
  - name: "BTC Spike"
    ticker: "BTC"
    type: "spike"
    threshold: 60
    
  - name: "ETH Velocity"
    ticker: "ETH"
    type: "velocity"
    velocity_threshold: 10.0
    
  - name: "SOL Mindshare"
    ticker: "SOL"
    type: "mindshare"
    threshold: 0.1
"""
        with open(temp_yaml_file, 'w') as f:
            f.write(yaml_content)
        
        rules = RuleConfigLoader.load_from_file(temp_yaml_file)
        
        assert len(rules) == 3
        assert rules[0].ticker == "BTC"
        assert rules[1].ticker == "ETH"
        assert rules[2].ticker == "SOL"
    
    def test_load_rule_with_custom_message(self, temp_yaml_file):
        """Test loading rule with custom message template."""
        yaml_content = """
alerts:
  - name: "Custom Alert"
    ticker: "BTC"
    type: "spike"
    threshold: 50
    message: "Custom: {ticker} has {mentions} mentions"
"""
        with open(temp_yaml_file, 'w') as f:
            f.write(yaml_content)
        
        rules = RuleConfigLoader.load_from_file(temp_yaml_file)
        
        assert len(rules) == 1
        assert "Custom:" in rules[0].message_template
    
    def test_load_yaml_handles_missing_file(self):
        """Test loading YAML handles missing file gracefully."""
        rules = RuleConfigLoader.load_from_file("/nonexistent/file.yaml")
        
        assert rules == []
    
    def test_load_yaml_handles_invalid_yaml(self, temp_yaml_file):
        """Test loading YAML handles invalid YAML gracefully."""
        with open(temp_yaml_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        rules = RuleConfigLoader.load_from_file(temp_yaml_file)
        
        # Should handle gracefully
        assert isinstance(rules, list)


class TestJSONConfigLoader:
    """Tests for JSON configuration loading."""
    
    def test_load_spike_rule_from_json(self, temp_json_file):
        """Test loading spike rule from JSON."""
        json_content = {
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
        with open(temp_json_file, 'w') as f:
            json.dump(json_content, f)
        
        rules = RuleConfigLoader.load_from_file(temp_json_file)
        
        assert len(rules) == 1
        assert rules[0].name == "BTC Spike"
        assert rules[0].ticker == "BTC"
    
    def test_load_all_rule_types_from_json(self, temp_json_file):
        """Test loading all rule types from JSON."""
        json_content = {
            "alerts": [
                {
                    "name": "Spike",
                    "ticker": "BTC",
                    "type": "spike",
                    "threshold": 50
                },
                {
                    "name": "Velocity",
                    "ticker": "ETH",
                    "type": "velocity",
                    "velocity_threshold": 10.0
                },
                {
                    "name": "Anomaly",
                    "ticker": "SOL",
                    "type": "anomaly",
                    "z_threshold": 2.0
                },
                {
                    "name": "Smart Money",
                    "ticker": "BTC",
                    "type": "smart_money",
                    "min_accounts": 3
                },
                {
                    "name": "Mindshare",
                    "ticker": "ETH",
                    "type": "mindshare",
                    "threshold": 0.1
                }
            ]
        }
        with open(temp_json_file, 'w') as f:
            json.dump(json_content, f)
        
        rules = RuleConfigLoader.load_from_file(temp_json_file)
        
        assert len(rules) == 5
        assert all(isinstance(r, AlertRule) for r in rules)
    
    def test_load_json_handles_missing_file(self):
        """Test loading JSON handles missing file gracefully."""
        rules = RuleConfigLoader.load_from_file("/nonexistent/file.json")
        
        assert rules == []
    
    def test_load_json_handles_invalid_json(self, temp_json_file):
        """Test loading JSON handles invalid JSON gracefully."""
        with open(temp_json_file, 'w') as f:
            f.write("{ invalid json }")
        
        rules = RuleConfigLoader.load_from_file(temp_json_file)
        
        # Should handle gracefully
        assert isinstance(rules, list)


class TestRuleTypeParsing:
    """Tests for parsing different rule types."""
    
    def test_parse_spike_rule(self):
        """Test parsing spike rule type."""
        config = {
            "name": "Test Spike",
            "ticker": "BTC",
            "type": "spike",
            "threshold": 50
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is not None
        assert rule.name == "Test Spike"
        # Test condition
        assert rule.condition({'mentions': 60}) is True
        assert rule.condition({'mentions': 30}) is False
    
    def test_parse_velocity_rule(self):
        """Test parsing velocity rule type."""
        config = {
            "name": "Test Velocity",
            "ticker": "ETH",
            "type": "velocity",
            "velocity_threshold": 10.0
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is not None
        # Test condition
        assert rule.condition({'mentions_velocity': 15.0}) is True
        assert rule.condition({'mentions_velocity': 5.0}) is False
    
    def test_parse_anomaly_rule(self):
        """Test parsing anomaly rule type."""
        config = {
            "name": "Test Anomaly",
            "ticker": "SOL",
            "type": "anomaly",
            "z_threshold": 2.0
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is not None
        # Test condition
        assert rule.condition({'z_score': 2.5}) is True
        assert rule.condition({'z_score': 1.0}) is False
    
    def test_parse_smart_money_rule(self):
        """Test parsing smart money rule type."""
        config = {
            "name": "Test Smart Money",
            "ticker": "BTC",
            "type": "smart_money",
            "min_accounts": 3
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is not None
        # Test condition
        assert rule.condition({'smart_accounts': ['a1', 'a2', 'a3', 'a4']}) is True
        assert rule.condition({'smart_accounts': ['a1', 'a2']}) is False
    
    def test_parse_mindshare_rule(self):
        """Test parsing mindshare rule type."""
        config = {
            "name": "Test Mindshare",
            "ticker": "ETH",
            "type": "mindshare",
            "threshold": 0.1
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is not None
        # Test condition
        assert rule.condition({'mindshare': 0.15}) is True
        assert rule.condition({'mindshare': 0.05}) is False
    
    def test_parse_missing_required_fields(self):
        """Test parsing rule with missing required fields."""
        config = {
            "ticker": "BTC",
            "type": "spike"
            # Missing 'name'
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is None
    
    def test_parse_unknown_rule_type(self):
        """Test parsing unknown rule type."""
        config = {
            "name": "Test",
            "ticker": "BTC",
            "type": "unknown_type"
        }
        
        rule = RuleConfigLoader._create_rule_from_config(config)
        
        assert rule is None


class TestAlertsEngineConfigIntegration:
    """Tests for AlertsEngine integration with config loader."""
    
    def test_load_rules_from_config(self, temp_json_file):
        """Test AlertsEngine.load_rules_from_config method."""
        from optional.alerts_engine import AlertsEngine
        
        json_content = {
            "alerts": [
                {
                    "name": "BTC Spike",
                    "ticker": "BTC",
                    "type": "spike",
                    "threshold": 60
                }
            ]
        }
        with open(temp_json_file, 'w') as f:
            json.dump(json_content, f)
        
        engine = AlertsEngine(db_path=":memory:")
        engine.load_rules_from_config(temp_json_file)
        
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "BTC Spike"

