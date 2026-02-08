# Elfa-Tools (Layer 2)

**Narrative Tracking & Analysis.**

Python-based suite for parsing, enriching, and storing crypto narrative data.

*   **Location**: `~/dojo/projects/elfa-tools`
*   **Tech Stack**: Python 3.11+, DuckDB, SQLite.
*   **Role**: Backend processor for market intelligence.

## Quick Start
```bash
cd ~/dojo/projects/elfa-tools
source .venv/bin/activate
pip install -r requirements.txt
python elfa_client.py --help
# Review `PROJECT_CONTEXT.md` for architecture.
```

## Data
*   `narrative_history.db` (SQLite): Core events.
*   `narrative_chronicle.duckdb` (DuckDB): Analytical store.
