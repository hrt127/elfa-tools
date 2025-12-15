# 🎯 Elfa Tools MVP Plan

**Purpose:** Define the minimal viable product that delivers core value without losing meaning or substance.

**Status:** ⚠️ **FOR REVIEW** - Do not implement until approved.

---

## MVP Core Value Proposition

**Elfa Tools MVP enables users to:**
1. Fetch narrative data from Elfa API
2. Enrich it with temporal context (velocity, acceleration)
3. View it in a simple, explainable format
4. Understand the Decision Moment concept

**One sentence:** "Get narrative intelligence with velocity/acceleration tracking and understand why now matters."

---

## ✅ MVP Core Modules (4 files)

### 1. **elfa_client.py** ✅ KEEP
**Why:** Essential data layer. Without this, nothing works.
**Status:** Fully implemented, production-ready
**Dependencies:** `requests`

### 2. **narrative_enricher.py** ✅ KEEP
**Why:** Core value - transforms raw data into temporal insights (velocity, acceleration, churn)
**Status:** Fully implemented, production-ready
**Dependencies:** SQLite (built-in)

### 3. **narrative_radar.py** ✅ KEEP
**Why:** Primary user interface - the tool users actually run
**Status:** Fully implemented, production-ready
**Dependencies:** elfa_client, narrative_enricher

### 4. **decision_moment.py** ✅ KEEP
**Why:** Core concept - the atomic unit of value. Even if not fully used in MVP, it's the philosophical foundation
**Status:** Fully implemented
**Dependencies:** None (standalone concept)

**Total MVP Code:** 4 Python files (~1,200 lines)

---

## 🚧 Defer to v1.1 (Keep but mark as optional)

### Signal & Analysis Tools
- `signal_composer.py` - Multi-source fusion (useful but not MVP)
- `delta_store.py` - Historical analysis (nice-to-have)
- `narrative_heatmap.py` - Relationship visualization (advanced)
- `narrative_digest.py` - Multi-format outputs (advanced)

### Automation & Workflow
- `alerts_engine.py` - Rule-based alerting (useful but not MVP)
- `entry_scanner.py` - Entry opportunity detection (trading-specific)
- `pre_trade_check.py` - Trade validation (trading-specific)
- `position_monitor.py` - Position monitoring (trading-specific)
- `morning_routine.py` - Automated workflows (convenience)
- `eod_review.py` - End-of-day analysis (convenience)

### Data Clients
- `perp_client.py` - Market data (secondary data source)
- `onchain_client.py` - On-chain metrics (template, not implemented)

**Action:** Move to `optional/` directory or clearly mark in README as "v1.1 features"

---

## 📚 MVP Documentation (4 files)

### Essential (Keep)
1. **README.md** - Simplified, focused on MVP
   - What Elfa is (1 paragraph)
   - Quick start (3 commands)
   - Core modules (4 files)
   - Link to DESIGN_PRINCIPLES.md

2. **DESIGN_PRINCIPLES.md** - Core philosophy
   - What Elfa is/isn't
   - Decision Moment concept
   - 6 core principles
   - Keep substance, remove examples

3. **QUICKSTART.md** - Essential onboarding
   - Installation (2 steps)
   - First scan (1 command)
   - Understanding output (1 example)
   - Link to DESIGN_PRINCIPLES

4. **LICENSE** - Required

### Defer to v1.1 (Move to `docs/v1.1/` or archive)
- All architecture docs (ARCHITECTURE_*.md, CANONICAL_*.md, etc.)
- Trading workflow docs (TRADING_WORKFLOW.md)
- API guides (ELFA_API_GUIDE.md)
- Test plans (TEST_PLAN.md, TESTING_STATUS.md)
- Code analysis (CODE_ANALYSIS.md)
- Playful discovery (GALLERY.md, INSPIRE.md, ACHIEVEMENTS.md)
- Multiple examples (keep 1, move others)
- Roadmaps (ROADMAP.md → update to show MVP vs v1.1)
- Contributing guides (CONTRIBUTING.md → defer)
- Implementation status (IMPLEMENTATION_STATUS.md → defer)

**Total MVP Docs:** 4 files (~500 lines)

---

## 🗂️ Proposed Directory Structure

```
elfa-tools/
├── README.md                    # Simplified MVP focus
├── DESIGN_PRINCIPLES.md         # Core philosophy
├── QUICKSTART.md                # Essential onboarding
├── LICENSE                      # Required
│
├── elfa_client.py               # ✅ MVP Core
├── narrative_enricher.py        # ✅ MVP Core
├── narrative_radar.py           # ✅ MVP Core
├── decision_moment.py           # ✅ MVP Core
│
├── requirements.txt             # Minimal (requests only)
├── pyproject.toml               # Keep
│
├── optional/                    # 🚧 v1.1 Features
│   ├── signal_composer.py
│   ├── alerts_engine.py
│   ├── delta_store.py
│   ├── narrative_heatmap.py
│   ├── narrative_digest.py
│   ├── entry_scanner.py
│   ├── pre_trade_check.py
│   ├── position_monitor.py
│   ├── morning_routine.py
│   ├── eod_review.py
│   ├── perp_client.py
│   └── onchain_client.py
│
├── docs/                        # 📚 v1.1 Documentation
│   ├── v1.1/
│   │   ├── ARCHITECTURE_*.md
│   │   ├── TRADING_WORKFLOW.md
│   │   ├── ELFA_API_GUIDE.md
│   │   └── ...
│   └── examples/
│       └── BTC_DECISION_MOMENT.md  # Keep 1 example
│
└── tests/                       # Keep minimal tests
    ├── test_elfa_client.py
    └── test_narrative_enricher.py
```

---

## 📝 Simplified README.md Structure

```markdown
# Elfa Tools

**Narrative intelligence for decision-making under uncertainty.**

Elfa Tools transforms raw narrative signals into actionable insights by tracking velocity, acceleration, and account churn. It surfaces **Decision Moments**—structured explanations of why now matters.

## Quick Start

```bash
pip install -r requirements.txt
export ELFA_API_KEY="your_key"
python narrative_radar.py BTC ETH SOL --window 4h
```

## Core Modules

- **elfa_client.py** - Fetch narrative data from Elfa API
- **narrative_enricher.py** - Add temporal context (velocity, acceleration)
- **narrative_radar.py** - View enriched data in CLI or markdown
- **decision_moment.py** - Core concept: structured explanations

## Learn More

- [QUICKSTART.md](./QUICKSTART.md) - Step-by-step guide
- [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) - Core philosophy

## v1.1 Features

Advanced features available in `optional/` directory:
- Multi-source signal fusion
- Rule-based alerting
- Historical analysis
- Trading workflows

See [docs/v1.1/](./docs/v1.1/) for full documentation.
```

---

## 📦 Minimal Requirements.txt

```txt
# MVP Core Dependencies
requests>=2.31.0

# Optional (for v1.1 features)
# duckdb>=0.9.0
# matplotlib>=3.7.0
# seaborn>=0.12.0
# numpy>=1.24.0
```

---

## ✅ MVP Success Criteria

**A user can:**
1. ✅ Install in < 2 minutes
2. ✅ Run first scan in < 1 minute
3. ✅ Understand what velocity/acceleration mean
4. ✅ See Decision Moment concept explained
5. ✅ Know where to find advanced features (v1.1)

**MVP delivers:**
- Core narrative intelligence (fetch + enrich + view)
- Temporal analysis (velocity, acceleration, churn)
- Explainable outputs (source_query, audit trails)
- Decision Moment foundation

**MVP does NOT deliver:**
- Multi-source signal fusion
- Automated alerting
- Trading workflows
- Historical analysis
- Advanced visualizations

---

## 🔄 Migration Path

### Phase 1: Organize (No code changes)
1. Create `optional/` directory
2. Move non-MVP modules to `optional/`
3. Create `docs/v1.1/` directory
4. Move non-MVP docs to `docs/v1.1/`
5. Update README.md (simplified)
6. Update QUICKSTART.md (MVP focus)

### Phase 2: Simplify (Content edits)
1. Simplify README.md (remove v1.1 features)
2. Simplify QUICKSTART.md (MVP only)
3. Simplify DESIGN_PRINCIPLES.md (keep substance, remove examples)
4. Update requirements.txt (minimal)

### Phase 3: Test MVP
1. Verify MVP modules work standalone
2. Test installation from scratch
3. Verify quickstart works
4. Check all imports resolve

---

## ⚠️ What We're NOT Removing

**We keep:**
- ✅ All code (just organized differently)
- ✅ All documentation (just organized differently)
- ✅ Core concepts (Decision Moment, 6 principles)
- ✅ All functionality (just marked as v1.1)

**We simplify:**
- 📝 Documentation structure (fewer entry points)
- 📝 README focus (MVP only, link to v1.1)
- 📝 Quickstart scope (MVP only)
- 📝 Directory organization (clear separation)

---

## 🎯 MVP vs v1.1 Comparison

| Feature | MVP | v1.1 |
|---------|-----|------|
| Fetch narrative data | ✅ | ✅ |
| Velocity/acceleration | ✅ | ✅ |
| Account churn | ✅ | ✅ |
| CLI output | ✅ | ✅ |
| Decision Moment concept | ✅ | ✅ |
| Multi-source signals | ❌ | ✅ |
| Alerting | ❌ | ✅ |
| Historical analysis | ❌ | ✅ |
| Trading workflows | ❌ | ✅ |
| Advanced visualizations | ❌ | ✅ |

---

## 📊 Impact Summary

**Before MVP:**
- 21 Python files
- 30+ documentation files
- Unclear entry point
- Overwhelming for new users

**After MVP:**
- 4 core Python files (clear MVP)
- 4 essential docs (clear entry point)
- 17 optional files (organized)
- 26+ docs archived (accessible but not overwhelming)

**Result:**
- ✅ Clear MVP path
- ✅ No functionality lost
- ✅ Better organization
- ✅ Easier onboarding
- ✅ Preserved substance

---

## ⚠️ REVIEW CHECKLIST

Before implementation, confirm:

- [ ] MVP modules are correct (4 files)
- [ ] Deferred modules make sense (17 files)
- [ ] Documentation structure is acceptable
- [ ] Directory organization is clear
- [ ] Nothing essential is being removed
- [ ] Migration path is feasible
- [ ] MVP success criteria are achievable

---

**Status:** ⚠️ **AWAITING REVIEW**

Do not implement until this plan is approved and any requested changes are made.

