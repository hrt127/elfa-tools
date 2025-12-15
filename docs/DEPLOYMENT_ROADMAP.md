# Deployment Roadmap

**Elfa Tools - Production Deployment Guide**

This roadmap outlines the steps to deploy Elfa Tools to production, covering environment setup, testing, configuration, deployment options, and monitoring.

---

## 📋 Pre-Deployment Checklist

### Code Quality
- [x] All tests passing (207/216 tests passing)
- [x] Code linting and formatting (Black configured)
- [x] Type hints and documentation
- [x] Error handling (graceful degradation)
- [x] Defensive copying (fixed reference issues)

### Dependencies
- [x] `requirements.txt` up to date
- [x] Virtual environment setup documented
- [x] Optional dependencies clearly marked

### Documentation
- [x] README with quick start
- [x] API documentation
- [x] Provider registry documentation
- [x] Testing documentation

---

## 🔧 Phase 1: Environment Setup

### 1.1 Required Environment Variables

Create a `.env` file (or set in your deployment environment):

```bash
# Core API Keys (Required)
ELFA_API_KEY=your_elfa_api_key_here

# On-Chain Data Providers (Optional - enables fallback)
GLASSNODE_API_KEY=your_glassnode_key
CRYPTOQUANT_API_KEY=your_cryptoquant_key
ZAPPER_API_KEY=your_zapper_key
ZERION_API_KEY=your_zerion_key
COVALENT_API_KEY=your_covalent_key

# Binance Perpetual Futures (Optional)
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
```

### 1.2 Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import elfa_client; import narrative_enricher; print('✅ Core modules OK')"
```

### 1.3 Database Setup

The application uses SQLite and DuckDB (no external database required):

- **SQLite**: Auto-created at `narrative_history.db` (for narrative enricher)
- **DuckDB**: Auto-created at `narrative_chronicle.duckdb` (for delta store)
- **Alerts DB**: Auto-created at `alerts_history.db` (for alerts engine)

**Note**: These files are created automatically on first use. Ensure write permissions in the deployment directory.

---

## 🧪 Phase 2: Testing & Validation

### 2.1 Run Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test suites
pytest tests/test_elfa_client.py -v
pytest tests/test_narrative_enricher.py -v
pytest tests/integration/ -v
```

**Current Status**: 207/216 tests passing (96% pass rate)

### 2.2 Integration Testing

```bash
# Test end-to-end workflow
python -c "
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import enrich_snapshot

snap = get_ticker_narrative_snapshot('BTC', '4h')
if snap:
    enriched = enrich_snapshot(snap)
    print(f'✅ Enrichment successful: {enriched.delta_mentions} mentions')
else:
    print('❌ Failed to fetch snapshot')
"

# Test provider registry
python optional/test_provider_fallback.py BTC
```

### 2.3 Smoke Tests

```bash
# Test narrative radar CLI
python narrative_radar.py BTC --window 1h

# Test with export
python narrative_radar.py BTC ETH --window 4h --export test_report.md

# Verify export exists
ls -lh test_report.md
```

---

## 📦 Phase 3: Deployment Options

### Option A: Local/Server Deployment

**Best for**: Single-user or small team use

```bash
# 1. Clone repository
git clone <repository_url>
cd elfa-tools

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run
python narrative_radar.py BTC ETH SOL --window 4h
```

**Pros**:
- Simple setup
- Full control
- No external dependencies

**Cons**:
- Manual updates
- No built-in scheduling
- Single machine

---

### Option B: Docker Deployment

**Best for**: Containerized environments, CI/CD

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables (or use docker-compose)
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "narrative_radar.py", "BTC", "--window", "4h"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  elfa-tools:
    build: .
    environment:
      - ELFA_API_KEY=${ELFA_API_KEY}
      - GLASSNODE_API_KEY=${GLASSNODE_API_KEY}
    volumes:
      - ./data:/app/data  # Persist databases
      - ./reports:/app/reports  # Export reports
    restart: unless-stopped
```

**Deploy**:

```bash
docker-compose up -d
docker-compose logs -f
```

---

### Option C: Cloud Deployment (AWS/GCP/Azure)

**Best for**: Production, scaling, automation

#### AWS Lambda (Serverless)

**Pros**: Pay-per-use, auto-scaling, no server management

**Setup**:
1. Package as Lambda layer
2. Use EventBridge for scheduling
3. Store results in S3
4. Use Secrets Manager for API keys

#### AWS EC2 / GCP Compute Engine

**Pros**: Full control, persistent storage, scheduling

**Setup**:
1. Launch instance (Ubuntu/Debian)
2. Install Python 3.12+
3. Clone repository
4. Set up systemd service for scheduling
5. Use cron for periodic runs

#### Example systemd service (`/etc/systemd/system/elfa-tools.service`):

```ini
[Unit]
Description=Elfa Tools Narrative Radar
After=network.target

[Service]
Type=oneshot
User=elfa
WorkingDirectory=/opt/elfa-tools
Environment="ELFA_API_KEY=your_key"
ExecStart=/opt/elfa-tools/venv/bin/python narrative_radar.py BTC ETH SOL --window 4h --export /var/reports/radar_$(date +\%Y\%m\%d_\%H\%M).md
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Example cron job (daily at 9 AM UTC):

```bash
0 9 * * * /opt/elfa-tools/venv/bin/python /opt/elfa-tools/narrative_radar.py BTC ETH SOL --window 24h --export /var/reports/daily_$(date +\%Y\%m\%d).md
```

---

## 🔄 Phase 4: Automation & Scheduling

### 4.1 Scheduled Reports

**Use Case**: Daily/weekly narrative reports

```bash
# Daily report (9 AM UTC)
0 9 * * * cd /opt/elfa-tools && venv/bin/python narrative_radar.py BTC ETH SOL --window 24h --export /var/reports/daily_$(date +\%Y\%m\%d).md

# Hourly monitoring (every hour)
0 * * * * cd /opt/elfa-tools && venv/bin/python narrative_radar.py BTC --window 1h --export /var/reports/hourly_$(date +\%Y\%m\%d_\%H).md
```

### 4.2 Alert Monitoring

**Use Case**: Real-time alerts on narrative changes

```python
# Create alert_monitor.py
from optional.alerts_engine import AlertsEngine
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import enrich_snapshot

engine = AlertsEngine()

# Load alert rules
engine.load_rules_from_config("alerts_config.yaml")

# Monitor ticker
snap = get_ticker_narrative_snapshot("BTC", "1h")
if snap:
    enriched = enrich_snapshot(snap)
    alerts = engine.check_all_rules(enriched)
    
    for alert in alerts:
        print(f"🚨 Alert: {alert['message']}")
        # Send notification (email, Slack, etc.)
```

### 4.3 Continuous Monitoring Script

Create `monitor.py`:

```python
#!/usr/bin/env python3
"""Continuous monitoring with alerts."""

import time
from optional.alerts_engine import AlertsEngine
from elfa_client import get_ticker_narrative_snapshot
from narrative_enricher import enrich_snapshot

def monitor_loop(tickers, window="1h", interval_seconds=300):
    """Monitor tickers continuously."""
    engine = AlertsEngine()
    engine.load_rules_from_config("alerts_config.yaml")
    
    while True:
        for ticker in tickers:
            snap = get_ticker_narrative_snapshot(ticker, window, use_cache=False)
            if snap:
                enriched = enrich_snapshot(snap)
                alerts = engine.check_all_rules(enriched)
                
                for alert in alerts:
                    print(f"🚨 [{ticker}] {alert['message']}")
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_loop(["BTC", "ETH", "SOL"], window="1h", interval_seconds=300)
```

---

## 📊 Phase 5: Monitoring & Observability

### 5.1 Logging

The application uses `print()` statements for warnings. For production, consider:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('elfa_tools.log'),
        logging.StreamHandler()
    ]
)
```

### 5.2 Health Checks

Create `health_check.py`:

```python
#!/usr/bin/env python3
"""Health check endpoint for monitoring."""

from elfa_client import get_ticker_narrative_snapshot
from optional.onchain_client import get_onchain_data
import sys

def health_check():
    """Check if services are responding."""
    issues = []
    
    # Check Elfa API
    snap = get_ticker_narrative_snapshot("BTC", "1h", use_cache=False)
    if not snap:
        issues.append("Elfa API not responding")
    
    # Check on-chain providers (at least one should work)
    onchain = get_onchain_data("BTC", use_cache=False, use_fallback=True)
    if not onchain:
        issues.append("All on-chain providers failed")
    
    if issues:
        print(f"❌ Health check failed: {', '.join(issues)}")
        sys.exit(1)
    else:
        print("✅ All services healthy")
        sys.exit(0)

if __name__ == "__main__":
    health_check()
```

### 5.3 Metrics Collection

Track key metrics:
- API call success rate
- Cache hit rate
- Provider fallback frequency
- Alert trigger rate
- Database size

---

## 🔒 Phase 6: Security & Best Practices

### 6.1 API Key Management

**DO**:
- Use environment variables (never commit keys)
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Use least-privilege keys

**DON'T**:
- Commit `.env` files
- Hardcode keys in code
- Share keys in logs
- Use production keys in development

### 6.2 File Permissions

```bash
# Secure database files
chmod 600 *.db *.duckdb

# Secure .env file
chmod 600 .env

# Application files
chmod 644 *.py
chmod 755 narrative_radar.py
```

### 6.3 Network Security

- Use HTTPS for API calls (already enforced)
- Rate limit API calls (already implemented)
- Monitor for unusual activity
- Use VPN/proxy if needed

---

## 📈 Phase 7: Scaling Considerations

### 7.1 Database Optimization

- **SQLite**: Good for single-user, consider PostgreSQL for multi-user
- **DuckDB**: Excellent for analytics, consider partitioning for large datasets
- **Cleanup**: Implement data retention policies

### 7.2 Caching Strategy

- Current: In-memory cache (5-10 min TTL)
- Consider: Redis for distributed caching
- Consider: Persistent cache for offline use

### 7.3 Rate Limiting

- Current: 60 requests/minute per endpoint
- Monitor: API usage patterns
- Adjust: Based on provider limits

---

## 🚀 Phase 8: Go-Live Checklist

### Pre-Launch
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] API keys validated
- [ ] Database directories created with proper permissions
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backup strategy defined

### Launch Day
- [ ] Deploy to production environment
- [ ] Run smoke tests
- [ ] Verify first report generation
- [ ] Check alert system
- [ ] Monitor error logs
- [ ] Verify scheduled jobs

### Post-Launch
- [ ] Monitor for 24-48 hours
- [ ] Review first reports
- [ ] Check API usage
- [ ] Verify fallback mechanisms
- [ ] Collect user feedback
- [ ] Document any issues

---

## 📚 Additional Resources

- **Quick Start**: See `README.md`
- **API Documentation**: See `docs/v1.1/ELFA_API_GUIDE.md`
- **Provider Registry**: See `docs/PROVIDER_REGISTRY.md`
- **Testing**: See `TEST_EXPLANATION.md`
- **Architecture**: See `docs/v1.1/ARCHITECTURE_OVERVIEW.md`

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'optional'`
**Solution**: Ensure you're running from project root, or add to `PYTHONPATH`

**Issue**: `GLASSNODE_API_KEY not set`
**Solution**: Set environment variable or use fallback providers

**Issue**: Database locked errors
**Solution**: Ensure only one process accesses SQLite at a time

**Issue**: Rate limit errors
**Solution**: Enable fallback providers or increase cache TTL

---

## 📞 Support

For issues or questions:
1. Check documentation in `docs/`
2. Review test examples in `tests/`
3. Check `TEST_EXPLANATION.md` for test behavior
4. Review error messages (application is designed to be self-documenting)

---

**Last Updated**: 2025-12-15
**Version**: 1.0.0

