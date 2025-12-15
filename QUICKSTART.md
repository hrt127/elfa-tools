# 🚀 Elfa Tools Quickstart

**Get started in 5 minutes.** This guide will have you running your first narrative intelligence scan.

---

## ⚡ What is Elfa Tools?

Elfa Tools transforms raw narrative signals into actionable insights by tracking:

- **Velocity** - Change in mentions over time
- **Acceleration** - Change in velocity (momentum)
- **Account Churn** - New/lost smart accounts


It surfaces **Decision Moments**—structured explanations of why now matters.

See [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) for the complete philosophy.

---

## 🎯 Installation (2 minutes)

### Step 1: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set API Key

```bash
# Linux/macOS
export ELFA_API_KEY="your_api_key_here"

# Windows (PowerShell)
$env:ELFA_API_KEY="your_api_key_here"

# Windows (CMD)
set ELFA_API_KEY=your_api_key_here
```

**Get your API key:** [docs.elfa.ai](https://docs.elfa.ai)

---

## 🎮 Your First Scan (1 minute)

### Try This Now:

```bash
# Scan 3 tickers for narrative activity
python narrative_radar.py BTC ETH SOL --window 4h
```

**What you'll see:**

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


**You just completed your first narrative intelligence scan!** 🎉

---

## 📊 Understanding the Output

### Velocity Indicators

- 🚀 **+45** - Strong upward momentum (>10 mentions)
- 📈 **+23** - Moderate upward trend (5-10 mentions)
- ↗️ **+5** - Slight increase (0-5 mentions)
- ➡️ **0** - Stable (no change)
- ↘️ **-5** - Slight decrease
- 📉 **-23** - Moderate decline
- 💥 **-45** - Strong decline

---

### Acceleration

- ⚡ **+12** - Accelerating (velocity increasing)
- 🔺 **+8** - Positive acceleration
- ➡️ **+2** - Stable acceleration
- 🔻 **-8** - Negative acceleration (slowing)

---

### Mindshare

- **0.85** - High mindshare (85% of narrative space)
- **0.72** - Moderate mindshare
- **0.58** - Lower mindshare

---

### Account Churn

- **+2 new, -1 lost** - Gaining smart accounts
- **stable** - No account changes
- **-2 lost** - Losing smart accounts


---

## 🎯 Next Steps

### 1. Explore Different Time Windows

```bash
# Short-term (1 hour)
python narrative_radar.py BTC ETH --window 1h

# Medium-term (4 hours)
python narrative_radar.py BTC ETH --window 4h

# Long-term (24 hours)
python narrative_radar.py BTC ETH --window 24h
```

### 2. Export to Markdown

```bash
# Save scan results
python narrative_radar.py BTC ETH SOL --window 4h --export scan_results.md
```

### 3. Learn About Decision Moments

Read [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) to understand:

- What a Decision Moment is
- How Elfa surfaces "why now matters"
- The 6 core design principles

### 4. Explore v1.1 Features

Check out `optional/` directory for:

- Multi-source signal fusion
- Rule-based alerting
- Historical analysis
- Trading workflows

See [docs/v1.1/](./docs/v1.1/) for full documentation.


---

## 🔧 Common Tasks

### Daily Scan

```bash
# Morning scan of your watchlist
python narrative_radar.py BTC ETH SOL HYPE PENGU --window 4h
```

### Track a Single Ticker

```bash
# Monitor one ticker over time
python narrative_radar.py BTC --window 24h --export btc_daily.md
```

### Fresh Data (No Cache)

```bash
# Force fresh API call
python narrative_radar.py BTC --window 1h --no-cache
```

---

## 💡 Pro Tips

1. **Start with 4h window** - Good balance of recent activity and stability
2. **Use caching** - Default behavior saves API calls (5-minute TTL)
3. **Export regularly** - Build a history of scans for pattern recognition
4. **Watch acceleration** - Positive acceleration often precedes major moves
5. **Monitor account churn** - New smart accounts = follow the flow

---

## 🆘 Troubleshooting

### "ELFA_API_KEY environment variable is not set"

- Make sure you exported the key in your current shell
- Check: `echo $ELFA_API_KEY` (Linux/macOS)

### "No data available"

- Verify your API key is correct
- Check ticker symbols are valid
- Try a longer time window (24h instead of 1h)

### "Rate limit exceeded"

- Wait a minute and try again
- The client automatically tracks rate limits
- Use `--no-cache` sparingly


---

## 📚 Learn More

- **[DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md)** - Core philosophy and Decision Moment concept
- **[docs/v1.1/](./docs/v1.1/)** - Advanced features and workflows
- **[docs/examples/](./docs/examples/)** - Example Decision Moments

---

**Ready to dive deeper?** Explore the [v1.1 features](./docs/v1.1/) or read about [Decision Moments](./DESIGN_PRINCIPLES.md).
