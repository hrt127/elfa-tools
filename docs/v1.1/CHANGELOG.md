# Changelog

All notable changes to Elfa Tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Composite signal generator (narrative + funding + price)
- Alerts engine with configurable rules
- Delta store for historical data
- Bot adapter for Telegram/Discord
- Dashboard adapter for data visualization

---

## [1.0.0] - 2024-01-XX

### Added


- **elfa_client.py** - Authenticated REST API client
  - Environment variable authentication via `ELFA_API_KEY`
  - Graceful error handling (never crashes)
  - Built-in caching with configurable TTL
  - Rate limit tracking and awareness
  - Audit trails with `source_query` field
  - Support for ticker narrative snapshots

- **narrative_enricher.py** - History tracking and enrichment
  - SQLite backend for persistent storage
  - Velocity computation (change in mentions)
  - Acceleration computation (change in velocity)
  - Account churn tracking (new/lost accounts)
  - Temporal analysis capabilities

- **narrative_radar.py** - CLI radar scanner
  - Multi-ticker support
  - Velocity and acceleration indicators
  - Account churn visualization
  - Markdown export functionality
  - Visual indicators (🚀📈↗️➡️↘️📉💥)
  - Caching options

- **narrative_heatmap.py** - Co-heatmap generator
  - Account overlap matrix (Jaccard similarity)
  - Velocity correlation matrices
  - Mindshare similarity analysis
  - Account-ticker mention patterns
  - PNG image export (requires matplotlib/seaborn)
  - Markdown table export

- **narrative_digest.py** - Daily digest writer
  - Multi-format output support:
    - Obsidian (wiki-style markdown)
    - Telegram (plain text with emojis)
    - Discord (markdown formatted)
    - Email (HTML + plain text)
    - Blog (publishing-ready markdown)
    - JSON (structured data)
  - Insights extraction:
    - Top movers (highest velocity)
    - Fastest accelerating
    - Highest mindshare scores
    - Most mentioned tickers
    - Account churn leaders
    - Trending accounts
  - Aggregated metrics
  - Detailed per-ticker breakdowns

- **Documentation**
  - README.md with comprehensive usage guide
  - ROADMAP.md with development planning
  - CONTRIBUTING.md with contribution guidelines
  - CHANGELOG.md for version tracking
  - LICENSE file (MIT)
  - .env.example for configuration

### Design Principles

All tools adhere to six core principles:

1. Narrow: Each tool does one job well
2. Explainable: Source data, contributing factors, and audit trails included
3. Robust: Graceful error handling, never crashes, handles partial data
4. Composable: Tools work standalone and snap together naturally
5. Signal Layer, Not Oracle: Provides signals and context, not answers
6. Transparent Constraints: Rate limits, caching, and provenance are visible

All tools converge on the Decision Moment: a structured explanation of why now matters.

---

## Version History


- **1.0.0** - Initial release with core functionality
  - API client with authentication and caching
  - Narrative enrichment with history tracking
  - Radar scanner for multi-ticker analysis
  - Co-heatmap generator for relationship visualization
  - Multi-format daily digest generator

---

[Unreleased]: https://github.com/your-repo/elfa-tools/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-repo/elfa-tools/releases/tag/v1.0.0

