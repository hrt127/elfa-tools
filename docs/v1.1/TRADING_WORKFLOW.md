# Trading System Workflow Guide

Complete daily workflow for using Elfa Tools in a trading system.

---

## 🎯 System Overview

This trading system uses narrative intelligence to:

- **Find opportunities** before they peak
- **Validate trades** before entry
- **Monitor positions** to prevent holding losers
- **Learn and iterate** from daily results


---

## 📋 Daily Workflow

### 7:00 AM - Morning Scan (5 minutes)

**Purpose:** Find opportunities from overnight activity

**What this tells you:**

- Which narratives spiked overnight (missed opportunity or continuation?)
- Which tickers have velocity (momentum to ride)
- Which have anomalies (mean reversion plays)


**Commands:**

```bash
# Option 1: Run complete morning routine (recommended)
python morning_routine.py BTC ETH SOL HYPE PENGU

# Option 2: Run individual steps
# 1. Scan watchlist for narrative activity
python narrative_radar.py BTC ETH SOL HYPE PENGU --window 4h

# 2. Find high-conviction entry setups
python entry_scanner.py BTC ETH SOL HYPE PENGU

# 3. Generate journal entry for knowledge management
python narrative_digest.py BTC ETH SOL --window 24h --format obsidian >> journal.md
```

**What to look for:**

- 🚀 **Spikes:** High mentions + positive acceleration = continuation play
- 📈 **Momentum:** Strong velocity = ride the trend
- 🚨 **Anomalies:** Statistical outliers = mean reversion opportunity
- 💡 **Smart Money:** New accounts = follow the flow

---

### Throughout Day - Position Monitoring (Automatic)

**Purpose:** Get warned before losses

**What this does:**

- Alerts you when narrative moves against your position
- **Long + fading narrative** = trim warning
- **Short + spiking narrative** = cover warning
- Prevents you from holding losers too long


**Setup (one time):**

1. Edit `positions.json` with your current positions:

```json
{
  "BTC": {"side": "long", "size": 1.0, "entry_price": 45000},
  "ETH": {"side": "short", "size": 10.0, "entry_price": 2800},
  "SOL": {"side": "long", "size": 100.0, "entry_price": 95}
}
```

2. Run in background:

```bash
# Check every 5 minutes (300 seconds)
nohup python position_monitor.py 300 > alerts.log &

# Or check every 1 minute for active trading
nohup python position_monitor.py 60 > alerts.log &
```

**Monitor alerts:**

```bash
# Watch alerts in real-time
tail -f alerts.log

# Check recent alerts
tail -50 alerts.log
```

**Alert Types:**

- ⚠️ **TRIM WARNING:** Long position + narrative fading rapidly
- ⚠️ **COVER WARNING:** Short position + narrative spiking rapidly
- 📉 **CAUTION:** Narrative weakening (long position)
- 📈 **CAUTION:** Narrative strengthening (short position)

---

### Before Each Trade - Pre-Trade Check (30 seconds)

**Purpose:** Validate before entry

**This prevents you from:**

- ❌ Buying calls when narrative is fading
- ❌ Shorting into a narrative spike
- ❌ Trading without momentum confirmation


**Command:**

```bash
# Check before going long
python pre_trade_check.py HYPE long

# Check before going short
python pre_trade_check.py ETH short

# Use shorter window for intraday trades
python pre_trade_check.py BTC long --window 1h
```

**Output Interpretation:**

#### ✅ APPROVED (High Confidence)

- Narrative aligns with trade direction
- Strong momentum confirmation
- High composite signal confidence
- → **Proceed with trade**

---

#### ✅ APPROVED (Moderate/Low Confidence)

- Some warnings present
- Narrative not strongly aligned
- → **Proceed with caution, smaller size**

---

#### ❌ BLOCKED

- Narrative strongly against trade direction
- Multiple errors detected
- → **DO NOT ENTER - Wait for better setup**


**Example Output:**

```text
================================================================================
PRE-TRADE CHECK: HYPE LONG
================================================================================

Verdict: ✅ APPROVED (High Confidence)
Confidence: 85%
Reason: CLEAR

Narrative State:
  Mentions: 125
  Velocity: +45 mentions
  Acceleration: +12
  Mindshare: 0.15

Composite Signal:
  Score: +0.65
  Confidence: 85%

✅ Positives:
  ✅ Narrative strengthening: +45 mentions
  ✅ Positive acceleration: +12
  ✅ Bullish composite signal: +0.65
```

---

### 5:00 PM - EOD Review (2 minutes)

**Purpose:** Learn and iterate

**Commands:**

```bash
# Option 1: Run complete EOD review (recommended)
python eod_review.py --watchlist watchlist.txt

# Option 2: Run individual steps
# Review today's alerts
tail -50 alerts.log

# Check what worked (momentum leaders)
python -c "
from delta_store import DeltaStore
store = DeltaStore()
summary = store.get_watchlist_summary(['BTC', 'ETH', 'SOL'], '24h')
for s in summary:
    print(f'{s[\"ticker\"]}: momentum {s[\"momentum_score\"]:.0f}')
"

# Generate end-of-day digest
python narrative_digest.py BTC ETH SOL --window 24h --format obsidian >> journal.md
```

**What to review:**

- Which alerts fired and why
- Which trades were blocked (saved you from losses?)
- Which setups worked (high conviction → good outcome?)
- Momentum leaders (what's working today?)

**Update positions:**

- Edit `positions.json` to reflect closed positions
- Add new positions for tomorrow's monitoring


---

## 🚀 Quick Start

### First Time Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set API key:**

```bash
export ELFA_API_KEY="your_api_key_here"
```

3. **Create positions file:**

```bash
# This will create positions.json template
python position_monitor.py 300
# Then edit positions.json with your actual positions
```

4. **Test the system:**

```bash
# Morning scan
python entry_scanner.py BTC ETH SOL

# Pre-trade check
python pre_trade_check.py BTC long

# Position monitor (test run)
python position_monitor.py 60  # Run for 1 minute to test
```

---

## 📊 Script Reference

### `entry_scanner.py`

**Purpose:** Find high-conviction entry setups

**Usage:**
```bash
python entry_scanner.py BTC ETH SOL HYPE PENGU
python entry_scanner.py --watchlist watchlist.txt
python entry_scanner.py BTC ETH --window 1h --min-conviction 0.4
```

**Output:**

- **STRONG BUY/SELL:** Conviction ≥ 60% - High-quality setup
- **BUY/SELL:** Conviction ≥ 40% - Moderate setup
- **WATCH:** Conviction ≥ 20% - Monitor for better entry
- **PASS:** Conviction < 20% - No setup

**Setups Detected:**

- **spike:** Narrative spike (continuation play)
- **momentum:** Strong velocity (momentum play)
- **anomaly:** Statistical outlier (mean reversion play)
- **smart_money:** New smart accounts (follow the flow)
- **composite_bullish/bearish:** High-confidence composite signal


---

### `pre_trade_check.py`

**Purpose:** Validate trades before entry

**Usage:**
```bash
python pre_trade_check.py TICKER long
python pre_trade_check.py TICKER short
python pre_trade_check.py BTC long --window 1h
```

**Checks:**

- Narrative velocity (strengthening/weakening?)
- Acceleration (momentum direction?)
- Composite signal (aligned with trade?)
- Anomalies (statistical outliers?)
- Signal confidence (high enough?)

**Exit Codes:**

- `0` = Approved (proceed)
- `1` = Blocked (do not enter)


---

### `position_monitor.py`

**Purpose:** Monitor open positions for narrative changes

**Usage:**
```bash
# Edit positions.json first, then:
python position_monitor.py 300  # Check every 5 minutes

# Run in background:
nohup python position_monitor.py 300 > alerts.log &
```

**Position File Format (`positions.json`):**
```json
{
  "BTC": {
    "side": "long",
    "size": 1.0,
    "entry_price": 45000
  },
  "ETH": {
    "side": "short",
    "size": 10.0,
    "entry_price": 2800
  }
}
```

**Alerts:**

- ⚠️ **TRIM WARNING:** Long + narrative fading rapidly
- ⚠️ **COVER WARNING:** Short + narrative spiking rapidly
- 📉 **CAUTION:** Narrative weakening (long position)
- 📈 **CAUTION:** Narrative strengthening (short position)


---

## 💡 Pro Tips

### 1. Morning Scan Strategy

**Look for:**

- **Overnight spikes** → Continuation plays (if momentum continues)
- **Anomalies** → Mean reversion plays (if >2.5σ)
- **Smart money activity** → Follow the flow (new accounts)

**Avoid:**

- Fading narratives (velocity negative, acceleration negative)
- Low conviction setups (<40%)
- Conflicting signals (narrative vs market)


### 2. Pre-Trade Check Best Practices

**Always check:**

- Before entering any position
- Before adding to existing position
- Before holding overnight

**Red flags:**

- Narrative fading when going long
- Narrative spiking when going short
- Low confidence composite signals (<50%)
- Multiple warnings


### 3. Position Monitoring

**Set appropriate intervals:**

- **Active trading:** 60-120 seconds
- **Swing trading:** 300 seconds (5 min)
- **Position trading:** 600 seconds (10 min)

**Respond to alerts:**

- **High severity:** Consider trimming/covering immediately
- **Medium severity:** Monitor closely, prepare exit
- **Low severity:** Note but continue monitoring


### 4. EOD Review

**Track:**

- Which alerts fired (saved you from losses?)
- Which trades were blocked (good calls?)
- Which setups worked (high conviction → good outcome?)
- Momentum leaders (what's working?)

**Iterate:**

- Adjust conviction thresholds if too many false signals
- Refine position monitoring intervals
- Update watchlist based on what's working


---

## 🔧 Troubleshooting

### "No narrative data available"

- Check API key: `echo $ELFA_API_KEY`
- Verify ticker symbol is correct
- Try different time window (4h instead of 1h)

---

### "Rate limit exceeded"

- Use caching (default behavior)
- Reduce scan frequency
- Use `--window 4h` instead of `1h` for fewer API calls

---

### Position monitor not alerting

- Check `positions.json` exists and has valid positions
- Verify positions have non-zero size
- Check `alerts.log` for errors

---

### Pre-trade check always blocking

- Check if narrative is genuinely against your trade
- Consider if you're forcing trades (wait for better setup)
- Review conviction thresholds (may be too strict)


---

## 📈 Expected Outcomes

### Good System Usage

- **Morning scan** → Find 2-3 high-conviction setups per day
- **Pre-trade check** → Block 30-50% of bad trades
- **Position monitor** → Alert 1-2 hours before major reversals
- **EOD review** → Learn patterns, improve over time

---

### Success Metrics

- **Win rate improvement:** Pre-trade check blocks bad trades
- **Loss prevention:** Position monitor alerts before major reversals
- **Setup quality:** Entry scanner finds higher conviction plays
- **Learning:** EOD review reveals patterns over time


---

## 🎓 Learning Path

### Week 1: Setup & Basics

- Set up positions.json
- Run morning scan daily
- Use pre-trade check before every trade
- Review alerts at EOD

---

### Week 2: Refinement

- Adjust conviction thresholds
- Refine position monitoring intervals
- Track which setups work best
- Build watchlist of best performers

---

### Week 3: Advanced

- Combine with other signals (price, volume, etc.)
- Backtest entry scanner setups
- Optimize position sizing based on conviction
- Build custom alert rules


---

## 📚 Related Documentation

- **Elfa API Guide:** [ELFA_API_GUIDE.md](./ELFA_API_GUIDE.md)
- **Design Principles:** [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md)
- **Roadmap:** [ROADMAP.md](./ROADMAP.md)
- **Contributing:** [CONTRIBUTING.md](./CONTRIBUTING.md)

---

*Last updated: 2024-01-XX*

