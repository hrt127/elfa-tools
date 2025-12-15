# Quick Deployment Guide

**TL;DR - Get Elfa Tools running in 5 minutes**

## 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Set API Key

```bash
export ELFA_API_KEY="your_key_here"
```

## 3. Run

```bash
python narrative_radar.py BTC --window 4h
```

**That's it!** 🎉

---

## Optional: Enable On-Chain Data

```bash
export GLASSNODE_API_KEY="your_glassnode_key"
export CRYPTOQUANT_API_KEY="your_cryptoquant_key"
```

The system will automatically use fallback providers if one fails.

---

## Production Deployment

See `docs/DEPLOYMENT_ROADMAP.md` for:
- Docker deployment
- Cloud deployment (AWS/GCP/Azure)
- Scheduling & automation
- Monitoring & observability
- Security best practices

---

## Troubleshooting

**No data returned?**
- Check API key: `echo $ELFA_API_KEY`
- Test API: `python -c "from elfa_client import get_ticker_narrative_snapshot; print(get_ticker_narrative_snapshot('BTC', '1h'))"`

**Module not found?**
- Ensure virtual environment is activated
- Run from project root directory

**Rate limited?**
- Enable fallback providers
- Increase cache TTL (edit `elfa_client.py`)

---

**For full deployment guide**: See `docs/DEPLOYMENT_ROADMAP.md`

