# Optional v1.1 Modules

This directory contains advanced features that extend the MVP core functionality.

## Modules

### Signal & Analysis
- **signal_composer.py** - Multi-source signal fusion (narrative + market + on-chain)
- **delta_store.py** - Historical analysis and anomaly detection (DuckDB backend)

### Alerts & Automation
- **alerts_engine.py** - Rule-based alerting system with persistence
- **position_monitor.py** - Continuous position monitoring
- **entry_scanner.py** - High-conviction entry setup detection
- **pre_trade_check.py** - Pre-trade validation

### Visualization & Outputs
- **narrative_heatmap.py** - Relationship visualizations (requires matplotlib/seaborn)
- **narrative_digest.py** - Multi-format daily digests

### Market Data Clients
- **perp_client.py** - Binance perpetual futures data
- **onchain_client.py** - On-chain metrics (template)

### Workflows
- **morning_routine.py** - Automated morning scan workflow
- **eod_review.py** - End-of-day review workflow

## Usage

### Import Path Updates

Since these modules are in `optional/`, you may need to update import paths:

**Option 1: Add to Python path**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "optional"))
```

**Option 2: Use relative imports (if running from root)**
```python
from optional.signal_composer import SignalComposer
from optional.delta_store import DeltaStore
```

**Option 3: Run from root directory**
```bash
# From project root
python -m optional.entry_scanner BTC ETH SOL
```

## Dependencies

Some modules require additional dependencies:

```bash
# For delta_store.py
pip install duckdb>=0.9.0

# For narrative_heatmap.py
pip install matplotlib>=3.7.0 seaborn>=0.12.0 numpy>=1.24.0
```

## Documentation

See [../docs/v1.1/](../docs/v1.1/) for complete documentation on these modules.

