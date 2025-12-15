# Elfa Tools

**Narrative intelligence for decision-making under uncertainty.**

Elfa Tools transforms raw narrative signals into actionable insights by tracking velocity, acceleration, and account churn. It surfaces **Decision Moments**—structured explanations of why now matters.

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Set API key
export ELFA_API_KEY="your_api_key_here"

# Run your first scan
python narrative_radar.py BTC ETH SOL --window 4h
```

**Get your API key:** [docs.elfa.ai](https://docs.elfa.ai)

---

## Core Modules

### 1. **elfa_client.py** - Fetch narrative data
- Authenticated API client with `ELFA_API_KEY`
- Graceful error handling (never crashes)
- Built-in caching and rate-limit awareness
- Audit trails with `source_query` field

### 2. **narrative_enricher.py** - Add temporal context
- SQLite-backed history tracking
- Computes velocity (change in mentions)
- Computes acceleration (change in velocity)
- Tracks account churn (new/lost accounts)

### 3. **narrative_radar.py** - View enriched data
- CLI scanner with visual indicators (🚀📈↗️➡️↘️📉💥)
- Markdown export with audit trail
- Multi-ticker support
- Shows velocity, acceleration, mindshare, churn

### 4. **decision_moment.py** - Core concept
- Structured explanations of "why now matters"
- Signal evidence tracking
- Policy engine for surfacing moments
- Explainable by default

---

## Example Output

```text
📡 NARRATIVE RADAR - 4H WINDOW
================================================================================
Ticker   Mentions    Velocity      Accel    Mindshare    Churn
--------------------------------------------------------------------------------
BTC      1250        🚀 +45         ⚡ +12   0.85         +2 new, -1 lost
ETH      980         📈 +23         🔺 +8    0.72         stable
SOL      650         ➡️ +5          ➡️ +2    0.58         stable
```

**What this tells you:**
- 🚀 **BTC** has strong momentum (high velocity, positive acceleration)
- 📈 **ETH** is trending up
- ➡️ **SOL** is stable

---

## Learn More

- **[QUICKSTART.md](./QUICKSTART.md)** - Step-by-step guide
- **[DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md)** - Core philosophy and Decision Moment concept

---

## v1.1 Features

Advanced features available in `optional/` directory:
- Multi-source signal fusion (`signal_composer.py`)
- Rule-based alerting (`alerts_engine.py`)
- Historical analysis (`delta_store.py`)
- Relationship visualizations (`narrative_heatmap.py`)
- Multi-format digests (`narrative_digest.py`)
- Trading workflows (entry scanner, pre-trade check, position monitor)

See [docs/v1.1/](./docs/v1.1/) for full documentation.

---

## Design Principles

Elfa Tools adheres to six core principles:

1. **Narrow** — Each tool does one job well
2. **Explainable** — Show source data, contributing factors, and audit trails
3. **Robust** — Fail gracefully, never crash, handle partial data
4. **Composable** — Tools work standalone and snap together naturally
5. **Signal Layer, Not Oracle** — Provides signals and context, not answers
6. **Transparent Constraints** — Rate limits, caching, and provenance are visible

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for complete details.


---

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
git clone https://github.com/your-repo/elfa-tools.git
cd elfa-tools
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### API Key Configuration

**Linux/macOS:**

```bash
export ELFA_API_KEY="your_api_key_here"
```

**Windows (PowerShell):**

```powershell
$env:ELFA_API_KEY="your_api_key_here"
```

**Persistent (recommended):**

Add to your `~/.bashrc`, `~/.zshrc`, or `.env` file.


---

## Usage

### Basic Scan

```bash
# Scan multiple tickers
python narrative_radar.py BTC ETH SOL --window 4h

# Export to markdown
python narrative_radar.py BTC ETH --window 4h --export radar_report.md

# Single ticker with fresh data
python narrative_radar.py BTC --window 24h --no-cache
```

---

## Troubleshooting

### "ELFA_API_KEY environment variable is not set"
- Ensure you've exported the API key in your current shell session
- Check: `echo $ELFA_API_KEY` (Linux/macOS) or `echo %ELFA_API_KEY%` (Windows)

### "Rate limit exceeded"
- The client automatically tracks rate limits
- Wait before making more requests, or use `--no-cache` sparingly

### "No data available"
- Check your API key is valid
- Verify the ticker symbols are correct
- Try a different time window (e.g., `24h` instead of `1h`)

---

## License

See [LICENSE](./LICENSE) file for details.

---

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
